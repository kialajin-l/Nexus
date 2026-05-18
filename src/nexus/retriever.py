from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from nexus.embedder import Embedder
from nexus.models import MemoryRecord, MemoryType, RetrievalFilters, ScoredMemory
from nexus.store import MemoryStore


@dataclass
class RetrieverConfig:
    keyword_weight: float = 0.3
    vector_weight: float = 0.4
    importance_weight: float = 0.2
    recency_weight: float = 0.1
    recency_decay_lambda: float = 0.05
    default_top_k: int = 5
    max_top_k: int = 20


class Retriever:
    def __init__(
        self,
        store: MemoryStore,
        embedder: Embedder,
        config: RetrieverConfig | None = None,
    ) -> None:
        self._store = store
        self._embedder = embedder
        self._config = config or RetrieverConfig()

    def retrieve(
        self,
        query: str,
        project: str,
        top_k: int = 5,
        filters: RetrievalFilters | None = None,
    ) -> list[ScoredMemory]:
        top_k = min(top_k, self._config.max_top_k)
        keyword_results = self._keyword_search(query, project)
        vector_results = self._vector_search(query, project)

        merged = self._merge_results(keyword_results, vector_results)
        scored = self._apply_scoring(merged, keyword_results, vector_results)
        scored = self._apply_filters(scored, filters)
        scored.sort(key=lambda x: x.score, reverse=True)

        for sm in scored[:top_k]:
            sm.record.touch()
            self._store.update(sm.record.id, {
                "access_count": sm.record.access_count,
                "last_accessed_at": sm.record.last_accessed_at,
            })

        return scored[:top_k]

    def _keyword_search(self, query: str, project: str) -> dict[str, tuple[MemoryRecord, float]]:
        keywords = query.split()
        if not keywords:
            return {}
        results = {}
        raw = self._store.search_by_keywords(keywords, project, top_k=20)
        if raw:
            max_score = max(abs(s) for _, s in raw) or 1.0
            for rec, score in raw:
                normalized = min(score / max_score, 1.0) if max_score > 0 else 0.0
                results[rec.id] = (rec, normalized)
        return results

    def _vector_search(self, query: str, project: str) -> dict[str, tuple[MemoryRecord, float]]:
        try:
            query_vec = self._embedder.embed(query)
        except Exception:
            return {}
        raw = self._store.search_by_vector(query_vec, project, top_k=20)
        results = {}
        for rec, similarity in raw:
            results[rec.id] = (rec, similarity)
        return results

    def _merge_results(
        self,
        keyword: dict[str, tuple[MemoryRecord, float]],
        vector: dict[str, tuple[MemoryRecord, float]],
    ) -> dict[str, MemoryRecord]:
        all_ids = set(keyword.keys()) | set(vector.keys())
        merged = {}
        for mid in all_ids:
            if mid in keyword:
                merged[mid] = keyword[mid][0]
            else:
                merged[mid] = vector[mid][0]
        return merged

    def _apply_scoring(
        self,
        records: dict[str, MemoryRecord],
        keyword_results: dict[str, tuple[MemoryRecord, float]],
        vector_results: dict[str, tuple[MemoryRecord, float]],
    ) -> list[ScoredMemory]:
        cfg = self._config
        scored = []
        for mid, rec in records.items():
            kw_score = keyword_results[mid][1] if mid in keyword_results else 0.0
            vec_score = vector_results[mid][1] if mid in vector_results else 0.0
            recency = self._recency_score(rec)

            final = (
                cfg.keyword_weight * kw_score
                + cfg.vector_weight * vec_score
                + cfg.importance_weight * rec.importance
                + cfg.recency_weight * recency
            )
            scored.append(ScoredMemory(record=rec, score=final))
        return scored

    def _recency_score(self, rec: MemoryRecord) -> float:
        if not rec.last_accessed_at and not rec.created_at:
            return 0.0
        time_str = rec.last_accessed_at or rec.created_at
        try:
            dt = datetime.fromisoformat(time_str)
            now = datetime.now(timezone.utc)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            days = (now - dt).total_seconds() / 86400
            return math.exp(-self._config.recency_decay_lambda * max(days, 0))
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def _apply_filters(scored: list[ScoredMemory], filters: RetrievalFilters | None) -> list[ScoredMemory]:
        if not filters:
            return scored
        result = scored
        if filters.types:
            type_set = set(filters.types)
            result = [s for s in result if s.record.type in type_set]
        if filters.min_importance > 0:
            result = [s for s in result if s.record.importance >= filters.min_importance]
        return result

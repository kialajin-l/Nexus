from __future__ import annotations

import re
from datetime import datetime, timezone

from nexus.models import MemoryRecord, MemoryStatus, MemoryType, QueryFilter
from nexus.store import MemoryStore


class MemoryFilter:
    OUTDATED_DAYS = 30
    DELETE_OUTDATED_DAYS = 90
    IGNORED_THRESHOLD = 2
    DECAY_AMOUNT = 0.2
    MIN_IMPORTANCE = 0.1

    INJECT_IMPORTANCE_THRESHOLD = 0.4
    FACT_IMPORTANCE_THRESHOLD = 0.5
    DECISION_IMPORTANCE_THRESHOLD = 0.6
    DECISION_MIN_RETRIEVAL_SCORE = 0.15
    DECISION_ACCEPTED_SCORE_BOOST = 0.05
    DECISION_IGNORED_PENALTY = 0.05
    INJECT_EXCLUDE_TYPES: list[MemoryType] = [MemoryType.TODO]
    MIN_CONTENT_LENGTH = 10
    FACT_MIN_CONTENT_LENGTH = 20
    FACT_MIN_SPECIFICITY_SCORE = 1

    _SPECIFICITY_PATTERNS = [
        re.compile(r"\d+\.?\d*"),
        re.compile(r"[A-Z][a-zA-Z]+(?:\.js|\.py|\.ts|\.go|\.rs|\.md|\.sql|\.json|\.yaml|\.toml)"),
        re.compile(r"(?:SQLite|PostgreSQL|MySQL|Redis|MongoDB|FAISS|ChromaDB|numpy|pandas|pytest|Ollama|OpenAI|FTS5|REST|HTTP|API|SDK|CLI|CRUD|JSON|YAML|SQL|NoSQL|RAG|LLM|NLP|BERT|GPT)"),
        re.compile(r"[\u4e00-\u9fff]{2,}(?:架构|策略|方案|模块|接口|协议|格式|引擎|索引|分词|嵌入|向量|检索提取|注入|降权|过期|隔离|迁移)"),
    ]

    def __init__(self, store: MemoryStore | None = None) -> None:
        self._store = store

    def should_inject(
        self,
        record: MemoryRecord,
        task_context: str = "",
        mode: str = "task",
        retrieval_score: float = 0.0,
    ) -> bool:
        if record.status == MemoryStatus.DEPRECATED:
            return False
        if record.status == MemoryStatus.CANDIDATE and mode != "explore":
            return False
        if record.source_level == "L3" and mode != "explore":
            return False
        if mode == "brief" and (record.status != MemoryStatus.STABLE or record.source_level != "L1"):
            return False
        if mode == "task" and (record.status != MemoryStatus.STABLE or record.source_level not in {"L1", "L2"}):
            return False
        if record.type in self.INJECT_EXCLUDE_TYPES:
            return False
        if len(record.content) < self.MIN_CONTENT_LENGTH:
            return False

        if record.type == MemoryType.FACT:
            return self._should_inject_fact(record, task_context)

        if record.type == MemoryType.RULE:
            return self._should_inject_rule(record, task_context)

        if record.type == MemoryType.DECISION:
            return self._should_inject_decision(record, task_context, retrieval_score)

        if record.importance < self.INJECT_IMPORTANCE_THRESHOLD:
            return False
        return True

    def _should_inject_fact(self, record: MemoryRecord, task_context: str = "") -> bool:
        if record.importance < self.FACT_IMPORTANCE_THRESHOLD:
            return False
        if len(record.content) < self.FACT_MIN_CONTENT_LENGTH:
            return False

        specificity = self._compute_specificity(record.content)
        if specificity < self.FACT_MIN_SPECIFICITY_SCORE:
            return False

        if task_context:
            overlap = self._compute_task_overlap(record, task_context)
            if overlap == 0:
                return False

        return True

    def _should_inject_rule(self, record: MemoryRecord, task_context: str = "") -> bool:
        if record.importance < self.INJECT_IMPORTANCE_THRESHOLD:
            return False

        if task_context:
            overlap = self._compute_task_overlap(record, task_context)
            if overlap == 0:
                return False

        return True

    def _should_inject_decision(self, record: MemoryRecord, task_context: str = "", retrieval_score: float = 0.0) -> bool:
        if record.importance < self.DECISION_IMPORTANCE_THRESHOLD:
            return False

        min_score = self.DECISION_MIN_RETRIEVAL_SCORE

        accepted_count = self._get_accepted_count(record.id)
        ignored_count = self._get_ignored_count_from_record(record)

        min_score -= accepted_count * self.DECISION_ACCEPTED_SCORE_BOOST
        min_score += ignored_count * self.DECISION_IGNORED_PENALTY
        min_score = max(min_score, 0.0)

        if retrieval_score > 0 and retrieval_score < min_score:
            return False

        return True

    def _get_accepted_count(self, memory_id: str) -> int:
        if self._store is None:
            return 0
        try:
            row = self._store._conn.execute(
                "SELECT COUNT(*) as cnt FROM feedback_log WHERE memory_id = ? AND action = 'accepted'",
                (memory_id,),
            ).fetchone()
            return int(row["cnt"]) if row else 0
        except Exception:
            return 0

    def _get_ignored_count_from_record(self, record: MemoryRecord) -> int:
        if self._store is None:
            return 0
        return self._get_ignored_count(self._store, record.id)

    def _compute_specificity(self, content: str) -> int:
        score = 0
        for pat in self._SPECIFICITY_PATTERNS:
            if pat.search(content):
                score += 1
        return score

    @staticmethod
    def _compute_task_overlap(record: MemoryRecord, task_context: str) -> int:
        content_words = set(re.findall(r"[\u4e00-\u9fff]+|[a-zA-Z]+", record.content.lower()))
        summary_words = set(
            re.findall(r"[\u4e00-\u9fff]+|[a-zA-Z]+", (record.summary or record.content).lower())
        )
        memory_words = content_words | summary_words
        task_words = set(re.findall(r"[\u4e00-\u9fff]+|[a-zA-Z]+", task_context.lower()))
        return len(memory_words & task_words)

    def should_decay(self, record: MemoryRecord, ignored_count: int = 0) -> bool:
        if record.importance <= self.MIN_IMPORTANCE:
            return False
        if ignored_count >= self.IGNORED_THRESHOLD:
            return True
        if record.access_count == 0 and self._days_since(record.created_at) > self.OUTDATED_DAYS:
            return True
        return False

    def should_outdate(self, record: MemoryRecord) -> bool:
        if record.status != MemoryStatus.STABLE:
            return False
        if record.access_count == 0 and self._days_since(record.created_at) > self.OUTDATED_DAYS:
            return True
        if record.importance < 0.2:
            return True
        return False

    def should_delete(self, record: MemoryRecord) -> bool:
        if record.status == MemoryStatus.DEPRECATED and record.importance < self.MIN_IMPORTANCE:
            return True
        if record.importance < self.MIN_IMPORTANCE:
            return True
        if record.status == MemoryStatus.DEPRECATED and self._days_since(record.updated_at) > self.DELETE_OUTDATED_DAYS:
            return True
        return False

    def maintain(self, store: MemoryStore, project: str) -> dict[str, int]:
        stats = {"decayed": 0, "outdated": 0, "deleted": 0}

        stable_records = store.query(QueryFilter(
            project=project,
            statuses=[MemoryStatus.STABLE],
            limit=10000,
        ))

        for rec in stable_records:
            ignored_count = self._get_ignored_count(store, rec.id)
            if self.should_decay(rec, ignored_count):
                new_imp = max(rec.importance - self.DECAY_AMOUNT, 0.0)
                store.update(rec.id, {"importance": new_imp})
                stats["decayed"] += 1

        stable_records = store.query(QueryFilter(
            project=project,
            statuses=[MemoryStatus.STABLE],
            limit=10000,
        ))

        for rec in stable_records:
            if self.should_outdate(rec):
                store.update(rec.id, {"status": MemoryStatus.DEPRECATED.value})
                stats["outdated"] += 1

        deprecated_records = store.query(QueryFilter(
            project=project,
            statuses=[MemoryStatus.DEPRECATED],
            limit=10000,
        ))

        for rec in deprecated_records:
            if self.should_delete(rec):
                store.delete(rec.id)
                stats["deleted"] += 1

        return stats

    @staticmethod
    def _get_ignored_count(store: MemoryStore, memory_id: str) -> int:
        try:
            row = store._conn.execute(
                "SELECT COUNT(*) as cnt FROM feedback_log WHERE memory_id = ? AND action = 'ignored'",
                (memory_id,),
            ).fetchone()
            return int(row["cnt"]) if row else 0
        except Exception:
            return 0

    @staticmethod
    def _days_since(iso_str: str) -> float:
        if not iso_str:
            return 999.0
        try:
            dt = datetime.fromisoformat(iso_str)
            now = datetime.now(timezone.utc)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return (now - dt).total_seconds() / 86400
        except (ValueError, TypeError):
            return 999.0

from __future__ import annotations

import logging
from typing import Any

from nexus.config import Config
from nexus.embedder import Embedder, MockEmbedder, OllamaEmbedder, OpenAIEmbedder
from nexus.exceptions import ConfigurationError, ExtractionError, InjectionError, RetrievalError, StorageError
from nexus.extractor import Extractor
from nexus.feedback import FeedbackLogger
from nexus.injector import Injector
from nexus.llm_client import LLMClient, MockLLMClient, OllamaClient, OpenAIClient
from nexus.memory_filter import MemoryFilter
from nexus.models import ExtractMetadata, MemoryRecord, MemoryStatus, MemoryType, RetrievalFilters, ScoredMemory
from nexus.retriever import Retriever
from nexus.store import MemoryStore

logger = logging.getLogger(__name__)


def _create_llm_client(config: Config) -> LLMClient:
    if config.llm_provider == "ollama":
        return OllamaClient(base_url=config.llm_base_url, default_model=config.llm_model)
    if config.llm_provider == "openai":
        return OpenAIClient(
            base_url=config.llm_base_url,
            api_key=config.llm_api_key,
            default_model=config.llm_model,
        )
    raise ConfigurationError(
        f"Unknown LLM provider: {config.llm_provider}",
        code="INVALID_PROVIDER",
        details={"provider": config.llm_provider},
    )


def _create_embedder(config: Config) -> Embedder:
    if config.llm_provider == "ollama":
        return OllamaEmbedder(base_url=config.llm_base_url, model=config.embedding_model)
    if config.llm_provider == "openai":
        return OpenAIEmbedder(
            base_url=config.llm_base_url,
            api_key=config.llm_api_key,
            model=config.embedding_model,
        )
    raise ConfigurationError(
        f"Unknown LLM provider for embedding: {config.llm_provider}",
        code="INVALID_PROVIDER",
        details={"provider": config.llm_provider},
    )


class MemoryCoprocessor:
    def __init__(
        self,
        project: str,
        db_path: str = "data/nexus.db",
        config: Config | None = None,
        llm_client: LLMClient | None = None,
        embedder: Embedder | None = None,
        prompt: str = "",
    ) -> None:
        self._project = project
        self._config = config or Config.from_env()
        self._config.db_path = db_path or self._config.db_path

        self._llm = llm_client or _create_llm_client(self._config)
        self._embedder = embedder or _create_embedder(self._config)
        self._store = MemoryStore(self._config.db_path)

        self._extractor = Extractor(llm_client=self._llm, store=self._store, prompt=prompt)
        self._retriever = Retriever(store=self._store, embedder=self._embedder)
        self._injector = Injector()
        self._feedback = FeedbackLogger(store=self._store)
        self._filter = MemoryFilter(store=self._store)

    @property
    def project(self) -> str:
        return self._project

    def extract(self, text: str, session_id: str = "") -> list[MemoryRecord]:
        if not text or not text.strip():
            raise ExtractionError(
                "Cannot extract from empty text",
                code="EMPTY_CONTENT",
            )
        metadata = ExtractMetadata(
            project=self._project,
            session_id=session_id,
            topic=self._project,
        )
        try:
            records = self._extractor.extract(text, metadata)
        except Exception as e:
            if isinstance(e, ExtractionError):
                raise
            raise ExtractionError(
                f"Extraction failed: {e}",
                code="EXTRACT_FAILED",
                details={"text_length": len(text)},
            ) from e
        for rec in records:
            try:
                self._store.save(rec)
            except Exception as e:
                raise StorageError(
                    f"Failed to save extracted memory: {e}",
                    code="SAVE_FAILED",
                    details={"memory_id": rec.id},
                ) from e
            try:
                embedding = self._embedder.embed(rec.content)
                self._store.save_embedding(rec.id, embedding)
            except Exception as e:
                logger.warning("Failed to compute embedding for %s: %s", rec.id, e)
        return records

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filters: RetrievalFilters | None = None,
    ) -> list[ScoredMemory]:
        if not query or not query.strip():
            raise RetrievalError(
                "Cannot retrieve with empty query",
                code="EMPTY_QUERY",
            )
        try:
            return self._retriever.retrieve(
                query=query,
                project=self._project,
                top_k=top_k,
                filters=filters,
            )
        except Exception as e:
            if isinstance(e, RetrievalError):
                raise
            raise RetrievalError(
                f"Retrieval failed: {e}",
                code="RETRIEVE_FAILED",
                details={"query": query[:100], "top_k": top_k},
            ) from e

    def inject(
        self,
        query: str,
        max_tokens: int = 500,
        top_k: int = 5,
        filters: RetrievalFilters | None = None,
        mode: str = "task",
    ) -> str:
        if not query or not query.strip():
            raise InjectionError(
                "Cannot inject with empty query",
                code="EMPTY_QUERY",
            )
        try:
            memories = self.retrieve(query, top_k=top_k, filters=filters)
            filtered = [
                sm
                for sm in memories
                if self._filter.should_inject(sm.record, task_context=query, mode=mode, retrieval_score=sm.score)
            ]
            self._feedback.log_injection(
                [sm.record.id for sm in filtered], task_context=query
            )
            return self._injector.inject(filtered, context=query, max_tokens=max_tokens, mode=mode)
        except (RetrievalError, InjectionError):
            raise
        except Exception as e:
            raise InjectionError(
                f"Injection failed: {e}",
                code="INJECT_FAILED",
                details={"query": query[:100], "max_tokens": max_tokens},
            ) from e

    def feedback(self, memory_id: str, action: str, context: str = "") -> None:
        self._feedback.log_feedback(memory_id, action, context)

    def search(self, query: str, top_k: int = 10) -> list[MemoryRecord]:
        results = self._retriever.retrieve(
            query=query,
            project=self._project,
            top_k=top_k,
        )
        return [sm.record for sm in results]

    def list_memories(
        self,
        types: list[MemoryType] | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[MemoryRecord]:
        from nexus.models import QueryFilter

        qf = QueryFilter(
            project=self._project,
            types=types or [],
            statuses=[MemoryStatus.STABLE],
            limit=limit,
            offset=offset,
        )
        return self._store.query(qf)

    def stats(self) -> dict[str, Any]:
        total = self._store.count(project=self._project)
        stable = self._store.count(project=self._project, status=MemoryStatus.STABLE.value)
        candidate = self._store.count(project=self._project, status=MemoryStatus.CANDIDATE.value)
        deprecated = self._store.count(project=self._project, status=MemoryStatus.DEPRECATED.value)
        return {
            "project": self._project,
            "total": total,
            "active": stable,
            "deleted": deprecated,
            "outdated": deprecated,
            "stable": stable,
            "candidate": candidate,
            "deprecated": deprecated,
        }

    def maintain(self) -> dict[str, int]:
        return self._filter.maintain(self._store, self._project)

    def close(self) -> None:
        self._store.close()

    def __enter__(self) -> MemoryCoprocessor:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

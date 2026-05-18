from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class Config:
    db_path: str = "data/nexus.db"
    llm_provider: str = "ollama"
    llm_model: str = "qwen3:4b"
    llm_base_url: str = "http://localhost:11434"
    llm_api_key: str = ""
    embedding_model: str = "nomic-embed-text"
    embedding_dimension: int = 768
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> Config:
        return cls(
            db_path=os.environ.get("NEXUS_DB_PATH", "data/nexus.db"),
            llm_provider=os.environ.get("NEXUS_LLM_PROVIDER", "ollama"),
            llm_model=os.environ.get("NEXUS_LLM_MODEL", "qwen3:4b"),
            llm_base_url=os.environ.get("NEXUS_LLM_BASE_URL", "http://localhost:11434"),
            llm_api_key=os.environ.get("NEXUS_LLM_API_KEY", ""),
            embedding_model=os.environ.get("NEXUS_EMBEDDING_MODEL", "nomic-embed-text"),
            embedding_dimension=int(os.environ.get("NEXUS_EMBEDDING_DIMENSION", "768")),
            log_level=os.environ.get("NEXUS_LOG_LEVEL", "INFO"),
        )

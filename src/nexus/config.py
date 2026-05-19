from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _default_db_path() -> str:
    nexus_home = os.environ.get("NEXUS_HOME", "")
    root = Path(nexus_home) if nexus_home else Path.home() / ".nexus"
    return str((root / "nexus.db").resolve())


@dataclass
class Config:
    db_path: str = field(default_factory=_default_db_path)
    obsidian_root_path: str = ""
    llm_provider: str = ""
    llm_model: str = ""
    llm_base_url: str = ""
    llm_api_key: str = ""
    embedding_model: str = ""
    embedding_dimension: int = 768
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> Config:
        return cls(
            db_path=os.environ.get("NEXUS_DB_PATH", _default_db_path()),
            obsidian_root_path=os.environ.get("NEXUS_OBSIDIAN_ROOT_PATH", ""),
            llm_provider=os.environ.get("NEXUS_LLM_PROVIDER", ""),
            llm_model=os.environ.get("NEXUS_LLM_MODEL", ""),
            llm_base_url=os.environ.get("NEXUS_LLM_BASE_URL", ""),
            llm_api_key=os.environ.get("NEXUS_LLM_API_KEY", ""),
            embedding_model=os.environ.get("NEXUS_EMBEDDING_MODEL", ""),
            embedding_dimension=int(os.environ.get("NEXUS_EMBEDDING_DIMENSION", "768")),
            log_level=os.environ.get("NEXUS_LOG_LEVEL", "INFO"),
        )

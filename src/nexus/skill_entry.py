from __future__ import annotations

import json
import os
from pathlib import Path

from nexus.config import Config
from nexus.coprocessor import MemoryCoprocessor
from nexus.embedder import MockEmbedder
from nexus.llm_client import MockLLMClient


def _default_config_candidates() -> list[Path]:
    candidates: list[Path] = []
    env_path = os.environ.get("NEXUS_CONFIG", "").strip()
    if env_path:
        candidates.append(Path(env_path).expanduser())

    cwd_config = Path.cwd() / "config" / "nexus.json"
    repo_config = Path(__file__).resolve().parents[2] / "config" / "nexus.json"

    for candidate in (cwd_config, repo_config):
        if candidate not in candidates:
            candidates.append(candidate)
    return candidates


def _resolve_default_config_path() -> Path:
    candidates = _default_config_candidates()
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return candidates[0].resolve()


def _config_base_dir(config_path: Path) -> Path:
    if config_path.parent.name == "config":
        return config_path.parent.parent
    return config_path.parent


def _resolve_path_from_config(value: str, config_path: Path) -> str:
    if not value:
        return value
    path = Path(value).expanduser()
    if path.is_absolute():
        return str(path)
    return str((_config_base_dir(config_path) / path).resolve())


DEFAULT_CONFIG_PATH = _resolve_default_config_path()


def load_config(path: str | Path = DEFAULT_CONFIG_PATH) -> Config:
    config_path = Path(path).expanduser()
    config = Config.from_env()
    if not config_path.exists():
        return config

    config_path = config_path.resolve()
    data = json.loads(config_path.read_text(encoding="utf-8"))
    for field_name in config.__dataclass_fields__:
        if field_name in data:
            value = data[field_name]
            if field_name == "db_path" and isinstance(value, str):
                value = _resolve_path_from_config(value, config_path)
            setattr(config, field_name, value)
    return config


def open_coprocessor(
    *,
    project: str,
    config_path: str | Path = DEFAULT_CONFIG_PATH,
    db_path: str | Path | None = None,
    mock: bool = False,
    prompt: str = "",
) -> MemoryCoprocessor:
    config = load_config(config_path)
    resolved_db_path = str(db_path) if db_path else config.db_path

    if mock:
        mock_response = json.dumps(
            {
                "memories": [
                    {
                        "type": "fact",
                        "content": "Extracted from provided text (mock mode)",
                        "summary": "Mock extraction",
                        "tags": ["mock"],
                        "importance": 0.5,
                    }
                ]
            }
        )
        return MemoryCoprocessor(
            project=project,
            db_path=resolved_db_path,
            config=config,
            llm_client=MockLLMClient(responses=[mock_response]),
            embedder=MockEmbedder(),
            prompt=prompt,
        )

    return MemoryCoprocessor(
        project=project,
        db_path=resolved_db_path,
        config=config,
        prompt=prompt,
    )

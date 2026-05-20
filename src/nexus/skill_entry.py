from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

from nexus.config import Config
from nexus.coprocessor import MemoryCoprocessor
from nexus.embedder import MockEmbedder
from nexus.llm_client import MockLLMClient
from nexus.store import MemoryStore


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
    data = json.loads(config_path.read_text(encoding="utf-8-sig"))
    for field_name in config.__dataclass_fields__:
        if field_name in data:
            value = data[field_name]
            if field_name in {"db_path", "obsidian_root_path"} and isinstance(value, str):
                value = _resolve_path_from_config(value, config_path)
            setattr(config, field_name, value)
    return config


def save_config(
    *,
    path: str | Path = DEFAULT_CONFIG_PATH,
    db_path: str | Path | None = None,
    obsidian_root_path: str | Path | None = None,
) -> dict[str, object]:
    config_path = Path(path).expanduser()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    existing: dict[str, object] = {}
    if config_path.exists():
        existing = json.loads(config_path.read_text(encoding="utf-8-sig"))

    config = load_config(config_path) if config_path.exists() else Config.from_env()
    if db_path is not None:
        config.db_path = str(Path(db_path).expanduser().resolve())
    if obsidian_root_path is not None and str(obsidian_root_path).strip():
        config.obsidian_root_path = str(Path(obsidian_root_path).expanduser().resolve())

    updated = dict(existing)
    updated["db_path"] = config.db_path
    updated["obsidian_root_path"] = config.obsidian_root_path
    if "log_level" not in updated:
        updated["log_level"] = config.log_level

    config_path.write_text(
        json.dumps(updated, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    return {
        "config_path": str(config_path.resolve()),
        "db_path": config.db_path,
        "obsidian_root_path": config.obsidian_root_path,
    }


def inspect_storage_targets(
    *,
    db_path: str | Path,
    obsidian_root_path: str | Path = "",
) -> dict[str, object]:
    db = Path(db_path).expanduser().resolve()
    vault = Path(obsidian_root_path).expanduser().resolve() if obsidian_root_path else None

    result: dict[str, object] = {
        "db_path": str(db),
        "db_exists": db.exists(),
        "db_has_content": _db_has_memory_content(db),
        "obsidian_root_path": str(vault) if vault else "",
        "obsidian_exists": bool(vault and vault.exists()),
        "obsidian_has_content": False,
    }

    if vault and vault.exists():
        result["obsidian_has_content"] = any(vault.iterdir())

    return result


def ensure_database_ready(db_path: str | Path) -> dict[str, object]:
    db = Path(db_path).expanduser().resolve()
    db.parent.mkdir(parents=True, exist_ok=True)

    existed_before = db.exists()
    with MemoryStore(str(db)):
        pass

    return {
        "db_path": str(db),
        "db_exists": db.exists(),
        "db_created": not existed_before and db.exists(),
    }


def _db_has_memory_content(db_path: Path) -> bool:
    if not db_path.exists() or db_path.stat().st_size == 0:
        return False

    try:
        with sqlite3.connect(db_path) as conn:
            row = conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'memories'"
            ).fetchone()
            if row is None:
                return False

            count_row = conn.execute("SELECT COUNT(*) FROM memories").fetchone()
            return bool(count_row and int(count_row[0]) > 0)
    except sqlite3.Error:
        return False


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

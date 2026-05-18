from __future__ import annotations

import json
from pathlib import Path

from nexus.config import Config
from nexus.coprocessor import MemoryCoprocessor
from nexus.embedder import MockEmbedder
from nexus.llm_client import MockLLMClient


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "nexus.json"


def load_config(path: str | Path = DEFAULT_CONFIG_PATH) -> Config:
    config_path = Path(path)
    config = Config.from_env()
    if not config_path.exists():
        return config

    data = json.loads(config_path.read_text(encoding="utf-8"))
    for field_name in config.__dataclass_fields__:
        if field_name in data:
            setattr(config, field_name, data[field_name])
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

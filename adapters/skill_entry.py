from __future__ import annotations

import sys
from pathlib import Path


def _ensure_src_on_sys_path() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    src_dir = repo_root / "src"
    src_dir_str = str(src_dir)
    if src_dir.is_dir() and src_dir_str not in sys.path:
        sys.path.insert(0, src_dir_str)


_ensure_src_on_sys_path()

from nexus.skill_entry import DEFAULT_CONFIG_PATH, ensure_database_ready, inspect_storage_targets, load_config, open_coprocessor, save_config

__all__ = ["DEFAULT_CONFIG_PATH", "load_config", "open_coprocessor", "inspect_storage_targets", "save_config", "ensure_database_ready"]

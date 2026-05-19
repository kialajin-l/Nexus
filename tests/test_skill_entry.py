import tempfile
from pathlib import Path

from adapters.skill_entry import inspect_storage_targets, load_config, open_coprocessor, save_config
from nexus import Config


def test_load_config_reads_public_skill_config_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "nexus.json"
        path.write_text(
            """
{
  "db_path": "data/custom.db",
  "llm_provider": "openai",
  "llm_model": "gpt-4.1-mini",
  "llm_base_url": "https://api.openai.com/v1",
  "embedding_model": "text-embedding-3-small",
  "embedding_dimension": 1536
}
""".strip(),
            encoding="utf-8",
        )

        config = load_config(path)

    assert isinstance(config, Config)
    assert config.db_path == str((Path(tmpdir) / "data" / "custom.db").resolve())
    assert config.llm_provider == "openai"
    assert config.embedding_dimension == 1536


def test_open_coprocessor_uses_explicit_db_path_override():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "skill.db"
        with open_coprocessor(project="skill-test", db_path=db_path, mock=True) as coprocessor:
            assert coprocessor.project == "skill-test"


def test_default_config_does_not_force_local_model_stack():
    config = load_config(Path(tempfile.mkdtemp()) / "missing.json")

    assert Path(config.db_path).is_absolute()
    assert config.llm_provider == ""
    assert config.llm_model == ""
    assert config.llm_base_url == ""


def test_load_config_reads_obsidian_root_path():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "nexus.json"
        path.write_text(
            """
{
  "db_path": "data/shared.db",
  "obsidian_root_path": "vault/Nexus"
}
""".strip(),
            encoding="utf-8",
        )

        config = load_config(path)

    assert config.db_path == str((Path(tmpdir) / "data" / "shared.db").resolve())
    assert config.obsidian_root_path == str((Path(tmpdir) / "vault" / "Nexus").resolve())


def test_inspect_storage_targets_reports_existing_db_and_obsidian_content(tmp_path):
    db_path = tmp_path / "shared.db"
    vault_root = tmp_path / "vault"
    vault_root.mkdir(parents=True)
    (vault_root / "existing.md").write_text("# Existing", encoding="utf-8")

    config_path = tmp_path / "config" / "nexus.json"
    save_config(path=config_path, db_path=db_path, obsidian_root_path=vault_root)
    with open_coprocessor(project="shared", config_path=config_path, mock=True) as coprocessor:
        coprocessor.extract("Remember that shared memory is enabled.", session_id="setup")

    result = inspect_storage_targets(db_path=db_path, obsidian_root_path=vault_root)

    assert result["db_path"] == str(db_path.resolve())
    assert result["db_exists"] is True
    assert result["db_has_content"] is True
    assert result["obsidian_root_path"] == str(vault_root.resolve())
    assert result["obsidian_exists"] is True
    assert result["obsidian_has_content"] is True


def test_inspect_storage_targets_does_not_treat_empty_db_as_existing_content(tmp_path):
    db_path = tmp_path / "empty.db"
    db_path.write_text("", encoding="utf-8")

    result = inspect_storage_targets(db_path=db_path)

    assert result["db_exists"] is True
    assert result["db_has_content"] is False


def test_save_config_writes_paths_and_preserves_other_fields(tmp_path):
    config_path = tmp_path / "config" / "nexus.json"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        """
{
  "log_level": "DEBUG",
  "llm_provider": "openai"
}
""".strip(),
        encoding="utf-8",
    )

    saved = save_config(
        path=config_path,
        db_path=tmp_path / "shared.db",
        obsidian_root_path=tmp_path / "vault",
    )
    reloaded = load_config(config_path)

    assert saved["config_path"] == str(config_path.resolve())
    assert reloaded.db_path == str((tmp_path / "shared.db").resolve())
    assert reloaded.obsidian_root_path == str((tmp_path / "vault").resolve())
    raw = config_path.read_text(encoding="utf-8")
    assert '"log_level": "DEBUG"' in raw
    assert '"llm_provider": "openai"' in raw

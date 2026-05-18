import tempfile
from pathlib import Path

from adapters.skill_entry import load_config, open_coprocessor
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
    assert config.db_path == "data/custom.db"
    assert config.llm_provider == "openai"
    assert config.embedding_dimension == 1536


def test_open_coprocessor_uses_explicit_db_path_override():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "skill.db"
        with open_coprocessor(project="skill-test", db_path=db_path) as coprocessor:
            assert coprocessor.project == "skill-test"

import json

from nexus.cli import build_parser, main
from nexus.exchange import read_exchange
from nexus.store import MemoryStore
from nexus.models import MemoryRecord, MemoryStatus, MemoryType


def test_cli_exposes_limited_portable_exchange_export():
    parser = build_parser()
    commands = parser._subparsers._group_actions[0].choices

    assert {"extract", "search", "inject", "feedback", "list", "stats", "maintain", "projection", "version"} <= set(commands)
    exchange = commands["exchange"]
    actions = exchange._subparsers._group_actions[0].choices
    assert set(actions) == {"export"}


def test_projection_cli_exposes_only_export():
    parser = build_parser()
    projection = parser._subparsers._group_actions[0].choices["projection"]
    commands = projection._subparsers._group_actions[0].choices

    assert {"export"} <= set(commands)
    assert "import" not in commands


def test_projection_export_default_output_is_not_cwd_relative_literal():
    parser = build_parser()
    projection = parser._subparsers._group_actions[0].choices["projection"]
    export_parser = projection._subparsers._group_actions[0].choices["export"]
    args = export_parser.parse_args([])

    assert args.output == ""


def test_projection_export_accepts_obsidian_friendly_flag():
    parser = build_parser()
    projection = parser._subparsers._group_actions[0].choices["projection"]
    export_parser = projection._subparsers._group_actions[0].choices["export"]
    args = export_parser.parse_args(["--obsidian-friendly"])

    assert args.obsidian_friendly is True


def test_setup_cli_exists_for_first_run_path_configuration():
    parser = build_parser()
    commands = parser._subparsers._group_actions[0].choices

    assert "setup" in commands


def test_setup_creates_database_without_provider(tmp_path, capsys):
    config_path = tmp_path / "config" / "nexus.json"
    db_path = tmp_path / "knowledge" / "nexus.db"
    obsidian_root = tmp_path / "knowledge"
    obsidian_root.mkdir(parents=True)

    exit_code = main(
        [
            "--config",
            str(config_path),
            "--db-path",
            str(db_path),
            "setup",
            "--obsidian-root",
            str(obsidian_root),
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["database"]["db_exists"] is True
    assert db_path.exists() is True


def test_stats_list_and_maintain_work_without_provider(tmp_path, capsys):
    config_path = tmp_path / "config" / "nexus.json"
    db_path = tmp_path / "knowledge" / "nexus.db"
    obsidian_root = tmp_path / "knowledge"
    obsidian_root.mkdir(parents=True)

    setup_exit = main(
        [
            "--config",
            str(config_path),
            "--db-path",
            str(db_path),
            "setup",
            "--obsidian-root",
            str(obsidian_root),
        ]
    )
    assert setup_exit == 0
    capsys.readouterr()

    with MemoryStore(str(db_path)) as store:
        store.save(
            MemoryRecord(
                project="codex",
                type=MemoryType.FACT,
                content="Shared Nexus memory lives in L:/knowledge/nexus.db",
                summary="Shared DB path",
                tags=["storage"],
                status=MemoryStatus.STABLE,
            )
        )

    stats_exit = main(["--config", str(config_path), "--project", "codex", "stats"])
    assert stats_exit == 0
    stats_payload = json.loads(capsys.readouterr().out)
    assert stats_payload["total"] == 1
    assert stats_payload["stable"] == 1

    list_exit = main(["--config", str(config_path), "--project", "codex", "list"])
    assert list_exit == 0
    list_output = capsys.readouterr().out
    assert "Shared Nexus memory lives in L:/knowledge/nexus.db" in list_output

    maintain_exit = main(["--config", str(config_path), "--project", "codex", "maintain"])
    assert maintain_exit == 0
    maintain_payload = json.loads(capsys.readouterr().out)
    assert maintain_payload == {"decayed": 0, "outdated": 0, "deleted": 0}


def _save_exchange_memory(db_path, *, project="codex", content="Selected synthetic memory"):
    with MemoryStore(str(db_path)) as store:
        return store.save(
            MemoryRecord(
                project=project,
                type=MemoryType.FACT,
                content=content,
                status=MemoryStatus.STABLE,
            )
        )


def test_exchange_cli_exports_only_selected_ids_without_printing_memory_content(tmp_path, capsys):
    db_path = tmp_path / "knowledge" / "nexus.db"
    memory_id = _save_exchange_memory(db_path)
    _save_exchange_memory(db_path, content="Unselected synthetic memory")
    output = tmp_path / "selected.exchange.json"

    result = main([
        "--project", "codex", "--db-path", str(db_path), "exchange", "export",
        "--id", memory_id, "--output", str(output), "--source-scope", "user-selected",
    ])

    captured = capsys.readouterr()
    assert result == 0
    assert "Selected synthetic memory" not in captured.out + captured.err
    payload = read_exchange(output)
    assert payload["manifest"]["record_count"] == 1
    assert payload["records"][0]["id"] == memory_id
    assert "Unselected synthetic memory" not in output.read_text(encoding="utf-8")


def test_exchange_cli_rejects_missing_or_cross_project_ids_without_output(tmp_path, capsys):
    db_path = tmp_path / "knowledge" / "nexus.db"
    memory_id = _save_exchange_memory(db_path, project="other", content="private synthetic text")
    output = tmp_path / "must-not-exist.json"

    result = main([
        "--project", "codex", "--db-path", str(db_path), "exchange", "export",
        "--id", memory_id, "--output", str(output), "--source-scope", "user-selected",
    ])

    captured = capsys.readouterr()
    assert result == 2
    assert not output.exists()
    assert "private synthetic text" not in captured.out + captured.err


def test_exchange_cli_rejects_sensitive_content_without_output(tmp_path, capsys):
    db_path = tmp_path / "knowledge" / "nexus.db"
    memory_id = _save_exchange_memory(db_path, content="api_key=supersecretvalue123")
    output = tmp_path / "must-not-exist.json"

    result = main([
        "--project", "codex", "--db-path", str(db_path), "exchange", "export",
        "--id", memory_id, "--output", str(output), "--source-scope", "user-selected",
    ])

    captured = capsys.readouterr()
    assert result == 2
    assert not output.exists()
    assert "supersecretvalue123" not in captured.out + captured.err


def test_exchange_cli_cannot_replace_database_file(tmp_path, capsys):
    db_path = tmp_path / "knowledge" / "nexus.db"
    memory_id = _save_exchange_memory(db_path)
    original = db_path.read_bytes()

    result = main([
        "--project", "codex", "--db-path", str(db_path), "exchange", "export",
        "--id", memory_id, "--output", str(db_path), "--source-scope", "user-selected",
    ])

    assert result == 2
    assert db_path.read_bytes() == original
    assert "cannot replace the database" in capsys.readouterr().err

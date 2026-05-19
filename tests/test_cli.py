from nexus.cli import build_parser


def test_cli_exposes_only_skill_1_0_commands():
    parser = build_parser()
    commands = parser._subparsers._group_actions[0].choices

    assert {"extract", "search", "inject", "feedback", "list", "stats", "maintain", "projection", "version"} <= set(commands)
    assert "exchange" not in commands


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

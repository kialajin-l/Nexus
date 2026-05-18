from nexus.cli import build_parser


def test_cli_exposes_only_skill_1_0_commands():
    parser = build_parser()
    commands = parser._subparsers._group_actions[0].choices

    assert {"extract", "search", "inject", "feedback", "list", "stats", "maintain", "projection", "version"} <= set(commands)
    assert "exchange" not in commands


def test_projection_cli_exposes_export_and_import():
    parser = build_parser()
    projection = parser._subparsers._group_actions[0].choices["projection"]
    commands = projection._subparsers._group_actions[0].choices

    assert {"export", "import"} <= set(commands)


def test_projection_export_default_output_is_not_cwd_relative_literal():
    parser = build_parser()
    projection = parser._subparsers._group_actions[0].choices["projection"]
    export_parser = projection._subparsers._group_actions[0].choices["export"]
    args = export_parser.parse_args([])

    assert args.output == ""

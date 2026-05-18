from nexus.cli import build_parser


def test_cli_exposes_only_skill_1_0_commands():
    parser = build_parser()
    commands = parser._subparsers._group_actions[0].choices

    assert {"extract", "search", "inject", "feedback", "list", "stats", "maintain", "version"} <= set(commands)
    assert "exchange" not in commands

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from nexus import __version__
from nexus.models import MemoryType
from nexus.projection import export_markdown_projection
from nexus.feedback import FeedbackLogger
from nexus.skill_entry import DEFAULT_CONFIG_PATH, ensure_database_ready, inspect_storage_targets, load_config, open_coprocessor, save_config
from nexus.store import MemoryStore


def cmd_extract(args: argparse.Namespace) -> int:
    text = args.text
    if args.file:
        text = Path(args.file).read_text(encoding="utf-8")

    with open_coprocessor(
        project=args.project,
        config_path=args.config,
        db_path=args.db_path,
        mock=args.mock,
    ) as coprocessor:
        records = coprocessor.extract(text, session_id=args.session_id or "")

    for record in records:
        print(f"[{record.type.value}] {record.content}")
        if record.summary:
            print(f"  summary: {record.summary}")
        if record.tags:
            print(f"  tags: {', '.join(record.tags)}")
    print(f"\nExtracted {len(records)} memories.")
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    with open_coprocessor(
        project=args.project,
        config_path=args.config,
        db_path=args.db_path,
        mock=args.mock,
    ) as coprocessor:
        results = coprocessor.retrieve(args.query, top_k=args.top_k)

    for scored in results:
        print(f"[{scored.score:.3f}] [{scored.record.type.value}] {scored.record.content}")
    print(f"\nFound {len(results)} results.")
    return 0


def cmd_inject(args: argparse.Namespace) -> int:
    with open_coprocessor(
        project=args.project,
        config_path=args.config,
        db_path=args.db_path,
        mock=args.mock,
    ) as coprocessor:
        text = coprocessor.inject(
            args.query,
            max_tokens=args.max_tokens,
            top_k=args.top_k,
            mode=args.mode,
        )
    print(text)
    return 0


def cmd_feedback(args: argparse.Namespace) -> int:
    config = load_config(args.config or DEFAULT_CONFIG_PATH)
    db_path = args.db_path or config.db_path

    with MemoryStore(db_path) as store:
        FeedbackLogger(store).log_feedback(args.memory_id, args.action, context=args.context)
    print(f"Feedback '{args.action}' recorded for memory {args.memory_id}.")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    types = []
    if args.type:
        types = [MemoryType(value.strip()) for value in args.type.split(",") if value.strip()]

    config = load_config(args.config or DEFAULT_CONFIG_PATH)
    db_path = args.db_path or config.db_path

    with MemoryStore(db_path) as store:
        from nexus.models import MemoryStatus, QueryFilter

        records = store.query(
            QueryFilter(
                project=args.project,
                types=types or [],
                statuses=[MemoryStatus.STABLE],
                limit=args.limit,
                offset=args.offset,
            )
        )

    for record in records:
        tags = f" [{', '.join(record.tags)}]" if record.tags else ""
        print(f"{record.id[:16]}... [{record.type.value}] {record.content[:80]}{tags}")
    print(f"\nTotal: {len(records)} memories.")
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    config = load_config(args.config or DEFAULT_CONFIG_PATH)
    db_path = args.db_path or config.db_path

    with MemoryStore(db_path) as store:
        from nexus.models import MemoryStatus

        stable = store.count(project=args.project, status=MemoryStatus.STABLE.value)
        candidate = store.count(project=args.project, status=MemoryStatus.CANDIDATE.value)
        deprecated = store.count(project=args.project, status=MemoryStatus.DEPRECATED.value)
        stats = {
            "project": args.project,
            "total": store.count(project=args.project),
            "active": stable,
            "deleted": deprecated,
            "outdated": deprecated,
            "stable": stable,
            "candidate": candidate,
            "deprecated": deprecated,
        }
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    return 0


def cmd_maintain(args: argparse.Namespace) -> int:
    config = load_config(args.config or DEFAULT_CONFIG_PATH)
    db_path = args.db_path or config.db_path

    with MemoryStore(db_path) as store:
        from nexus.memory_filter import MemoryFilter

        result = MemoryFilter(store=store).maintain(store, args.project)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def cmd_version(args: argparse.Namespace) -> int:
    print(f"Nexus Skill 1.1 / Core {__version__}")
    return 0


def cmd_setup(args: argparse.Namespace) -> int:
    config = load_config(args.config or DEFAULT_CONFIG_PATH)
    db_path = args.db_path or config.db_path
    obsidian_root = args.obsidian_root or config.obsidian_root_path

    saved = save_config(
        path=args.config or DEFAULT_CONFIG_PATH,
        db_path=db_path,
        obsidian_root_path=obsidian_root,
    )
    database = ensure_database_ready(db_path)
    inspection = inspect_storage_targets(
        db_path=db_path,
        obsidian_root_path=obsidian_root,
    )
    print(
        json.dumps(
            {
                "saved": saved,
                "database": database,
                "inspection": inspection,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def cmd_projection_export(args: argparse.Namespace) -> int:
    config = load_config(args.config or DEFAULT_CONFIG_PATH)
    db_path = args.db_path or config.db_path
    output_root = args.output or config.obsidian_root_path or str(Path(db_path).resolve().parent / "projection")

    with MemoryStore(db_path) as store:
        result = export_markdown_projection(
            store,
            args.project,
            output_root,
            group_by=args.group_by,
            obsidian_friendly=args.obsidian_friendly,
        )

    print(f"Exported {result['count']} memories to Markdown projection.")
    print(f"Saved to: {result['output_dir']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nexus",
        description="Nexus Skill / Plugin 1.1 - long-term memory entry built on Nexus Core 1.0",
    )
    parser.add_argument("--project", "-p", default="", help="Project identifier")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="Path to nexus.json")
    parser.add_argument("--db-path", default="", help="Override SQLite database path")
    parser.add_argument("--mock", action="store_true", help="Use mock LLM and embedder for verification")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    p_extract = subparsers.add_parser("extract", help="Extract memories from text")
    p_extract.add_argument("--text", "-t", default="", help="Text to extract from")
    p_extract.add_argument("--file", "-f", default="", help="File to extract from")
    p_extract.add_argument("--session-id", "-s", default="", help="Session ID")
    p_extract.set_defaults(func=cmd_extract)

    p_search = subparsers.add_parser("search", help="Retrieve relevant memories")
    p_search.add_argument("query", help="Search query")
    p_search.add_argument("--top-k", "-k", type=int, default=5, help="Number of results")
    p_search.set_defaults(func=cmd_search)

    p_inject = subparsers.add_parser("inject", help="Inject relevant memories into context")
    p_inject.add_argument("query", help="Task or question to support")
    p_inject.add_argument("--max-tokens", "-m", type=int, default=500, help="Max tokens for injection")
    p_inject.add_argument("--top-k", "-k", type=int, default=5, help="Number of memories to consider")
    p_inject.add_argument("--mode", choices=["task", "chat", "explore"], default="task", help="Injection mode")
    p_inject.set_defaults(func=cmd_inject)

    p_feedback = subparsers.add_parser("feedback", help="Record memory feedback")
    p_feedback.add_argument("memory_id", help="Memory ID")
    p_feedback.add_argument("action", choices=["accepted", "ignored", "corrected", "deleted"], help="Feedback action")
    p_feedback.add_argument("--context", default="", help="Optional feedback context")
    p_feedback.set_defaults(func=cmd_feedback)

    p_list = subparsers.add_parser("list", help="List stored memories")
    p_list.add_argument("--type", "-t", default="", help="Filter by type (comma-separated)")
    p_list.add_argument("--limit", "-n", type=int, default=20, help="Max results")
    p_list.add_argument("--offset", type=int, default=0, help="Offset")
    p_list.set_defaults(func=cmd_list)

    p_stats = subparsers.add_parser("stats", help="Show memory statistics")
    p_stats.set_defaults(func=cmd_stats)

    p_maintain = subparsers.add_parser("maintain", help="Run maintenance against stored memories")
    p_maintain.set_defaults(func=cmd_maintain)

    p_setup = subparsers.add_parser("setup", help="Save and inspect configured DB and Obsidian storage targets")
    p_setup.add_argument("--obsidian-root", default="", help="Override Obsidian vault export root")
    p_setup.set_defaults(func=cmd_setup)

    p_projection = subparsers.add_parser("projection", help="Export Markdown projection files")
    projection_subparsers = p_projection.add_subparsers(dest="projection_command", help="Projection actions")

    p_projection_export = projection_subparsers.add_parser("export", help="Export Markdown projection files")
    p_projection_export.add_argument(
        "--output",
        "-o",
        default="",
        help="Projection output root directory; defaults to a 'projection' folder next to the database",
    )
    p_projection_export.add_argument(
        "--group-by",
        choices=["flat", "topic", "type"],
        default="flat",
        help="How to organize exported Markdown files",
    )
    p_projection_export.add_argument(
        "--obsidian-friendly",
        action="store_true",
        help="Emit Obsidian-friendly Markdown formatting",
    )
    p_projection_export.set_defaults(func=cmd_projection_export)

    p_version = subparsers.add_parser("version", help="Show version")
    p_version.set_defaults(func=cmd_version)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 1

    if args.command in {"version", "setup"}:
        return args.func(args)

    if args.command == "projection" and not getattr(args, "projection_command", ""):
        parser.parse_args(["projection", "--help"])
        return 1

    if not args.project:
        print("Error: --project is required for all commands except 'version'", file=sys.stderr)
        return 1

    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

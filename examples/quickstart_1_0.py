"""
Nexus Skill / Plugin 1.0 Quick Start

This example shows the public 1.0 workflow and uses mock components so it can run
without forcing a specific local model stack.
"""

import sys
import tempfile
from pathlib import Path

from nexus import Config, MemoryCoprocessor, MemoryRiskLevel, ProjectionConfig, ProjectionMode, __version__
from nexus.embedder import MockEmbedder
from nexus.llm_client import MockLLMClient
from nexus.projection import export_markdown_projection, import_markdown_projection
from nexus.store import MemoryStore


def main():
    print(f"Nexus Skill / Plugin v{__version__} Quick Start")
    print("=" * 50)

    db_path = str(Path(tempfile.mkdtemp()) / "quickstart.db")
    config = Config(db_path=db_path)
    mock_response = (
        '{"memories": ['
        '{"type": "decision", "content": "Use PostgreSQL as the primary database.",'
        '"summary": "Primary database choice", "tags": ["database", "architecture"], "importance": 0.8},'
        '{"type": "rule", "content": "All API endpoints require JWT authentication.",'
        '"summary": "Authentication rule", "tags": ["security", "api"], "importance": 0.9}'
        "]}"
    )

    with MemoryCoprocessor(
        project="quickstart",
        db_path=db_path,
        config=config,
        llm_client=MockLLMClient(responses=[mock_response]),
        embedder=MockEmbedder(),
    ) as coproc:

        print("\n--- Step 1: Extract memories ---")
        text = (
            "We are building a data platform called DataPulse. "
            "We decided to use PostgreSQL as the primary database because it has the best JSON support. "
            "Deployment target is AWS us-east-1. "
            "All API endpoints must require JWT authentication tokens. "
            "User prefers dark mode UI and Chinese documentation."
        )
        records = coproc.extract(text)
        print(f"Extracted {len(records)} memories:")
        for rec in records:
            print(f"  [{rec.type.value}] {rec.content}")

        print("\n--- Step 2: Retrieve memories ---")
        results = coproc.retrieve("database choice")
        print(f"Found {len(results)} results for 'database choice':")
        for sm in results:
            print(f"  [{sm.score:.3f}] [{sm.record.type.value}] {sm.record.content}")

        print("\n--- Step 3: Inject context ---")
        context = coproc.inject("What database should we use?")
        if context:
            print("Injected context:")
            for line in context.split("\n"):
                if line.strip():
                    print(f"  {line}")
        else:
            print("No relevant memories to inject.")

        print("\n--- Step 4: Give feedback ---")
        if records:
            coproc.feedback(records[0].id, "accepted")
            print(f"Accepted memory: {records[0].id[:16]}...")

        print("\n--- Step 5: View stats ---")
        stats = coproc.stats()
        print(f"Project: {stats['project']}")
        print(f"Total memories: {stats['total']}")
        print(f"Stable: {stats['stable']}")
        print(f"Candidate: {stats['candidate']}")

        print("\n--- Step 6: List memories ---")
        all_memories = coproc.list_memories(limit=10)
        for rec in all_memories:
            print(f"  [{rec.type.value}] {rec.content[:50]}")

    print("\n--- Step 7: Export Markdown projection ---")
    with MemoryStore(db_path) as store:
        export_result = export_markdown_projection(store, "quickstart", str(Path(db_path).parent / "projection"))
    print(f"Exported {export_result['count']} Markdown files.")

    first_projection = Path(export_result["files"][0])
    content = first_projection.read_text(encoding="utf-8")
    content = content.replace("Use PostgreSQL as the primary database.", "Use PostgreSQL 16 as the primary database.")
    first_projection.write_text(content, encoding="utf-8")

    print("\n--- Step 8: Import edited Markdown projection ---")
    with MemoryStore(db_path) as store:
        import_result = import_markdown_projection(
            store,
            str(first_projection.parent),
            ProjectionConfig(
                enabled=True,
                mode=ProjectionMode.RELAXED_WRITEBACK,
                risk_level=MemoryRiskLevel.L1_PERSONAL,
                root_path=str(first_projection.parent),
            ),
        )
    print(f"Updated: {import_result['updated']}, skipped: {import_result['skipped']}")

    print("\n" + "=" * 50)
    print("Quick Start complete!")
    print(f"Database saved to: {db_path}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)

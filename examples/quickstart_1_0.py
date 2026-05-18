"""
Nexus Skill / Plugin 1.0 Quick Start Guide

This script demonstrates the minimal workflow to get started with Nexus.
Run it with: python examples/quickstart_1_0.py

Prerequisites:
  - pip install -e .[ollama]
  - Ollama running locally with qwen3:4b and nomic-embed-text pulled
"""

import sys
import tempfile
from pathlib import Path

from nexus import MemoryCoprocessor, Config, __version__


def main():
    print(f"Nexus Skill / Plugin v{__version__} Quick Start")
    print("=" * 50)

    db_path = str(Path(tempfile.mkdtemp()) / "quickstart.db")
    config = Config(
        llm_provider="ollama",
        llm_base_url="http://localhost:11434",
        llm_model="qwen3:4b",
        embedding_model="nomic-embed-text",
    )

    with MemoryCoprocessor(project="quickstart", db_path=db_path, config=config) as coproc:

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

    print("\n" + "=" * 50)
    print("Quick Start complete!")
    print(f"Database saved to: {db_path}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        print("\nPrerequisites:", file=sys.stderr)
        print("  1. pip install -e .[ollama]", file=sys.stderr)
        print("  2. ollama pull qwen3:4b", file=sys.stderr)
        print("  3. ollama pull nomic-embed-text", file=sys.stderr)
        sys.exit(1)

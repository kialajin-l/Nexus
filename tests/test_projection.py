from pathlib import Path

from nexus.models import MemoryRecord, MemoryRiskLevel, MemoryStatus, MemoryType, ProjectionConfig, ProjectionMode
from nexus.projection import export_markdown_projection, import_markdown_projection
from nexus.store import MemoryStore


def test_projection_export_and_import_roundtrip(tmp_path):
    db_path = tmp_path / "nexus.db"
    projection_root = tmp_path / "projection"

    with MemoryStore(str(db_path)) as store:
        record = MemoryRecord(
            project="demo",
            type=MemoryType.FACT,
            content="Original memory",
            summary="Original summary",
            tags=["alpha"],
            status=MemoryStatus.STABLE,
        )
        store.save(record)

        export_result = export_markdown_projection(store, "demo", str(projection_root))
        assert export_result["count"] == 1

    projection_file = Path(export_result["files"][0])
    text = projection_file.read_text(encoding="utf-8")
    text = text.replace("Original memory", "Edited memory")
    text = text.replace("Original summary", "Edited summary")
    text = text.replace("tags: [alpha]", "tags: [alpha, beta]")
    projection_file.write_text(text, encoding="utf-8")

    with MemoryStore(str(db_path)) as store:
        import_result = import_markdown_projection(
            store,
            str(projection_file.parent),
            ProjectionConfig(
                enabled=True,
                mode=ProjectionMode.RELAXED_WRITEBACK,
                risk_level=MemoryRiskLevel.L1_PERSONAL,
                root_path=str(projection_file.parent),
            ),
        )
        updated = store.get(record.id)

    assert import_result == {"updated": 1, "skipped": 0}
    assert updated is not None
    assert updated.content == "Edited memory"
    assert updated.summary == "Edited summary"
    assert updated.tags == ["alpha", "beta"]


def test_projection_export_supports_obsidian_friendly_topic_layout(tmp_path):
    db_path = tmp_path / "nexus.db"
    vault_root = tmp_path / "vault"

    with MemoryStore(str(db_path)) as store:
        record = MemoryRecord(
            project="demo",
            topic="Product Decisions",
            type=MemoryType.DECISION,
            content="Ship the Obsidian export in 1.1",
            summary="Obsidian export decision",
            tags=["obsidian", "release"],
            status=MemoryStatus.STABLE,
        )
        store.save(record)

        export_result = export_markdown_projection(
            store,
            "demo",
            str(vault_root),
            group_by="topic",
            obsidian_friendly=True,
        )

    exported = Path(export_result["files"][0])
    assert export_result["output_dir"] == str((vault_root / "demo").resolve())
    assert exported.parent.name == "Product_Decisions"
    assert exported.name == f"{record.id}.md"

    text = exported.read_text(encoding="utf-8")
    assert "format_version: nexus-projection-v1" in text
    assert "obsidian-compatible: true" in text
    assert "# Ship the Obsidian export in 1.1" in text
    assert "tags: [obsidian, release]" in text

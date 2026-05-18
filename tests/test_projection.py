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

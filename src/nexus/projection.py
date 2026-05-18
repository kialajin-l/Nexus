from __future__ import annotations

from pathlib import Path

from nexus.models import MemoryRecord, MemoryStatus, ProjectionConfig, QueryFilter
from nexus.store import MemoryStore


def export_markdown_projection(
    store: MemoryStore,
    project: str,
    output_root: str,
) -> dict[str, object]:
    project_dir = Path(output_root) / project
    project_dir.mkdir(parents=True, exist_ok=True)

    records = store.query(
        QueryFilter(
            project=project,
            statuses=[MemoryStatus.CANDIDATE, MemoryStatus.STABLE],
            limit=100000,
        )
    )

    files: list[str] = []
    for record in records:
        file_path = project_dir / f"{record.id}.md"
        file_path.write_text(_render_memory_markdown(record), encoding="utf-8")
        files.append(str(file_path))

    return {
        "project": project,
        "output_dir": str(project_dir),
        "count": len(files),
        "files": files,
    }


def import_markdown_projection(
    store: MemoryStore,
    project_dir: str,
    config: ProjectionConfig,
) -> dict[str, int]:
    if not config.enabled or config.mode == config.mode.READ_ONLY:
        files = list(Path(project_dir).glob("*.md"))
        return {"updated": 0, "skipped": len(files)}

    updated = 0
    skipped = 0
    for file_path in Path(project_dir).glob("*.md"):
        parsed = _parse_memory_markdown(file_path.read_text(encoding="utf-8"))
        memory_id = parsed.get("id", "")
        if not memory_id:
            skipped += 1
            continue

        current = store.get(memory_id)
        if current is None:
            skipped += 1
            continue

        updates = {}
        for field_name in ("content", "summary", "tags"):
            if field_name not in parsed:
                continue
            if not config.can_edit_field(field_name):
                continue
            new_value = parsed[field_name]
            current_value = getattr(current, field_name)
            if new_value != current_value:
                updates[field_name] = new_value

        if updates:
            store.update(memory_id, updates)
            updated += 1
        else:
            skipped += 1

    return {"updated": updated, "skipped": skipped}


def _render_memory_markdown(record: MemoryRecord) -> str:
    tags = ", ".join(record.tags)
    lines = [
        "---",
        f"id: {record.id}",
        f"project: {record.project}",
        f"session_id: {record.session_id}",
        f"topic: {record.topic}",
        f"type: {record.type.value}",
        f"status: {record.status.value}",
        f"importance: {record.importance}",
        f"confidence: {record.confidence}",
        f"source_kind: {record.source_kind}",
        f"source_ref: {record.source_ref}",
        f"source_level: {record.source_level}",
        f"created_at: {record.created_at}",
        f"updated_at: {record.updated_at}",
        f"tags: [{tags}]",
        "---",
        "",
        "content:",
        record.content,
        "",
        "summary:",
        record.summary,
        "",
    ]
    return "\n".join(lines)


def _parse_memory_markdown(text: str) -> dict[str, object]:
    lines = text.splitlines()
    if len(lines) < 3 or lines[0].strip() != "---":
        return {}

    index = 1
    frontmatter: dict[str, str] = {}
    while index < len(lines):
        line = lines[index]
        index += 1
        if line.strip() == "---":
            break
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        frontmatter[key.strip()] = value.strip()

    sections: dict[str, list[str]] = {}
    current_section = ""
    while index < len(lines):
        line = lines[index]
        index += 1
        if line.endswith(":") and line[:-1] in {"content", "summary"}:
            current_section = line[:-1]
            sections[current_section] = []
            continue
        if current_section:
            sections[current_section].append(line)

    tags_raw = frontmatter.get("tags", "[]").strip()
    tags: list[str] = []
    if tags_raw.startswith("[") and tags_raw.endswith("]"):
        inner = tags_raw[1:-1].strip()
        if inner:
            tags = [part.strip() for part in inner.split(",") if part.strip()]

    return {
        "id": frontmatter.get("id", ""),
        "content": "\n".join(sections.get("content", [])).strip(),
        "summary": "\n".join(sections.get("summary", [])).strip(),
        "tags": tags,
    }

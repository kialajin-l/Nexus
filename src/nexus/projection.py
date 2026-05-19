from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone

from nexus.models import MemoryRecord, MemoryStatus, ProjectionConfig, QueryFilter
from nexus.store import MemoryStore

PROJECTION_FORMAT_VERSION = "nexus-projection-v1"


def export_markdown_projection(
    store: MemoryStore,
    project: str,
    output_root: str,
    group_by: str = "flat",
    obsidian_friendly: bool = False,
) -> dict[str, object]:
    project_dir = (Path(output_root) / project).resolve()
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
        target_dir = _resolve_projection_dir(project_dir, record, group_by)
        target_dir.mkdir(parents=True, exist_ok=True)
        file_path = target_dir / f"{record.id}.md"
        file_path.write_text(
            _render_memory_markdown(record, obsidian_friendly=obsidian_friendly),
            encoding="utf-8",
        )
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
    for file_path in Path(project_dir).rglob("*.md"):
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


def _resolve_projection_dir(project_dir: Path, record: MemoryRecord, group_by: str) -> Path:
    if group_by == "topic":
        return project_dir / _sanitize_projection_part(record.topic or record.project)
    if group_by == "type":
        return project_dir / record.type.value
    return project_dir


def _render_memory_markdown(record: MemoryRecord, *, obsidian_friendly: bool = False) -> str:
    tags = ", ".join(record.tags)
    exported_at = datetime.now(timezone.utc).isoformat()
    lines = [
        "---",
        f"format_version: {PROJECTION_FORMAT_VERSION}",
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
        f"exported_at: {exported_at}",
        f"obsidian-compatible: {'true' if obsidian_friendly else 'false'}",
        f"tags: [{tags}]",
        "---",
        "",
    ]

    if obsidian_friendly:
        lines.extend(
            [
                f"# {record.content}",
                "",
                f"- Type: {record.type.value}",
                f"- Status: {record.status.value}",
                f"- Topic: {record.topic}",
                "",
                "## Content",
                record.content,
                "",
                "## Summary",
                record.summary,
                "",
            ]
        )
        return "\n".join(lines)

    lines.extend(
        [
        "content:",
        record.content,
        "",
        "summary:",
        record.summary,
        "",
        ]
    )
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


def _sanitize_projection_part(value: str) -> str:
    cleaned = []
    for ch in value:
        if ch.isalnum() or ch in {"-", "_"}:
            cleaned.append(ch)
        else:
            cleaned.append("_")
    result = "".join(cleaned).strip("_")
    return result or "default"

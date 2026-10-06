from __future__ import annotations

import hashlib
import json
import math
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from nexus.models import MemoryRecord, MemoryStatus, MemoryType

EXCHANGE_SCHEMA = "NEXUS_PORTABLE_MEMORY_EXCHANGE_V1"
MAX_RECORDS = 100_000
MAX_EXCHANGE_BYTES = 32 * 1024 * 1024

_RECORD_FIELDS = {
    "id",
    "project",
    "session_id",
    "topic",
    "type",
    "status",
    "content",
    "summary",
    "importance",
    "confidence",
    "source_kind",
    "source_ref",
    "source_level",
    "source",
    "tags",
    "created_at",
    "updated_at",
}


class ExchangeError(ValueError):
    """Raised when a portable exchange package is invalid or unsafe."""


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _record_payload(record: MemoryRecord) -> dict[str, Any]:
    if record.status not in {MemoryStatus.CANDIDATE, MemoryStatus.STABLE}:
        raise ExchangeError("only candidate and stable memories may be exported")
    return {
        "id": record.id,
        "project": record.project,
        "session_id": record.session_id,
        "topic": record.topic,
        "type": record.type.value,
        "status": record.status.value,
        "content": record.content,
        "summary": record.summary,
        "importance": record.importance,
        "confidence": record.confidence,
        "source_kind": record.source_kind,
        "source_ref": record.source_ref,
        "source_level": record.source_level,
        "source": {"type": record.source.type, "ref": record.source.ref},
        "tags": list(record.tags),
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }


def _records_hash(records: list[dict[str, Any]]) -> str:
    return hashlib.sha256(_canonical_json(records).encode("utf-8")).hexdigest()


def build_exchange(
    records: Iterable[MemoryRecord],
    *,
    source_scope: str,
    producer_version: str = "1.0.0",
    created_at: str | None = None,
) -> dict[str, Any]:
    if not isinstance(source_scope, str) or not source_scope.strip():
        raise ExchangeError("source_scope must be a non-empty string")
    selected = [_record_payload(record) for record in records]
    if len(selected) > MAX_RECORDS:
        raise ExchangeError("record_count exceeds exchange limit")
    payload = {
        "schema": EXCHANGE_SCHEMA,
        "producer": {"edition": "open-skill", "version": producer_version},
        "created_at": created_at or datetime.now(timezone.utc).isoformat(),
        "source_scope": source_scope,
        "records": selected,
        "manifest": {
            "record_count": len(selected),
            "content_sha256": _records_hash(selected),
        },
    }
    return validate_exchange(payload)


def validate_exchange(payload: object) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ExchangeError("exchange must be a JSON object")
    required = {"schema", "producer", "created_at", "source_scope", "records", "manifest"}
    if set(payload) != required:
        raise ExchangeError("exchange has unsupported or missing top-level fields")
    if payload["schema"] != EXCHANGE_SCHEMA:
        raise ExchangeError("unsupported exchange schema")
    producer = payload["producer"]
    if not isinstance(producer, dict) or set(producer) != {"edition", "version"}:
        raise ExchangeError("invalid producer metadata")
    if producer["edition"] != "open-skill" or not isinstance(producer["version"], str):
        raise ExchangeError("invalid producer metadata")
    if not isinstance(payload["created_at"], str) or not payload["created_at"]:
        raise ExchangeError("created_at must be a non-empty string")
    if not isinstance(payload["source_scope"], str) or not payload["source_scope"].strip():
        raise ExchangeError("source_scope must be a non-empty string")

    records = payload["records"]
    if not isinstance(records, list) or len(records) > MAX_RECORDS:
        raise ExchangeError("records must be a bounded list")
    normalized: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for record in records:
        if not isinstance(record, dict) or set(record) != _RECORD_FIELDS:
            raise ExchangeError("record has unsupported or missing fields")
        if not isinstance(record["id"], str) or not record["id"]:
            raise ExchangeError("record id is required")
        if record["id"] in seen_ids:
            raise ExchangeError("duplicate record id")
        seen_ids.add(record["id"])
        if not isinstance(record["project"], str) or not record["project"]:
            raise ExchangeError("record project is required")
        if not isinstance(record["content"], str) or not record["content"]:
            raise ExchangeError("record content is required")
        if record["type"] not in {item.value for item in MemoryType}:
            raise ExchangeError("unsupported record type")
        if record["status"] not in {MemoryStatus.CANDIDATE.value, MemoryStatus.STABLE.value}:
            raise ExchangeError("unsupported record status")
        if not isinstance(record["tags"], list) or not all(isinstance(tag, str) for tag in record["tags"]):
            raise ExchangeError("record tags must be a list of strings")
        if not isinstance(record["source"], dict) or set(record["source"]) != {"type", "ref"}:
            raise ExchangeError("invalid record source")
        for field in ("session_id", "topic", "summary", "source_kind", "source_ref", "source_level", "created_at", "updated_at"):
            if not isinstance(record[field], str):
                raise ExchangeError(f"record {field} must be a string")
        for field in ("importance", "confidence"):
            if isinstance(record[field], bool) or not isinstance(record[field], (int, float)) or not math.isfinite(record[field]):
                raise ExchangeError(f"record {field} must be numeric")
        normalized.append(record)

    manifest = payload["manifest"]
    if not isinstance(manifest, dict) or set(manifest) != {"record_count", "content_sha256"}:
        raise ExchangeError("invalid exchange manifest")
    if manifest["record_count"] != len(normalized):
        raise ExchangeError("record count does not match manifest")
    expected_hash = _records_hash(normalized)
    if manifest["content_sha256"] != expected_hash:
        raise ExchangeError("record hash does not match manifest")
    return payload


def write_exchange(path: str | Path, records: Iterable[MemoryRecord], *, source_scope: str) -> dict[str, Any]:
    payload = build_exchange(records, source_scope=source_scope)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, sort_keys=True, indent=2)
            handle.write("\n")
        os.replace(temporary, target)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise
    return payload


def read_exchange(path: str | Path) -> dict[str, Any]:
    target = Path(path)
    try:
        if target.stat().st_size > MAX_EXCHANGE_BYTES:
            raise ExchangeError("exchange file is too large")
        payload = json.loads(target.read_text(encoding="utf-8"))
    except ExchangeError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ExchangeError("unable to read exchange package") from exc
    return validate_exchange(payload)


def records_from_exchange(payload: object) -> list[MemoryRecord]:
    validated = validate_exchange(payload)
    return [MemoryRecord.from_dict(record) for record in validated["records"]]


__all__ = [
    "EXCHANGE_SCHEMA",
    "ExchangeError",
    "MAX_EXCHANGE_BYTES",
    "build_exchange",
    "read_exchange",
    "records_from_exchange",
    "validate_exchange",
    "write_exchange",
]

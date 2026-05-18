from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def _new_id() -> str:
    return f"mem_{uuid.uuid4().hex[:24]}"


class MemoryType(str, Enum):
    FACT = "fact"
    DECISION = "decision"
    PREFERENCE = "preference"
    RULE = "rule"
    TODO = "todo"


class MemoryStatus(str, Enum):
    CANDIDATE = "candidate"
    STABLE = "stable"
    DEPRECATED = "deprecated"
    ACTIVE = "stable"
    IGNORED = "candidate"
    OUTDATED = "deprecated"
    DELETED = "deprecated"

    @classmethod
    def _missing_(cls, value: object) -> MemoryStatus | None:
        legacy = {
            "active": cls.STABLE,
            "ignored": cls.CANDIDATE,
            "outdated": cls.DEPRECATED,
            "deleted": cls.DEPRECATED,
        }
        if isinstance(value, str):
            return legacy.get(value)
        return None


class FeedbackAction(str, Enum):
    ACCEPTED = "accepted"
    IGNORED = "ignored"
    CORRECTED = "corrected"
    DELETED = "deleted"


class ProjectionMode(str, Enum):
    READ_ONLY = "read_only"
    CONTROLLED_WRITEBACK = "controlled_writeback"
    RELAXED_WRITEBACK = "relaxed_writeback"


class MemoryRiskLevel(str, Enum):
    L1_PERSONAL = "L1_personal"
    L2_EXCHANGE = "L2_exchange"
    L3_GOVERNED = "L3_governed"
    L4_CORE = "L4_core"


@dataclass
class SourceInfo:
    type: str = ""
    ref: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SourceInfo:
        return cls(type=data.get("type", ""), ref=data.get("ref", ""))


@dataclass
class MemoryRecord:
    project: str
    type: MemoryType
    content: str
    id: str = field(default_factory=_new_id)
    session_id: str = ""
    topic: str = ""
    summary: str = ""
    tags: list[str] = field(default_factory=list)
    importance: float = 0.5
    status: MemoryStatus = MemoryStatus.CANDIDATE
    confidence: float = 0.5
    source_kind: str = ""
    source_ref: str = ""
    source_level: str = "L2"
    source: SourceInfo = field(default_factory=SourceInfo)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    access_count: int = 0
    last_accessed_at: str = ""

    def __post_init__(self) -> None:
        if not self.topic:
            self.topic = self.project
        if not self.source_kind and self.source.type:
            self.source_kind = self.source.type
        if not self.source_ref and self.source.ref:
            self.source_ref = self.source.ref
        if not self.source.type and self.source_kind:
            self.source.type = self.source_kind
        if not self.source.ref and self.source_ref:
            self.source.ref = self.source_ref

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["type"] = self.type.value
        d["anchor_type"] = self.type.value
        d["status"] = self.status.value
        d["source"] = (
            self.source.to_dict() if isinstance(self.source, SourceInfo) else self.source
        )
        d["tags"] = json.dumps(self.tags, ensure_ascii=False)
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MemoryRecord:
        source_data = data.get("source", {})
        if isinstance(source_data, str):
            try:
                source_data = json.loads(source_data)
            except (json.JSONDecodeError, TypeError):
                source_data = {}
        source = SourceInfo.from_dict(source_data) if source_data else SourceInfo()

        tags_data = data.get("tags", [])
        if isinstance(tags_data, str):
            try:
                tags_data = json.loads(tags_data)
            except (json.JSONDecodeError, TypeError):
                tags_data = []

        return cls(
            id=data.get("id", _new_id()),
            project=data["project"],
            session_id=data.get("session_id", ""),
            topic=data.get("topic", data.get("project", "")),
            type=MemoryType(data.get("anchor_type", data["type"])),
            content=data["content"],
            summary=data.get("summary", ""),
            tags=tags_data,
            importance=float(data.get("importance", 0.5)),
            status=MemoryStatus(data.get("status", MemoryStatus.CANDIDATE.value)),
            confidence=float(data.get("confidence", data.get("importance", 0.5))),
            source_kind=data.get("source_kind", source_data.get("type", "")),
            source_ref=data.get("source_ref", source_data.get("ref", "")),
            source_level=data.get("source_level", "L2"),
            source=source,
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            access_count=int(data.get("access_count", 0)),
            last_accessed_at=data.get("last_accessed_at", ""),
        )

    def touch(self) -> None:
        self.access_count += 1
        self.last_accessed_at = datetime.now(timezone.utc).isoformat()
        self.updated_at = self.last_accessed_at


@dataclass
class ScoredMemory:
    record: MemoryRecord
    score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {"record": self.record.to_dict(), "score": self.score}


@dataclass
class ExtractMetadata:
    project: str
    source_type: str = "conversation"
    session_id: str = ""
    source_ref: str = ""
    topic: str = ""
    source_level: str = "L1"


@dataclass
class QueryFilter:
    project: str = ""
    topic: str = ""
    types: list[MemoryType] = field(default_factory=list)
    statuses: list[MemoryStatus] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    source_levels: list[str] = field(default_factory=list)
    min_importance: float = 0.0
    since: str = ""
    until: str = ""
    limit: int = 100
    offset: int = 0


@dataclass
class RetrievalFilters:
    types: list[MemoryType] = field(default_factory=list)
    statuses: list[MemoryStatus] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    source_levels: list[str] = field(default_factory=list)
    min_importance: float = 0.0
    since: str = ""
    until: str = ""


@dataclass
class ProjectionConfig:
    enabled: bool = False
    mode: ProjectionMode = ProjectionMode.READ_ONLY
    risk_level: MemoryRiskLevel = MemoryRiskLevel.L2_EXCHANGE
    root_path: str = ""

    def can_edit_field(self, field_name: str) -> bool:
        if not self.enabled:
            return False
        if self.mode == ProjectionMode.READ_ONLY:
            return False

        low_risk_fields = {
            "content",
            "summary",
            "tags",
            "note",
            "notes",
            "display_title",
        }
        medium_risk_fields = {
            "topic",
            "category",
            "classification",
            "relation",
            "source_description",
        }

        if field_name in low_risk_fields:
            return self.risk_level in {
                MemoryRiskLevel.L1_PERSONAL,
                MemoryRiskLevel.L2_EXCHANGE,
                MemoryRiskLevel.L3_GOVERNED,
            }
        if field_name in medium_risk_fields:
            return self.risk_level == MemoryRiskLevel.L1_PERSONAL
        return False

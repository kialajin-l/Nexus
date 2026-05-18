from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import numpy as np

from nexus.models import MemoryRecord, MemoryStatus, MemoryType, QueryFilter, SourceInfo


_SCHEMA_PATH = Path(__file__).parent / "schema.sql"


class MemoryStore:
    def __init__(self, db_path: str = "data/nexus.db") -> None:
        self._db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._init_schema()

    def _init_schema(self) -> None:
        schema_sql = _SCHEMA_PATH.read_text(encoding="utf-8")
        self._conn.executescript(schema_sql)
        self._ensure_columns()
        self._conn.commit()

    def _ensure_columns(self) -> None:
        existing = {
            row["name"] for row in self._conn.execute("PRAGMA table_info(memories)").fetchall()
        }
        missing_columns = {
            "topic": "TEXT",
            "confidence": "REAL NOT NULL DEFAULT 0.5",
            "source_kind": "TEXT",
            "source_level": "TEXT",
        }
        for name, ddl in missing_columns.items():
            if name not in existing:
                self._conn.execute(f"ALTER TABLE memories ADD COLUMN {name} {ddl}")

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> MemoryStore:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def save(self, record: MemoryRecord) -> str:
        d = record.to_dict()
        embedding_blob = d.pop("embedding", None)
        if embedding_blob is not None:
            embedding_blob = np.array(embedding_blob, dtype=np.float32).tobytes()
        self._conn.execute(
            """INSERT OR REPLACE INTO memories
               (id, project, session_id, topic, type, content, summary, importance, status,
                confidence, source_kind, source_level, source_type, source_ref, tags, embedding,
                created_at, updated_at, access_count, last_accessed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                d["id"],
                d["project"],
                d.get("session_id"),
                d.get("topic"),
                d["type"],
                d["content"],
                d.get("summary"),
                d["importance"],
                d["status"],
                d.get("confidence", 0.5),
                d.get("source_kind", ""),
                d.get("source_level", "L2"),
                d["source"].get("type", ""),
                d.get("source_ref", d["source"].get("ref", "")),
                d.get("tags", "[]"),
                embedding_blob,
                d["created_at"],
                d["updated_at"],
                d.get("access_count", 0),
                d.get("last_accessed_at", ""),
            ),
        )
        self._conn.commit()
        return record.id

    def save_batch(self, records: list[MemoryRecord]) -> list[str]:
        return [self.save(record) for record in records]

    def get(self, memory_id: str) -> MemoryRecord | None:
        row = self._conn.execute(
            "SELECT * FROM memories WHERE id = ?", (memory_id,)
        ).fetchone()
        if row is None:
            return None
        return self._row_to_record(row)

    def update(self, memory_id: str, updates: dict[str, Any]) -> bool:
        if not updates:
            return False
        set_clauses = []
        values = []
        for key, value in updates.items():
            if key == "tags" and isinstance(value, list):
                value = json.dumps(value, ensure_ascii=False)
            if key == "type" and isinstance(value, MemoryType):
                value = value.value
            if key == "status" and isinstance(value, MemoryStatus):
                value = value.value
            set_clauses.append(f"{key} = ?")
            values.append(value)
        values.append(memory_id)
        cursor = self._conn.execute(
            f"UPDATE memories SET {', '.join(set_clauses)} WHERE id = ?",
            values,
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def delete(self, memory_id: str) -> bool:
        return self.update(memory_id, {"status": MemoryStatus.DEPRECATED.value})

    def query(self, f: QueryFilter) -> list[MemoryRecord]:
        clauses = []
        params: list[Any] = []

        if f.project:
            clauses.append("project = ?")
            params.append(f.project)
        if f.topic:
            clauses.append("topic = ?")
            params.append(f.topic)
        if f.types:
            placeholders = ",".join("?" * len(f.types))
            clauses.append(f"type IN ({placeholders})")
            params.extend(t.value for t in f.types)
        if f.statuses:
            placeholders = ",".join("?" * len(f.statuses))
            clauses.append(f"status IN ({placeholders})")
            params.extend(s.value for s in f.statuses)
        else:
            clauses.append("status != 'deprecated'")
        if f.tags:
            for tag in f.tags:
                clauses.append("tags LIKE ?")
                params.append(f'%"{tag}"%')
        if f.source_levels:
            placeholders = ",".join("?" * len(f.source_levels))
            clauses.append(f"source_level IN ({placeholders})")
            params.extend(f.source_levels)
        if f.min_importance > 0:
            clauses.append("importance >= ?")
            params.append(f.min_importance)
        if f.since:
            clauses.append("created_at >= ?")
            params.append(f.since)
        if f.until:
            clauses.append("created_at <= ?")
            params.append(f.until)

        where = " AND ".join(clauses) if clauses else "1=1"
        sql = f"SELECT * FROM memories WHERE {where} ORDER BY updated_at DESC LIMIT ? OFFSET ?"
        params.extend([f.limit, f.offset])

        rows = self._conn.execute(sql, params).fetchall()
        return [self._row_to_record(row) for row in rows]

    def search_by_keywords(
        self, keywords: list[str], project: str, top_k: int = 10
    ) -> list[tuple[MemoryRecord, float]]:
        if not keywords:
            return []
        import re

        cleaned = []
        for kw in keywords:
            kw = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]", "", kw)
            if kw:
                cleaned.append(kw)
        if not cleaned:
            return []

        query_str = " OR ".join(cleaned)
        rows = self._conn.execute(
            """SELECT m.*, rank
               FROM memories_fts f
               JOIN memories m ON m.id = (SELECT id FROM memories WHERE rowid = f.rowid)
               WHERE memories_fts MATCH ? AND m.project = ? AND m.status IN ('stable', 'candidate')
               ORDER BY rank
               LIMIT ?""",
            (query_str, project, top_k),
        ).fetchall()
        results = []
        for row in rows:
            record = self._row_to_record(row)
            score = -float(row["rank"]) if row["rank"] else 0.0
            results.append((record, score))
        return results

    def search_by_vector(
        self,
        query_vector: list[float] | np.ndarray,
        project: str,
        top_k: int = 10,
    ) -> list[tuple[MemoryRecord, float]]:
        rows = self._conn.execute(
            "SELECT * FROM memories WHERE project = ? AND status IN ('stable', 'candidate') AND embedding IS NOT NULL",
            (project,),
        ).fetchall()
        if not rows:
            return []

        q = np.array(query_vector, dtype=np.float32)
        q_norm = np.linalg.norm(q)
        if q_norm == 0:
            return []

        scored = []
        for row in rows:
            emb_bytes = row["embedding"]
            if emb_bytes is None:
                continue
            emb = np.frombuffer(emb_bytes, dtype=np.float32)
            emb_norm = np.linalg.norm(emb)
            if emb_norm == 0:
                continue
            similarity = float(np.dot(q, emb) / (q_norm * emb_norm))
            scored.append((self._row_to_record(row), similarity))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def save_embedding(self, memory_id: str, embedding: list[float] | np.ndarray) -> bool:
        emb_bytes = np.array(embedding, dtype=np.float32).tobytes()
        cursor = self._conn.execute(
            "UPDATE memories SET embedding = ? WHERE id = ?",
            (emb_bytes, memory_id),
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def count(self, project: str = "", status: str = "") -> int:
        clauses = []
        params: list[Any] = []
        if project:
            clauses.append("project = ?")
            params.append(project)
        if status:
            status_map = {
                "active": MemoryStatus.STABLE.value,
                "ignored": MemoryStatus.CANDIDATE.value,
                "outdated": MemoryStatus.DEPRECATED.value,
                "deleted": MemoryStatus.DEPRECATED.value,
            }
            status = status_map.get(status, status)
            clauses.append("status = ?")
            params.append(status)
        where = " AND ".join(clauses) if clauses else "1=1"
        row = self._conn.execute(
            f"SELECT COUNT(*) as cnt FROM memories WHERE {where}", params
        ).fetchone()
        return int(row["cnt"])

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> MemoryRecord:
        source = SourceInfo(
            type=(row["source_kind"] or row["source_type"] or ""),
            ref=row["source_ref"] or "",
        )
        tags_raw = row["tags"] or "[]"
        if isinstance(tags_raw, str):
            try:
                tags = json.loads(tags_raw)
            except (json.JSONDecodeError, TypeError):
                tags = []
        else:
            tags = []

        return MemoryRecord(
            id=row["id"],
            project=row["project"],
            session_id=row["session_id"] or "",
            topic=row["topic"] or row["project"],
            type=MemoryType(row["type"]),
            content=row["content"],
            summary=row["summary"] or "",
            tags=tags,
            importance=float(row["importance"]),
            status=MemoryStatus(row["status"]),
            confidence=float(row["confidence"]) if row["confidence"] is not None else float(row["importance"]),
            source_kind=(row["source_kind"] or row["source_type"] or ""),
            source_ref=row["source_ref"] or "",
            source_level=row["source_level"] or "L2",
            source=source,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            access_count=int(row["access_count"]),
            last_accessed_at=row["last_accessed_at"] or "",
        )

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from nexus.models import FeedbackAction, MemoryStatus, MemoryType
from nexus.store import MemoryStore


class FeedbackLogger:
    def __init__(self, store: MemoryStore) -> None:
        self._store = store

    def log_injection(self, memory_ids: list[str], task_context: str = "") -> None:
        for mid in memory_ids:
            rec = self._store.get(mid)
            if rec is None:
                continue
            rec.touch()
            self._store.update(mid, {
                "access_count": rec.access_count,
                "last_accessed_at": rec.last_accessed_at,
            })

    def log_feedback(self, memory_id: str, action: str, context: str = "") -> None:
        try:
            fb_action = FeedbackAction(action)
        except ValueError:
            return

        if self._store.get(memory_id) is None:
            return

        self._write_feedback_record(memory_id, fb_action.value, context)
        self._update_memory_state(memory_id, fb_action)

    def _write_feedback_record(self, memory_id: str, action: str, context: str) -> None:
        import sqlite3
        fb_id = f"fb_{uuid.uuid4().hex[:20]}"
        now = datetime.now(timezone.utc).isoformat()
        self._store._conn.execute(
            "INSERT INTO feedback_log (id, memory_id, action, task_context, created_at) VALUES (?, ?, ?, ?, ?)",
            (fb_id, memory_id, action, context, now),
        )
        self._store._conn.commit()

    def _update_memory_state(self, memory_id: str, action: FeedbackAction) -> None:
        rec = self._store.get(memory_id)
        if rec is None:
            return

        if action == FeedbackAction.ACCEPTED:
            rec.touch()
            self._store.update(memory_id, {
                "access_count": rec.access_count,
                "last_accessed_at": rec.last_accessed_at,
            })
        elif action == FeedbackAction.IGNORED:
            new_importance = max(rec.importance - 0.1, 0.0)
            self._store.update(memory_id, {"importance": new_importance})
        elif action == FeedbackAction.DELETED:
            self._store.delete(memory_id)
        elif action == FeedbackAction.CORRECTED:
            rec.touch()
            self._store.update(memory_id, {
                "access_count": rec.access_count,
                "last_accessed_at": rec.last_accessed_at,
            })

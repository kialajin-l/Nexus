from __future__ import annotations

from dataclasses import dataclass

from nexus.models import MemoryStatus, MemoryType, ScoredMemory


@dataclass
class InjectorConfig:
    max_tokens: int = 500
    include_metadata: bool = True


_TYPE_LABELS = {
    MemoryType.FACT: "fact",
    MemoryType.DECISION: "decision",
    MemoryType.PREFERENCE: "preference",
    MemoryType.RULE: "rule",
    MemoryType.TODO: "todo",
}


class Injector:
    def __init__(self, config: InjectorConfig | None = None) -> None:
        self._config = config or InjectorConfig()

    def inject(
        self,
        memories: list[ScoredMemory],
        context: str = "",
        max_tokens: int = 0,
        mode: str = "task",
    ) -> str:
        if not memories:
            return ""

        budget = max_tokens or self._config.max_tokens
        sorted_memories = self._select_memories(memories, mode=mode)
        if not sorted_memories:
            return ""

        lines = ["## 相关记忆", ""]
        lines.append("Below are retrieved memories that may help with the current task.")
        lines.append("")
        lines.append(f"Mode: {mode}")
        lines.append("")

        char_budget = budget * 4
        header_chars = sum(len(l) for l in lines)
        remaining = char_budget - header_chars

        count = 0
        for sm in sorted_memories:
            entry = self._format_entry(sm)
            entry_chars = len(entry) + 1
            if remaining - entry_chars < 0:
                break
            lines.append(entry)
            remaining -= entry_chars
            count += 1

        if count == 0:
            return ""

        lines.append("")
        lines.append("---")
        return "\n".join(lines)

    def _select_memories(
        self,
        memories: list[ScoredMemory],
        mode: str,
    ) -> list[ScoredMemory]:
        mode_limits = {"brief": 2, "task": 5, "explore": 8}
        limit = mode_limits.get(mode, 5)
        selected: list[ScoredMemory] = []
        rule_count = 0

        for sm in sorted(memories, key=lambda m: (m.score, m.record.confidence), reverse=True):
            record = sm.record
            if not self._allowed_in_mode(record, mode):
                continue
            if mode == "task" and record.type == MemoryType.RULE:
                if rule_count >= 2:
                    continue
                rule_count += 1
            selected.append(sm)
            if len(selected) >= limit:
                break
        return selected

    @staticmethod
    def _allowed_in_mode(record, mode: str) -> bool:
        if record.status == MemoryStatus.DEPRECATED:
            return False
        if mode == "brief":
            return record.status == MemoryStatus.STABLE and record.source_level == "L1"
        if mode == "task":
            return record.status == MemoryStatus.STABLE and record.source_level in {"L1", "L2"}
        if mode == "explore":
            return record.status in {MemoryStatus.STABLE, MemoryStatus.CANDIDATE}
        return record.status == MemoryStatus.STABLE

    def _format_entry(self, sm: ScoredMemory) -> str:
        rec = sm.record
        if self._config.include_metadata:
            type_label = _TYPE_LABELS.get(rec.type, rec.type.value)
            date_str = rec.created_at[:10] if rec.created_at else ""
            content = rec.summary if rec.summary else rec.content
            return (
                f"{sm.record.id.rsplit('/', 1)[-1]}. [{type_label}] {content} "
                f"({rec.status.value}/{rec.source_level}/{rec.confidence:.1f}, {date_str})"
            )
        content = rec.summary if rec.summary else rec.content
        return f"- {content}"

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from nexus.llm_client import LLMClient, LLMMessage
from nexus.models import ExtractMetadata, MemoryRecord, MemoryStatus, MemoryType, SourceInfo

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).parent / "prompts" / "extract_v1.md"


@dataclass
class ExtractorConfig:
    max_memories_per_call: int = 10
    dedup_enabled: bool = True
    dedup_similarity_threshold: float = 0.85
    extract_retries: int = 1


class Extractor:
    def __init__(
        self,
        llm_client: LLMClient,
        store: Any = None,
        config: ExtractorConfig | None = None,
        prompt: str = "",
    ) -> None:
        self._llm = llm_client
        self._store = store
        self._config = config or ExtractorConfig()
        self._system_prompt = prompt if prompt else self._load_prompt()

    def _load_prompt(self) -> str:
        if _PROMPT_PATH.exists():
            return _PROMPT_PATH.read_text(encoding="utf-8")
        return "Extract structured memories from the following text. Return JSON."

    def extract(self, text: str, metadata: ExtractMetadata) -> list[MemoryRecord]:
        raw_memories = self._call_llm(text)
        records = self._parse_response(raw_memories, metadata)
        if not records and self._config.extract_retries > 0:
            for attempt in range(self._config.extract_retries):
                logger.info("extract returned 0 records, retry %d/%d", attempt + 1, self._config.extract_retries)
                raw_memories = self._call_llm(text)
                records = self._parse_response(raw_memories, metadata)
                if records:
                    break
        if self._config.dedup_enabled and self._store is not None:
            records = self._deduplicate(records)
        return records[: self._config.max_memories_per_call]

    def _call_llm(self, text: str) -> str:
        messages = [
            LLMMessage(role="system", content=self._system_prompt),
            LLMMessage(role="user", content=f"Extract memories from the following text:\n\n{text}"),
        ]
        response = self._llm.chat(messages, temperature=0.2, max_tokens=4096)
        return response.content

    def _parse_response(self, raw: str, metadata: ExtractMetadata) -> list[MemoryRecord]:
        try:
            data = self._extract_json(raw)
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(
                "Failed to parse LLM response as JSON: %s (raw length=%d, preview=%.100s)",
                e, len(raw), raw[:100],
            )
            return []

        memories_raw = data.get("memories", [])
        if not isinstance(memories_raw, list):
            return []

        records = []
        for item in memories_raw:
            if not isinstance(item, dict):
                continue
            record = self._item_to_record(item, metadata)
            if record is not None:
                records.append(record)
        return records

    def _item_to_record(self, item: dict[str, Any], metadata: ExtractMetadata) -> MemoryRecord | None:
        try:
            mem_type = MemoryType(item.get("type", item.get("anchor_type", "fact")))
        except ValueError:
            mem_type = MemoryType.FACT

        raw_content = item.get("content", "")
        if isinstance(raw_content, dict):
            parts = [f"{k}: {v}" for k, v in raw_content.items() if isinstance(v, (str, int, float, bool))]
            raw_content = ", ".join(parts) if parts else json.dumps(raw_content, ensure_ascii=False)
        content = str(raw_content).strip() if raw_content else ""
        if not content:
            return None

        source_kind = item.get("source_kind", metadata.source_type)
        source_ref = item.get("source_ref", metadata.source_ref)
        source_level = item.get("source_level", metadata.source_level)

        raw_importance = item.get("importance", 0.5)
        raw_confidence = item.get("confidence", item.get("importance", 0.5))

        def _safe_float(v: Any, default: float = 0.5) -> float:
            try:
                return float(v)
            except (TypeError, ValueError):
                return default

        return MemoryRecord(
            project=metadata.project,
            topic=item.get("topic", metadata.topic or metadata.project),
            type=mem_type,
            content=content,
            summary=str(item.get("summary", "") or ""),
            tags=item.get("tags", []) if isinstance(item.get("tags"), list) else [],
            importance=_safe_float(raw_importance),
            status=self._default_status(item.get("status"), source_level),
            confidence=_safe_float(raw_confidence),
            source_kind=source_kind,
            source_ref=source_ref,
            source_level=source_level,
            source=SourceInfo(type=source_kind, ref=source_ref),
            session_id=metadata.session_id,
        )

    @staticmethod
    def _default_status(raw_status: Any, source_level: str) -> MemoryStatus:
        if raw_status:
            return MemoryStatus(raw_status)
        if source_level == "L1":
            return MemoryStatus.STABLE
        return MemoryStatus.CANDIDATE

    def _deduplicate(self, records: list[MemoryRecord]) -> list[MemoryRecord]:
        if not self._store or not records:
            return records
        unique = []
        for rec in records:
            keywords = self._extract_keywords(rec.content)
            existing = self._store.search_by_keywords(
                keywords=keywords,
                project=rec.project,
                top_k=3,
            )
            is_dup = False
            for existing_rec, _ in existing:
                if self._text_similarity(rec.content, existing_rec.content) >= self._config.dedup_similarity_threshold:
                    is_dup = True
                    break
            if not is_dup:
                unique.append(rec)
        return unique

    @staticmethod
    def _extract_keywords(text: str, max_keywords: int = 5) -> list[str]:
        import re

        segments = re.findall(r"[\u4e00-\u9fff]+|[a-zA-Z0-9]+", text)
        keywords = []
        for seg in segments:
            if re.match(r"[\u4e00-\u9fff]", seg):
                for i in range(0, len(seg), 2):
                    if len(keywords) >= max_keywords:
                        break
                    keywords.append(seg[i:i + 2])
            else:
                keywords.append(seg.lower())
            if len(keywords) >= max_keywords:
                break
        return keywords

    @staticmethod
    def _text_similarity(a: str, b: str) -> float:
        def _ngrams(text: str, n: int = 3) -> set[str]:
            text = text.lower()
            return {text[i:i + n] for i in range(len(text) - n + 1)}

        set_a = _ngrams(a)
        set_b = _ngrams(b)
        if not set_a or not set_b:
            return 0.0
        intersection = set_a & set_b
        union = set_a | set_b
        return len(intersection) / len(union)

    @staticmethod
    def _extract_json(text: str) -> dict[str, Any]:
        text = text.strip()

        text = re.sub(r"<think[^>]*>.*?</think\s*>", "", text, flags=re.DOTALL)
        text = text.strip()

        if text.startswith("```"):
            lines = text.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines)

        json_marker = '{"memories"'
        marker_pos = text.find(json_marker)
        if marker_pos != -1:
            json_text = text[marker_pos:]
            depth = 0
            in_string = False
            escape_next = False
            for i, ch in enumerate(json_text):
                if escape_next:
                    escape_next = False
                    continue
                if ch == "\\":
                    escape_next = True
                    continue
                if ch == '"' and not escape_next:
                    in_string = not in_string
                    continue
                if in_string:
                    continue
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        candidate = json_text[: i + 1]
                        try:
                            return json.loads(candidate)
                        except json.JSONDecodeError:
                            cleaned = Extractor._repair_trailing_commas(candidate)
                            if cleaned is not None:
                                return cleaned
                            break

        start = text.find("{")
        end = text.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError("No JSON object found in response")
        candidate = text[start:end]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            cleaned = Extractor._repair_trailing_commas(candidate)
            if cleaned is not None:
                return cleaned
            raise

    @staticmethod
    def _repair_trailing_commas(text: str) -> dict[str, Any] | None:
        repaired = re.sub(r",\s*([}\]])", r"\1", text)
        try:
            return json.loads(repaired)
        except (json.JSONDecodeError, ValueError):
            pass

        open_brackets = repaired.count("[") - repaired.count("]")
        open_braces = repaired.count("{") - repaired.count("}")
        if open_brackets > 0 or open_braces > 0:
            repaired += "]" * max(0, open_brackets)
            repaired += "}" * max(0, open_braces)
            repaired = re.sub(r",\s*([}\]])", r"\1", repaired)
            try:
                return json.loads(repaired)
            except (json.JSONDecodeError, ValueError):
                pass

        return None

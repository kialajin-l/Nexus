from __future__ import annotations

import json

import pytest

from nexus.exchange import ExchangeError, build_exchange, read_exchange, records_from_exchange, write_exchange
from nexus.models import MemoryRecord, MemoryStatus, MemoryType


def _record(status: MemoryStatus = MemoryStatus.STABLE) -> MemoryRecord:
    return MemoryRecord(
        id="mem_exchange_1",
        project="portable-test",
        type=MemoryType.DECISION,
        content="Commercial import must validate the portable exchange hash.",
        summary="Validate portable exchange hash",
        tags=["portable", "commercial"],
        importance=0.8,
        status=status,
        confidence=0.9,
        source_kind="test",
        source_ref="fixture",
        source_level="L2",
    )


def test_exchange_round_trip_has_canonical_hash(tmp_path) -> None:
    target = tmp_path / "memory.exchange.json"
    written = write_exchange(target, [_record()], source_scope="portable-test")

    loaded = read_exchange(target)
    restored = records_from_exchange(loaded)

    assert loaded == written
    assert loaded["manifest"]["record_count"] == 1
    assert len(loaded["manifest"]["content_sha256"]) == 64
    assert restored[0].id == "mem_exchange_1"
    assert restored[0].tags == ["portable", "commercial"]


def test_exchange_rejects_tampered_content(tmp_path) -> None:
    target = tmp_path / "memory.exchange.json"
    write_exchange(target, [_record()], source_scope="portable-test")
    payload = json.loads(target.read_text(encoding="utf-8"))
    payload["records"][0]["content"] = "tampered"
    target.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ExchangeError, match="hash"):
        read_exchange(target)


def test_exchange_rejects_deprecated_and_sensitive_metadata() -> None:
    with pytest.raises(ExchangeError, match="candidate and stable"):
        build_exchange([_record(MemoryStatus.DEPRECATED)], source_scope="portable-test")

    payload = build_exchange([_record()], source_scope="portable-test")
    payload["records"][0]["authorization_ledger"] = "must-not-be-exported"
    with pytest.raises(ExchangeError, match="unsupported or missing"):
        read_exchange_payload(payload)


def read_exchange_payload(payload: dict) -> dict:
    from nexus.exchange import validate_exchange

    return validate_exchange(payload)

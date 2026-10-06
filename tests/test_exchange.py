from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import validate as validate_json_schema

from nexus import exchange
from nexus.exchange import ExchangeError, build_exchange, read_exchange, records_from_exchange, write_exchange
from nexus.models import MemoryRecord, MemoryStatus, MemoryType


def _record(
    status: MemoryStatus = MemoryStatus.STABLE,
    content: str = "Commercial import must validate the portable exchange hash.",
) -> MemoryRecord:
    return MemoryRecord(
        id="mem_exchange_1",
        project="portable-test",
        type=MemoryType.DECISION,
        content=content,
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


def test_exchange_matches_public_json_schema() -> None:
    schema_path = Path(__file__).resolve().parents[1] / "docs" / "schemas" / "NEXUS_PORTABLE_MEMORY_EXCHANGE_V1.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    validate_json_schema(build_exchange([_record()], source_scope="portable-test"), schema)


def test_exchange_rejects_tampered_content(tmp_path) -> None:
    target = tmp_path / "memory.exchange.json"
    write_exchange(target, [_record()], source_scope="portable-test")
    payload = json.loads(target.read_text(encoding="utf-8"))
    payload["records"][0]["content"] = "tampered"
    target.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ExchangeError, match="hash"):
        read_exchange(target)


def test_exchange_writer_rejects_oversized_package_without_creating_files(tmp_path, monkeypatch) -> None:
    target = tmp_path / "not-created" / "memory.exchange.json"
    monkeypatch.setattr(exchange, "MAX_EXCHANGE_BYTES", 64)

    with pytest.raises(ExchangeError, match="too large"):
        write_exchange(target, [_record()], source_scope="portable-test")

    assert not target.exists()
    assert not target.parent.exists()


@pytest.mark.parametrize(
    "sensitive_text",
    [
        "api" + "_key=" + "synthetic-value-123456",
        "Bearer " + "x" * 24,
        "-----BEGIN PRIVATE KEY-----",
        "g" + "hp_" + "x" * 24,
    ],
)
def test_exchange_rejects_credential_like_record_text_without_echoing_it(sensitive_text: str) -> None:
    with pytest.raises(ExchangeError, match="restricted text") as error:
        build_exchange([_record(content=f"selected memory: {sensitive_text}")], source_scope="portable-test")

    assert sensitive_text not in str(error.value)


def test_exchange_rejects_sensitive_source_scope_without_echoing_it() -> None:
    sensitive_text = "api_key=supersecretvalue123"
    with pytest.raises(ExchangeError, match="source_scope contains restricted text") as error:
        build_exchange([_record()], source_scope=sensitive_text)

    assert sensitive_text not in str(error.value)


def test_exchange_allows_non_credential_security_discussion() -> None:
    payload = build_exchange(
        [_record(content="Rotate the API key after moving the service to a new host.")],
        source_scope="portable-test",
    )

    assert payload["manifest"]["record_count"] == 1


@pytest.mark.parametrize(
    "restricted_path",
    [
        "C:" + r"\Users\synthetic\.nexus\nexus.db",
        "/home/synthetic/.nexus/nexus.sqlite3",
    ],
)
def test_exchange_rejects_database_path_in_source_reference(restricted_path: str) -> None:
    record = _record()
    record.source_ref = restricted_path

    with pytest.raises(ExchangeError, match="restricted text") as error:
        build_exchange([record], source_scope="portable-test")

    assert restricted_path not in str(error.value)


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

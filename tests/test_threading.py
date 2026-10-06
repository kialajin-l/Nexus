from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from nexus.feedback import FeedbackLogger
from nexus.memory_filter import MemoryFilter
from nexus.models import MemoryRecord, MemoryStatus, MemoryType, SourceInfo
from nexus.store import MemoryStore


def _record(content: str, memory_type: MemoryType = MemoryType.FACT) -> MemoryRecord:
    return MemoryRecord(
        id=f"mem_{abs(hash(content))}",
        project="thread-test",
        session_id="session",
        topic="thread-test",
        type=memory_type,
        content=content,
        summary="",
        tags=[],
        importance=0.8,
        status=MemoryStatus.STABLE,
        confidence=0.8,
        source_kind="test",
        source_ref="test",
        source_level="L2",
        source=SourceInfo(type="test", ref="test"),
    )


def test_memory_store_can_be_used_across_worker_threads(tmp_path) -> None:
    store = MemoryStore(str(tmp_path / "thread-safe.db"))
    try:
        store.save(_record("thread-safe sqlite memory"))

        def query_count() -> int:
            return store.count(project="thread-test")

        with ThreadPoolExecutor(max_workers=1) as executor:
            assert executor.submit(query_count).result(timeout=5) == 1
    finally:
        store.close()


def test_feedback_and_filter_can_use_store_across_worker_threads(tmp_path) -> None:
    store = MemoryStore(str(tmp_path / "feedback-thread-safe.db"))
    try:
        record = _record(
            "Thread safe decision memory has enough concrete content for injection checks",
            MemoryType.DECISION,
        )
        store.save(record)

        def write_and_read_feedback() -> tuple[int, bool]:
            FeedbackLogger(store).log_feedback(record.id, "accepted", context="worker")
            should_inject = MemoryFilter(store=store).should_inject(
                record,
                task_context="Thread safe decision memory",
                retrieval_score=0.2,
            )
            return store.count_feedback(record.id, "accepted"), should_inject

        with ThreadPoolExecutor(max_workers=1) as executor:
            accepted_count, should_inject = executor.submit(write_and_read_feedback).result(timeout=5)

        assert accepted_count == 1
        assert should_inject is True
    finally:
        store.close()


def test_chinese_overlap_requires_a_stable_bigram() -> None:
    record = _record("项目使用红线策略保存客户数据")

    assert MemoryFilter._compute_task_overlap(record, "项目配置") > 0
    assert MemoryFilter._compute_task_overlap(record, "用户") == 0


def test_generic_chinese_text_is_not_specific_enough_for_fact_injection() -> None:
    record = _record("这是一个项目完成后的普通数据说明文本", MemoryType.FACT)

    assert MemoryFilter().should_inject(record) is False

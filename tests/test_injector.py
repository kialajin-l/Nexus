from nexus.injector import Injector, InjectorConfig
from nexus.models import MemoryRecord, MemoryStatus, MemoryType, ScoredMemory


def test_injector_keeps_full_content_when_summary_exists():
    record = MemoryRecord(
        project="hermes-pro",
        type=MemoryType.FACT,
        content="NexusOnly隔离召回验证代号是 NXISO-20260606-NEXUSONLY-9137",
        summary="NexusOnly隔离召回验证代号",
        status=MemoryStatus.STABLE,
        source_level="L1",
        confidence=0.9,
    )

    injected = Injector(InjectorConfig()).inject(
        [ScoredMemory(record=record, score=0.9)],
        mode="task",
    )

    assert "NXISO-20260606-NEXUSONLY-9137" in injected
    assert "summary=NexusOnly隔离召回验证代号" in injected

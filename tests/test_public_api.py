from nexus import (
    Config,
    MemoryCoprocessor,
    MemoryRecord,
    MemoryRiskLevel,
    MemoryStatus,
    MemoryType,
    ProjectionConfig,
    ProjectionMode,
    ScoredMemory,
)


def test_stable_public_exports_are_available():
    assert MemoryCoprocessor is not None
    assert Config is not None
    assert MemoryRecord is not None
    assert MemoryType.FACT.value == "fact"
    assert MemoryStatus.STABLE.value == "stable"
    assert ProjectionMode.RELAXED_WRITEBACK.value == "relaxed_writeback"
    assert MemoryRiskLevel.L1_PERSONAL.value == "L1_personal"
    assert ProjectionConfig is not None
    assert ScoredMemory is not None

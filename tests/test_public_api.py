from nexus import Config, MemoryCoprocessor, MemoryRecord, MemoryStatus, MemoryType, ScoredMemory


def test_stable_public_exports_are_available():
    assert MemoryCoprocessor is not None
    assert Config is not None
    assert MemoryRecord is not None
    assert MemoryType.FACT.value == "fact"
    assert MemoryStatus.STABLE.value == "stable"
    assert ScoredMemory is not None

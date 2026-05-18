__version__ = "1.0.0"

from nexus.coprocessor import MemoryCoprocessor
from nexus.config import Config
from nexus.exceptions import (
    ConfigurationError,
    ExtractionError,
    InjectionError,
    NexusError,
    RetrievalError,
    StorageError,
)
from nexus.models import (
    MemoryRiskLevel,
    MemoryRecord,
    MemoryStatus,
    MemoryType,
    ProjectionConfig,
    ProjectionMode,
    ScoredMemory,
)

__all__ = [
    "MemoryCoprocessor",
    "Config",
    "MemoryRecord",
    "MemoryStatus",
    "MemoryType",
    "ProjectionConfig",
    "ProjectionMode",
    "MemoryRiskLevel",
    "ScoredMemory",
    "NexusError",
    "ExtractionError",
    "RetrievalError",
    "InjectionError",
    "StorageError",
    "ConfigurationError",
]

_STABLE_API = [
    "MemoryCoprocessor",
    "Config",
    "MemoryRecord",
    "MemoryStatus",
    "MemoryType",
    "ProjectionConfig",
    "ProjectionMode",
    "MemoryRiskLevel",
    "ScoredMemory",
    "NexusError",
    "ExtractionError",
    "RetrievalError",
    "InjectionError",
    "StorageError",
    "ConfigurationError",
]

_EXPERIMENTAL_API = [
    "search",
    "list_memories",
]

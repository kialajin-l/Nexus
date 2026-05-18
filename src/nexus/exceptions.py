from __future__ import annotations


class NexusError(Exception):
    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        details: dict | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.details = details or {}


class ExtractionError(NexusError):
    pass


class RetrievalError(NexusError):
    pass


class InjectionError(NexusError):
    pass


class StorageError(NexusError):
    pass


class ConfigurationError(NexusError):
    pass

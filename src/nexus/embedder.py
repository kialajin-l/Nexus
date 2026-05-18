from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import numpy as np


class Embedder(ABC):
    @abstractmethod
    def embed(self, text: str) -> list[float]:
        ...

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(t) for t in texts]

    @property
    @abstractmethod
    def dimension(self) -> int:
        ...


class OllamaEmbedder(Embedder):
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "") -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._dimension = 768
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import ollama
            except ImportError:
                raise ImportError("ollama package not installed. Install with: pip install ollama")
            self._client = ollama.Client(host=self._base_url)
        return self._client

    def embed(self, text: str) -> list[float]:
        client = self._get_client()
        if not self._model:
            raise ValueError("Ollama embedding model is required. Pass it from the host or explicit config.")
        response = client.embed(model=self._model, input=text)
        return list(response.embeddings[0])

    @property
    def dimension(self) -> int:
        return self._dimension


class OpenAIEmbedder(Embedder):
    def __init__(
        self,
        base_url: str = "https://api.openai.com/v1",
        api_key: str = "",
        model: str = "text-embedding-3-small",
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._dimension = 1536

    def embed(self, text: str) -> list[float]:
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("openai package not installed. Install with: pip install openai")

        client = OpenAI(base_url=self._base_url, api_key=self._api_key)
        response = client.embeddings.create(model=self._model, input=text)
        return response.data[0].embedding

    @property
    def dimension(self) -> int:
        return self._dimension


class MockEmbedder(Embedder):
    def __init__(self, dim: int = 8) -> None:
        self._dim = dim
        self._rng = np.random.default_rng(42)

    def embed(self, text: str) -> list[float]:
        vec = self._rng.standard_normal(self._dim).astype(np.float32)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    @property
    def dimension(self) -> int:
        return self._dim

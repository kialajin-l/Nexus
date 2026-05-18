from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class LLMMessage:
    role: str
    content: str


@dataclass
class LLMResponse:
    content: str
    model: str = ""
    usage: dict[str, int] = field(default_factory=dict)


class LLMClient(ABC):
    @abstractmethod
    def chat(
        self,
        messages: list[LLMMessage],
        model: str = "",
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> LLMResponse:
        ...

    def simple_chat(
        self,
        prompt: str,
        system: str = "",
        model: str = "",
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> LLMResponse:
        messages = []
        if system:
            messages.append(LLMMessage(role="system", content=system))
        messages.append(LLMMessage(role="user", content=prompt))
        return self.chat(messages, model=model, temperature=temperature, max_tokens=max_tokens)


class OllamaClient(LLMClient):
    def __init__(self, base_url: str = "http://localhost:11434", default_model: str = "") -> None:
        self._base_url = base_url.rstrip("/")
        self._default_model = default_model
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import ollama
            except ImportError:
                raise ImportError("ollama package not installed. Install with: pip install ollama")
            self._client = ollama.Client(host=self._base_url)
        return self._client

    def chat(
        self,
        messages: list[LLMMessage],
        model: str = "",
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> LLMResponse:
        client = self._get_client()
        model = model or self._default_model
        if not model:
            raise ValueError("Ollama model is required. Pass it from the host or explicit config.")
        msg_dicts = [{"role": m.role, "content": m.content} for m in messages]

        response = client.chat(
            model=model,
            messages=msg_dicts,
            options={"temperature": temperature, "num_predict": max_tokens},
        )

        content = response.message.content or ""
        if not content:
            thinking = getattr(response.message, "thinking", None) or ""
            if thinking:
                content = thinking
        return LLMResponse(
            content=content,
            model=model,
            usage={
                "prompt_tokens": response.prompt_eval_count or 0,
                "completion_tokens": response.eval_count or 0,
            },
        )


class OpenAIClient(LLMClient):
    def __init__(
        self,
        base_url: str = "https://api.openai.com/v1",
        api_key: str = "",
        default_model: str = "gpt-4o-mini",
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._default_model = default_model

    def chat(
        self,
        messages: list[LLMMessage],
        model: str = "",
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> LLMResponse:
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("openai package not installed. Install with: pip install openai")

        model = model or self._default_model
        client = OpenAI(base_url=self._base_url, api_key=self._api_key)
        msg_dicts = [{"role": m.role, "content": m.content} for m in messages]

        response = client.chat.completions.create(
            model=model,
            messages=msg_dicts,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        content = response.choices[0].message.content or ""
        return LLMResponse(
            content=content,
            model=model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            },
        )


class MockLLMClient(LLMClient):
    def __init__(self, responses: list[str] | None = None) -> None:
        self._responses = responses or []
        self._call_count = 0
        self.call_log: list[list[LLMMessage]] = []

    def chat(
        self,
        messages: list[LLMMessage],
        model: str = "",
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> LLMResponse:
        self.call_log.append(messages)
        idx = min(self._call_count, len(self._responses) - 1) if self._responses else 0
        content = self._responses[idx] if self._responses else '{"memories": []}'
        self._call_count += 1
        return LLMResponse(content=content, model="mock")

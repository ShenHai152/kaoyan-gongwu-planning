"""LLMProvider protocol, request/completion shapes, and explicit resolution.

Resolution is an explicit `resolve(request)` step, never a hidden default inside
`run()` (architecture.md: Explicit beats implicit). A missing key means "no
provider" (`LLMUnavailable`), not a crash: the caller decides whether to fall
back to a template.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


class LLMUnavailable(RuntimeError):
    """Raised when no provider is configured or a provider call fails."""


@dataclass(frozen=True)
class LLMRequest:
    system: str
    user: str
    json_output: bool = False
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Completion:
    text: str
    model: str
    usage: dict[str, int] = field(default_factory=dict)


@runtime_checkable
class LLMProvider(Protocol):
    name: str

    def complete(self, request: LLMRequest) -> Completion: ...


class FakeProvider:
    """Deterministic provider for tests: no network, no credentials."""

    name = "fake"

    def __init__(self, text: str = "fake-completion") -> None:
        self._text = text
        self.requests: list[LLMRequest] = []

    def complete(self, request: LLMRequest) -> Completion:
        self.requests.append(request)
        return Completion(text=self._text, model="fake", usage={"total_tokens": 0})


def resolve(request: LLMRequest | None = None) -> LLMProvider:
    """Pick a provider from the environment, or raise `LLMUnavailable`.

    Anthropic wins when `ANTHROPIC_API_KEY` is set; an OpenAI-compatible
    endpoint (`OPENAI_API_KEY`, optional `OPENAI_BASE_URL`) is the fallback.
    """
    if os.environ.get("ANTHROPIC_API_KEY"):
        from app.llm.anthropic import AnthropicProvider

        return AnthropicProvider()
    if os.environ.get("OPENAI_API_KEY"):
        from app.llm.openai_compatible import OpenAICompatibleProvider

        return OpenAICompatibleProvider()
    raise LLMUnavailable("no LLM provider configured")

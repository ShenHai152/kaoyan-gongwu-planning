"""LLM adapter domain: the LLMProvider protocol and its implementations.

Adapters translate contracts; they own no state (see this project's engineering rules). Swapping a
provider is a config change, never a change to the caller.
"""

from app.llm.anthropic import AnthropicProvider
from app.llm.openai_compatible import OpenAICompatibleProvider
from app.llm.provider import (
    Completion,
    FakeProvider,
    LLMProvider,
    LLMRequest,
    LLMUnavailable,
    resolve,
)

__all__ = [
    "AnthropicProvider",
    "Completion",
    "FakeProvider",
    "LLMProvider",
    "LLMRequest",
    "LLMUnavailable",
    "OpenAICompatibleProvider",
    "resolve",
]

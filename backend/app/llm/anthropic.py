"""Anthropic implementation of the LLMProvider protocol (adapter, no state)."""

from __future__ import annotations

import os

from app.llm.provider import Completion, LLMRequest, LLMUnavailable

_DEFAULT_MODEL = "claude-sonnet-4-20250514"
_DEFAULT_BASE_URL = "https://api.anthropic.com/v1/messages"


class AnthropicProvider:
    name = "anthropic"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise LLMUnavailable("ANTHROPIC_API_KEY is not set")
        self.model = model or os.environ.get("ANTHROPIC_MODEL", _DEFAULT_MODEL)
        self.base_url = str(
            base_url or os.environ.get("ANTHROPIC_BASE_URL") or _DEFAULT_BASE_URL
        )

    def _payload(self, request: LLMRequest) -> dict:
        return {
            "model": self.model,
            "max_tokens": 2048,
            "system": request.system,
            "messages": [{"role": "user", "content": request.user}],
        }

    def complete(self, request: LLMRequest) -> Completion:
        import httpx

        try:
            response = httpx.post(
                self.base_url,
                headers={
                    "x-api-key": str(self.api_key),
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json=self._payload(request),
                timeout=60.0,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:  # pragma: no cover - network path
            raise LLMUnavailable(str(exc)) from exc
        data = response.json()
        text = "".join(
            block.get("text", "") for block in data.get("content", []) if block.get("type") == "text"
        )
        usage = data.get("usage", {})
        return Completion(text=text, model=data.get("model", self.model), usage=usage)

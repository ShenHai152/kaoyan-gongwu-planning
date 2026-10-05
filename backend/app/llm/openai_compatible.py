"""OpenAI-compatible provider (DeepSeek, Tongyi, ...): adapter, no state."""

from __future__ import annotations

import os

from app.llm.provider import Completion, LLMRequest, LLMUnavailable

_DEFAULT_MODEL = "gpt-4o-mini"
_DEFAULT_BASE_URL = "https://api.openai.com/v1"


class OpenAICompatibleProvider:
    name = "openai-compatible"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise LLMUnavailable("OPENAI_API_KEY is not set")
        self.model = model or os.environ.get("OPENAI_MODEL", _DEFAULT_MODEL)
        self.base_url = (base_url or os.environ.get("OPENAI_BASE_URL", _DEFAULT_BASE_URL)).rstrip("/")

    def _payload(self, request: LLMRequest) -> dict:
        payload: dict = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": request.system},
                {"role": "user", "content": request.user},
            ],
        }
        if request.json_output:
            payload["response_format"] = {"type": "json_object"}
        return payload

    def complete(self, request: LLMRequest) -> Completion:
        import httpx

        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "content-type": "application/json",
                },
                json=self._payload(request),
                timeout=60.0,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:  # pragma: no cover - network path
            raise LLMUnavailable(str(exc)) from exc
        data = response.json()
        choices = data.get("choices", [])
        text = choices[0]["message"]["content"] if choices else ""
        usage = data.get("usage", {})
        return Completion(text=text, model=data.get("model", self.model), usage=usage)

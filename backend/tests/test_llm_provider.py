
import pytest

from app.llm import FakeProvider, LLMRequest, LLMUnavailable, resolve
from app.llm.anthropic import AnthropicProvider
from app.llm.openai_compatible import OpenAICompatibleProvider


def test_fake_provider_is_deterministic():
    provider = FakeProvider(text="hello")
    completion = provider.complete(LLMRequest(system="s", user="u"))
    assert completion.text == "hello"
    assert completion.model == "fake"
    assert provider.requests[0].user == "u"


def test_resolve_without_keys_is_unavailable(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(LLMUnavailable):
        resolve()


def test_resolve_prefers_anthropic(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "a-key")
    monkeypatch.setenv("OPENAI_API_KEY", "o-key")
    provider = resolve()
    assert provider.name == "anthropic"


def test_resolve_openai_when_only_openai(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "o-key")
    provider = resolve()
    assert provider.name == "openai-compatible"


def test_providers_require_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(LLMUnavailable):
        AnthropicProvider()
    with pytest.raises(LLMUnavailable):
        OpenAICompatibleProvider()


def test_payload_shapes():
    anthropic = AnthropicProvider(api_key="k", model="m", base_url="http://x")
    payload = anthropic._payload(LLMRequest(system="s", user="u"))
    assert payload["model"] == "m"
    assert payload["messages"][0]["content"] == "u"

    oai = OpenAICompatibleProvider(api_key="k", model="m", base_url="http://x")
    payload = oai._payload(LLMRequest(system="s", user="u", json_output=True))
    assert payload["response_format"] == {"type": "json_object"}

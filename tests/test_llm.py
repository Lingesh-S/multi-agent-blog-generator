"""Tests for the LLM provider wrappers."""

from types import SimpleNamespace

import pytest

from src.tools.llm import LLMProvider, OllamaProvider, OpenAIProvider


class FakeChatModel:
    instances = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.prompts = []
        self.calls = []
        FakeChatModel.instances.append(self)

    def invoke(self, prompt):
        self.prompts.append(prompt)
        self.calls.append(dict(vars(self)))
        return SimpleNamespace(content=f"reply to {prompt}")


@pytest.fixture
def fake_models(monkeypatch):
    FakeChatModel.instances = []
    monkeypatch.setattr("langchain_ollama.ChatOllama", FakeChatModel)
    monkeypatch.setattr("langchain_openai.ChatOpenAI", FakeChatModel)
    return FakeChatModel.instances


def test_llm_provider_builds_ollama_with_default_base_url(fake_models):
    llm = LLMProvider({"provider": "ollama", "model": "llama3"})

    assert isinstance(llm.provider, OllamaProvider)
    assert fake_models[0].kwargs == {
        "model": "llama3",
        "base_url": "http://localhost:11434",
    }
    assert llm.default_temperature == 0.7
    assert llm.default_max_tokens == 2000


def test_llm_provider_builds_openai_with_api_key(fake_models):
    llm = LLMProvider({"provider": "openai", "model": "gpt-4o", "api_key": "sk-test"})

    assert isinstance(llm.provider, OpenAIProvider)
    assert fake_models[0].kwargs == {"model": "gpt-4o", "api_key": "sk-test"}


def test_llm_provider_requires_openai_api_key(fake_models):
    with pytest.raises(ValueError, match="API key"):
        LLMProvider({"provider": "openai", "model": "gpt-4o"})

    assert fake_models == []


def test_llm_provider_rejects_unknown_provider(fake_models):
    with pytest.raises(ValueError, match="Unknown LLM provider"):
        LLMProvider({"provider": "mystery", "model": "x"})


def test_generate_uses_config_defaults(fake_models):
    llm = LLMProvider({
        "provider": "openai",
        "model": "gpt-4o",
        "api_key": "sk-test",
        "temperature": 0.2,
        "max_tokens": 300,
    })

    assert llm.generate("hello") == "reply to hello"

    call = fake_models[0].calls[0]
    assert call["temperature"] == 0.2
    assert call["max_tokens"] == 300


def test_generate_overrides_defaults_per_call(fake_models):
    llm = LLMProvider({"provider": "openai", "model": "gpt-4o", "api_key": "sk-test"})

    llm.generate("hello", temperature=0.0, max_tokens=50)

    call = fake_models[0].calls[0]
    assert call["temperature"] == 0.0
    assert call["max_tokens"] == 50


def test_generate_reraises_provider_errors(fake_models):
    llm = LLMProvider({"provider": "ollama", "model": "llama3"})

    def broken_invoke(prompt):
        raise ConnectionError("ollama is not running")

    fake_models[0].invoke = broken_invoke

    with pytest.raises(ConnectionError):
        llm.generate("hello")


def test_ollama_generate_applies_max_tokens(fake_models):
    llm = LLMProvider({"provider": "ollama", "model": "llama3", "max_tokens": 400})

    llm.generate("hello")
    llm.generate("hello again", temperature=0.1, max_tokens=80)

    first, second = fake_models[0].calls
    assert first["num_predict"] == 400
    assert second["num_predict"] == 80
    assert second["temperature"] == 0.1

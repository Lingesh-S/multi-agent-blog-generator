"""Tests for settings validation and configuration helpers."""

import pytest
from pydantic import ValidationError

from src.config import settings as settings_module
from src.config.settings import Settings


def make_settings(**overrides):
    return Settings(_env_file=None, **overrides)


@pytest.fixture
def use_settings(monkeypatch):
    def apply(**overrides):
        configured = make_settings(**overrides)
        monkeypatch.setattr(settings_module, "get_settings", lambda: configured)
        return configured

    return apply


def test_defaults_are_valid():
    configured = make_settings()

    assert configured.llm_provider == "ollama"
    assert configured.search_provider == "duckduckgo"
    assert configured.validate_api_keys() == []


@pytest.mark.parametrize(
    "field, value",
    [
        ("llm_provider", "anthropic"),
        ("search_provider", "bing"),
        ("environment", "qa"),
        ("log_level", "verbose"),
    ],
)
def test_unknown_choices_are_rejected(field, value):
    with pytest.raises(ValidationError):
        make_settings(**{field: value})


def test_log_level_is_uppercased():
    assert make_settings(log_level="debug").log_level == "DEBUG"


def test_missing_api_keys_are_reported():
    configured = make_settings(llm_provider="openai", search_provider="tavily")

    assert configured.validate_api_keys() == ["OPENAI_API_KEY", "TAVILY_API_KEY"]


def test_serper_key_is_required_for_serper():
    assert make_settings(search_provider="serper").validate_api_keys() == ["SERPER_API_KEY"]
    assert make_settings(search_provider="serper", serper_api_key="key").validate_api_keys() == []


def test_validate_configuration_reports_missing_keys(use_settings):
    use_settings(llm_provider="openai")

    assert settings_module.validate_configuration() == (
        False,
        "Missing required API keys: OPENAI_API_KEY",
    )


def test_validate_configuration_creates_log_directory(use_settings, tmp_path):
    log_dir = tmp_path / "logs"
    use_settings(log_file=str(log_dir / "app.log"))

    assert settings_module.validate_configuration() == (True, None)
    assert log_dir.is_dir()


def test_config_helpers_expose_provider_settings(use_settings):
    use_settings(
        llm_provider="openai",
        llm_model="gpt-4o-mini",
        openai_api_key="key",
        search_provider="serper",
        search_max_results=3,
    )

    llm_config = settings_module.get_llm_config()
    search_config = settings_module.get_search_config()

    assert llm_config["provider"] == "openai"
    assert llm_config["model"] == "gpt-4o-mini"
    assert llm_config["api_key"] == "key"
    assert search_config["provider"] == "serper"
    assert search_config["max_results"] == 3


def test_choices_ignore_case_and_whitespace():
    configured = make_settings(
        llm_provider=" OpenAI ", search_provider="DuckDuckGo", environment="Production"
    )

    assert configured.llm_provider == "openai"
    assert configured.search_provider == "duckduckgo"
    assert configured.environment == "production"

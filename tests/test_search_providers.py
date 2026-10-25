"""Tests for the individual search providers."""

import pytest
import requests

from src.tools import search as search_module
from src.tools.search import DuckDuckGoSearch, SearchTool, SerperSearch, TavilySearch


class FakeDDGS:
    instances = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        FakeDDGS.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def text(self, query, max_results):
        return [
            {"title": "First", "href": "https://example.com/1", "body": "One"},
            {"title": "Second", "href": "https://example.com/2"},
        ][:max_results]


def test_duckduckgo_passes_timeout_and_maps_results(monkeypatch):
    FakeDDGS.instances = []
    monkeypatch.setattr(search_module, "DDGS", FakeDDGS)

    results = DuckDuckGoSearch(timeout=3).search("topic", max_results=2)

    assert FakeDDGS.instances[0].kwargs == {"timeout": 3}
    assert results == [
        {"title": "First", "link": "https://example.com/1", "snippet": "One"},
        {"title": "Second", "link": "https://example.com/2", "snippet": ""},
    ]


def test_duckduckgo_returns_empty_list_on_error(monkeypatch):
    class BrokenDDGS(FakeDDGS):
        def text(self, query, max_results):
            raise RuntimeError("rate limited")

    monkeypatch.setattr(search_module, "DDGS", BrokenDDGS)

    assert DuckDuckGoSearch().search("topic") == []


class FakeResponse:
    def __init__(self, data, status_error=None):
        self.data = data
        self.status_error = status_error

    def raise_for_status(self):
        if self.status_error:
            raise self.status_error

    def json(self):
        return self.data


def test_serper_sends_key_and_maps_organic_results():
    provider = SerperSearch(api_key="serper-key", timeout=4)
    calls = []

    def post(url, **kwargs):
        calls.append((url, kwargs))
        return FakeResponse({
            "organic": [
                {"title": "A", "link": "https://a.example", "snippet": "a"},
                {"title": "B", "link": "https://b.example", "snippet": "b"},
                {"title": "C", "link": "https://c.example", "snippet": "c"},
            ]
        })

    provider.session.post = post
    results = provider.search("topic", max_results=2)

    url, kwargs = calls[0]
    assert url == "https://google.serper.dev/search"
    assert kwargs["headers"]["X-API-KEY"] == "serper-key"
    assert kwargs["json"] == {"q": "topic", "num": 2}
    assert kwargs["timeout"] == 4
    assert [item["link"] for item in results] == ["https://a.example", "https://b.example"]


def test_serper_returns_empty_list_on_http_error():
    provider = SerperSearch(api_key="bad-key")
    provider.session.post = lambda url, **kwargs: FakeResponse(
        {}, status_error=requests.HTTPError("403 Forbidden")
    )

    assert provider.search("topic") == []


def test_tavily_sends_key_and_maps_results():
    provider = TavilySearch(api_key="tavily-key", timeout=5)
    calls = []

    def post(url, **kwargs):
        calls.append((url, kwargs))
        return FakeResponse({
            "results": [
                {"title": "A", "url": "https://a.example", "content": "Body"},
                {"title": "B"},
            ]
        })

    provider.session.post = post
    results = provider.search("topic", max_results=3)

    url, kwargs = calls[0]
    assert url == "https://api.tavily.com/search"
    assert kwargs["json"]["api_key"] == "tavily-key"
    assert kwargs["json"]["max_results"] == 3
    assert kwargs["timeout"] == 5
    assert results == [
        {"title": "A", "link": "https://a.example", "snippet": "Body"},
        {"title": "B", "link": "", "snippet": ""},
    ]


def test_tavily_returns_empty_list_on_timeout():
    provider = TavilySearch(api_key="tavily-key")

    def post(url, **kwargs):
        raise requests.Timeout("timed out")

    provider.session.post = post

    assert provider.search("topic") == []


def test_search_tool_rejects_missing_key_and_unknown_provider():
    with pytest.raises(ValueError, match="API key"):
        SearchTool(provider="serper")
    with pytest.raises(ValueError, match="API key"):
        SearchTool(provider="tavily")
    with pytest.raises(ValueError, match="Unknown search provider"):
        SearchTool(provider="bing", api_key="key")


def test_search_tool_does_not_cache_empty_results():
    tool = SearchTool(provider="serper", api_key="key", cache_enabled=True, cache_ttl=60, cache_max_size=5)
    calls = []

    def search(query, max_results):
        calls.append(query)
        return []

    tool.provider.search = search
    tool.search("topic")
    tool.search("topic")

    assert calls == ["topic", "topic"]

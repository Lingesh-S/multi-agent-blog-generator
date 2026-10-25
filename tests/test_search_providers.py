"""Tests for the individual search providers."""

import requests

from src.tools import search as search_module
from src.tools.search import DuckDuckGoSearch


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

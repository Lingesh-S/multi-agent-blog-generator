"""Tests for successful search result caching."""

from src.tools.search import SearchTool


def test_search_cache_reuses_results_and_returns_copies():
    tool = SearchTool(
        provider="serper",
        api_key="test-key",
        cache_enabled=True,
        cache_ttl=60,
        cache_max_size=2,
    )
    calls = []

    def search(query, max_results):
        calls.append((query, max_results))
        return [{"title": "Result", "link": "https://example.com", "snippet": "Details"}]

    tool.provider.search = search
    first = tool.search("topic")
    first[0]["title"] = "Changed by caller"
    second = tool.search("topic")

    assert len(calls) == 1
    assert second[0]["title"] == "Result"


def test_search_cache_evicts_least_recently_used_entry():
    tool = SearchTool(
        provider="serper",
        api_key="test-key",
        cache_enabled=True,
        cache_ttl=60,
        cache_max_size=1,
    )
    calls = []

    def search(query, max_results):
        calls.append(query)
        return [{"title": query}]

    tool.provider.search = search
    tool.search("first")
    tool.search("second")
    tool.search("first")

    assert calls == ["first", "second", "first"]

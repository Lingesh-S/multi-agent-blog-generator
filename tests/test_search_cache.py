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


def test_search_cache_ignores_case_and_extra_whitespace():
    tool = SearchTool(
        provider="serper",
        api_key="test-key",
        cache_enabled=True,
        cache_ttl=60,
        cache_max_size=2,
    )
    calls = []

    def search(query, max_results):
        calls.append(query)
        return [{"title": query}]

    tool.provider.search = search
    tool.search("Community Solar")
    tool.search("  community   solar ")

    assert calls == ["Community Solar"]


def test_search_cache_expires_entries_after_ttl(monkeypatch):
    import src.tools.search as search_module

    clock = [100.0]
    monkeypatch.setattr(search_module, "monotonic", lambda: clock[0])
    tool = SearchTool(
        provider="serper",
        api_key="test-key",
        cache_enabled=True,
        cache_ttl=60,
        cache_max_size=2,
    )
    calls = []

    def search(query, max_results):
        calls.append(query)
        return [{"title": query}]

    tool.provider.search = search
    tool.search("topic")
    clock[0] = 159.0
    tool.search("topic")
    clock[0] = 160.0
    tool.search("topic")

    assert calls == ["topic", "topic"]


def test_search_cache_skips_empty_results():
    tool = SearchTool(
        provider="serper",
        api_key="test-key",
        cache_enabled=True,
        cache_ttl=60,
        cache_max_size=2,
    )
    calls = []

    def search(query, max_results):
        calls.append(query)
        return []

    tool.provider.search = search
    tool.search("topic")
    tool.search("topic")

    assert calls == ["topic", "topic"]

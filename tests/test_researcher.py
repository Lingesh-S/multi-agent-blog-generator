"""Tests for the researcher agent."""

import pytest

from src.agents import researcher
from src.agents.researcher import ResearcherAgent
from src.state.schema import AgentStatus, ResearchQuality


class FakeSearchTool:
    def __init__(self, responses):
        self.responses = list(responses)
        self.queries = []

    def search(self, query):
        self.queries.append(query)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    sleeps = []
    monkeypatch.setattr(researcher.time, "sleep", sleeps.append)
    return sleeps


def make_agent(responses):
    agent = ResearcherAgent()
    agent.search_tool = FakeSearchTool(responses)
    agent.max_retries = 3
    return agent


def make_results(count, snippet_words=60):
    return [
        {
            "title": f"Title {i}",
            "link": f"https://example.com/{i}",
            "snippet": " ".join(["fact"] * snippet_words),
        }
        for i in range(count)
    ]


def test_researcher_returns_data_sources_and_quality():
    agent = make_agent([make_results(4)])

    result = agent({"topic": "AI agents", "user_requirements": "for beginners"})

    assert result["agent_status"]["Researcher"] == AgentStatus.COMPLETED
    assert result["research_quality"] == ResearchQuality.HIGH
    assert len(result["research_data"]) == 4
    assert result["research_data"][0].startswith("[Source 1] Title 0\n")
    assert result["research_sources"][1] == {
        "url": "https://example.com/1",
        "title": "Title 1",
        "snippet": " ".join(["fact"] * 60),
    }
    query = agent.search_tool.queries[0]
    assert "AI agents" in query
    assert "for beginners" in query


def test_researcher_fails_without_topic():
    agent = make_agent([])

    result = agent({})

    assert result["agent_status"]["Researcher"] == AgentStatus.FAILED
    assert "Missing required field: topic" in result["error_log"][0]["error"]
    assert agent.search_tool.queries == []


def test_researcher_retries_after_search_errors(no_sleep):
    agent = make_agent([RuntimeError("boom"), RuntimeError("boom"), make_results(2, 30)])

    result = agent({"topic": "AI"})

    assert len(agent.search_tool.queries) == 3
    assert no_sleep == [1, 2]
    assert result["research_quality"] == ResearchQuality.LOW
    assert len(result["research_sources"]) == 2


def test_researcher_falls_back_when_all_searches_fail(no_sleep):
    agent = make_agent([RuntimeError("down")] * 3)

    result = agent({"topic": "AI"})

    assert result["agent_status"]["Researcher"] == AgentStatus.COMPLETED
    assert result["research_quality"] == ResearchQuality.LOW
    assert result["research_sources"] == []
    assert result["research_data"][0].startswith("No research data available")
    assert no_sleep == [1, 2]


@pytest.mark.parametrize(
    "count, words, expected",
    [
        (4, 60, ResearchQuality.HIGH),
        (2, 60, ResearchQuality.MEDIUM),
        (1, 200, ResearchQuality.LOW),
        (4, 5, ResearchQuality.LOW),
    ],
)
def test_assess_quality_thresholds(count, words, expected):
    agent = make_agent([])
    results = make_results(count, words)

    quality = agent._assess_quality(agent._extract_information(results), results)

    assert quality == expected


def test_researcher_falls_back_when_results_have_no_snippets():
    results = [{"title": "Empty", "link": "https://example.com", "snippet": ""}]
    agent = make_agent([results])

    result = agent({"topic": "AI"})

    assert result["research_data"][0].startswith("No research data available")
    assert result["research_sources"][0]["url"] == "https://example.com"

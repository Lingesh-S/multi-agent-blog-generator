"""Tests for the workflow orchestrators with stubbed agents."""

from types import SimpleNamespace

import pytest

from src.agents import orchestrator
from src.agents.orchestrator import (
    IterativeOrchestrator,
    MultiAgentOrchestrator,
    WorkflowExecutionError,
)
from src.state.schema import AgentStatus


class FakeAgent:
    def __init__(self, name, update=None, status=AgentStatus.COMPLETED):
        self.name = name
        self.update = update or {}
        self.status = status
        self.calls = 0

    def __call__(self, state):
        self.calls += 1
        update = self.update(state) if callable(self.update) else dict(self.update)
        update["agent_status"] = {**state.get("agent_status", {}), self.name: self.status}
        update["execution_time"] = {**state.get("execution_time", {}), self.name: 0.5}
        return update


@pytest.fixture
def agents(monkeypatch):
    fakes = {
        "researcher": FakeAgent("Researcher", {"research_data": ["fact"]}),
        "writer": FakeAgent(
            "Writer",
            lambda state: {
                "blog_post": "A finished post.",
                "blog_title": "Title",
                "draft_iterations": state.get("draft_iterations", 0) + 1,
            },
        ),
        "editor": FakeAgent("Editor", {"quality_score": 0.9, "needs_revision": False}),
    }
    monkeypatch.setattr(orchestrator, "ResearcherAgent", lambda config=None: fakes["researcher"])
    monkeypatch.setattr(orchestrator, "WriterAgent", lambda config=None: fakes["writer"])
    monkeypatch.setattr(orchestrator, "EditorAgent", lambda config=None: fakes["editor"])
    use_settings(monkeypatch, editor_enabled=True)
    return fakes


def use_settings(monkeypatch, editor_enabled):
    monkeypatch.setattr(
        orchestrator, "get_settings", lambda: SimpleNamespace(editor_enabled=editor_enabled)
    )


def test_run_executes_all_agents_in_order(agents):
    result = MultiAgentOrchestrator().run(topic="Community solar")

    assert result["blog_post"] == "A finished post."
    assert result["quality_score"] == 0.9
    assert [agents[name].calls for name in ("researcher", "writer", "editor")] == [1, 1, 1]


def test_run_skips_editor_when_disabled(agents, monkeypatch):
    use_settings(monkeypatch, editor_enabled=False)

    flow = MultiAgentOrchestrator()
    result = flow.run(topic="Community solar")

    assert flow.editor is None
    assert agents["editor"].calls == 0
    assert result["quality_score"] is None


def test_run_rejects_invalid_topic(agents):
    with pytest.raises(ValueError):
        MultiAgentOrchestrator().run(topic="AI")

    assert agents["researcher"].calls == 0


def test_run_raises_when_an_agent_fails(agents):
    agents["writer"].status = AgentStatus.FAILED

    with pytest.raises(WorkflowExecutionError, match="Writer"):
        MultiAgentOrchestrator().run(topic="Community solar")


def test_run_raises_when_no_post_is_written(agents):
    agents["writer"].update = {}

    with pytest.raises(WorkflowExecutionError, match="workflow"):
        MultiAgentOrchestrator().run(topic="Community solar")


def test_run_from_state_validates_state(agents):
    with pytest.raises(ValueError):
        MultiAgentOrchestrator().run_from_state({})


def test_iterative_orchestrator_revises_until_quality_is_met(agents):
    scores = iter([0.5, 0.85])
    agents["editor"].update = lambda state: {
        "quality_score": next(scores),
        "needs_revision": True,
    }

    result = IterativeOrchestrator(max_iterations=3).run(topic="Community solar")

    assert agents["writer"].calls == 2
    assert result["draft_iterations"] == 2
    assert result["quality_score"] == 0.85


def test_iterative_orchestrator_stops_at_max_iterations(agents):
    agents["editor"].update = {"quality_score": 0.4, "needs_revision": True}

    IterativeOrchestrator(max_iterations=2).run(topic="Community solar")

    assert agents["writer"].calls == 2
    assert agents["editor"].calls == 2


def test_iterative_orchestrator_stops_when_editor_gives_no_score(agents):
    agents["editor"].update = {"quality_score": None, "needs_revision": True}

    result = IterativeOrchestrator(max_iterations=3).run(topic="Community solar")

    assert agents["writer"].calls == 1
    assert result["blog_post"] == "A finished post."

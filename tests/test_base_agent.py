"""Tests for the shared agent base classes."""

from src.agents.base import BaseAgent, ConditionalAgent
from src.state.schema import AgentStatus


class EchoAgent(BaseAgent):
    def __init__(self, config=None):
        super().__init__(name="Echo", config=config)

    def execute(self, state):
        return {"blog_post": state["topic"].upper()}


class BrokenAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Broken")

    def execute(self, state):
        raise RuntimeError("provider unavailable")


class OptionalAgent(ConditionalAgent):
    def __init__(self):
        super().__init__(name="Optional")
        self.calls = 0

    def should_execute(self, state):
        return bool(state.get("needs_revision"))

    def execute(self, state):
        self.calls += 1
        return {"blog_post": "revised"}


def test_successful_run_adds_status_and_timing():
    agent = EchoAgent()
    state = {
        "topic": "solar",
        "agent_status": {"Researcher": AgentStatus.COMPLETED},
        "execution_time": {"Researcher": 1.5},
    }

    result = agent(state)

    assert result["blog_post"] == "SOLAR"
    assert result["last_modified_by"] == "Echo"
    assert result["agent_status"] == {
        "Researcher": AgentStatus.COMPLETED,
        "Echo": AgentStatus.COMPLETED,
    }
    assert result["execution_time"]["Researcher"] == 1.5
    assert result["execution_time"]["Echo"] >= 0
    assert agent.execution_count == 1


def test_failed_run_is_recorded_without_raising():
    agent = BrokenAgent()
    state = {"topic": "solar", "error_log": [{"agent": "Researcher", "error": "earlier"}]}

    result = agent(state)

    assert result["agent_status"]["Broken"] == AgentStatus.FAILED
    assert "blog_post" not in result
    assert len(result["error_log"]) == 2
    assert result["error_log"][-1]["agent"] == "Broken"
    assert result["error_log"][-1]["error"] == "provider unavailable"
    assert result["error_log"][-1]["execution_count"] == 1
    assert "Broken" in result["execution_time"]


def test_validate_input_reports_first_missing_field():
    agent = EchoAgent()

    assert agent.validate_input({"topic": "solar"}, ["topic"]) == (True, None)
    assert agent.validate_input({"topic": None}, ["topic"]) == (
        False,
        "Missing required field: topic",
    )
    assert agent.validate_input({"topic": "solar"}, ["topic", "research_data"]) == (
        False,
        "Missing required field: research_data",
    )


def test_get_config_falls_back_to_default():
    agent = EchoAgent(config={"max_results": 3})

    assert agent.get_config("max_results") == 3
    assert agent.get_config("timeout", 10) == 10
    assert EchoAgent().get_config("max_results") is None


def test_conditional_agent_skips_when_condition_not_met():
    agent = OptionalAgent()

    skipped = agent({"topic": "solar", "needs_revision": False})

    assert agent.calls == 0
    assert skipped == {"agent_status": {"Optional": AgentStatus.COMPLETED}}

    executed = agent({"topic": "solar", "needs_revision": True})

    assert agent.calls == 1
    assert executed["blog_post"] == "revised"

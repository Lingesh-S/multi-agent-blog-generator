"""Tests for the writer agents."""

import pytest

from src.agents import writer
from src.agents.writer import WriterAgent, WriterAgentWithRevision
from src.state.schema import AgentStatus


class FakeLLM:
    def __init__(self, responses):
        self.responses = list(responses)
        self.prompts = []

    def generate(self, prompt, **kwargs):
        self.prompts.append((prompt, kwargs))
        return self.responses.pop(0)


def make_agent(responses, cls=WriterAgent, monkeypatch=None):
    llm = FakeLLM(responses)
    monkeypatch.setattr(writer, "LLMProvider", lambda: llm)
    return cls(), llm


def make_post(words_per_paragraph=100, paragraphs=4):
    return "\n\n".join(" ".join(["word"] * words_per_paragraph) for _ in range(paragraphs))


def test_writer_drafts_post_title_and_metadata(monkeypatch):
    post = make_post()
    agent, llm = make_agent([post, '"How AI Agents Are Changing Software"'], monkeypatch=monkeypatch)
    state = {
        "topic": "AI agents",
        "research_data": ["[Source 1] fact one", "[Source 2] fact two"],
        "target_audience": "developers",
        "tone": "casual",
        "word_count": 400,
        "user_requirements": "include examples",
    }

    result = agent(state)

    assert result["agent_status"]["Writer"] == AgentStatus.COMPLETED
    assert result["blog_post"] == post
    assert result["blog_title"] == "How AI Agents Are Changing Software"
    assert result["blog_metadata"] == {
        "word_count": 400,
        "character_count": len(post),
        "paragraph_count": 4,
        "estimated_reading_time": 2,
    }
    assert result["draft_iterations"] == 1
    prompt, _ = llm.prompts[0]
    assert "[Source 1] fact one\n\n[Source 2] fact two" in prompt
    assert "developers" in prompt
    assert "casual" in prompt
    assert "Additional Requirements: include examples" in prompt
    _, title_kwargs = llm.prompts[1]
    assert title_kwargs == {"temperature": 0.8, "max_tokens": 50}


def test_writer_fails_without_research_data(monkeypatch):
    agent, llm = make_agent([], monkeypatch=monkeypatch)

    result = agent({"topic": "AI agents"})

    assert result["agent_status"]["Writer"] == AgentStatus.FAILED
    assert "research_data" in result["error_log"][0]["error"]
    assert llm.prompts == []


def test_writer_revises_existing_draft_with_feedback(monkeypatch):
    agent, llm = make_agent([make_post(), "A Better Look at AI Agents Today"], monkeypatch=monkeypatch)
    state = {
        "topic": "AI agents",
        "research_data": ["fact"],
        "blog_post": "old draft text",
        "editor_feedback": "tighten the intro",
        "draft_iterations": 1,
    }

    result = agent(state)

    prompt, _ = llm.prompts[0]
    assert prompt.startswith("Revise the blog post")
    assert "tighten the intro" in prompt
    assert "old draft text" in prompt
    assert result["draft_iterations"] == 2


def test_writer_falls_back_when_title_is_too_short(monkeypatch):
    agent, _ = make_agent([make_post(), '""'], monkeypatch=monkeypatch)

    result = agent({"topic": "AI agents", "research_data": ["fact"]})

    assert result["blog_title"] == "AI agents: A Comprehensive Guide"


def test_writer_handles_zero_word_count_target(monkeypatch):
    agent, _ = make_agent([make_post(), "A Title That Is Long Enough"], monkeypatch=monkeypatch)

    result = agent({"topic": "AI", "research_data": ["fact"], "word_count": 0})

    assert result["agent_status"]["Writer"] == AgentStatus.COMPLETED


def test_revision_agent_skips_without_feedback(monkeypatch):
    agent, llm = make_agent([], cls=WriterAgentWithRevision, monkeypatch=monkeypatch)

    assert agent.revise({"blog_post": "draft"}) == {}
    assert llm.prompts == []


def test_revision_agent_revises_with_feedback(monkeypatch):
    agent, llm = make_agent(["revised draft"], cls=WriterAgentWithRevision, monkeypatch=monkeypatch)

    result = agent.revise({"blog_post": "draft", "editor_feedback": "add examples"})

    assert result == {"blog_post": "revised draft", "draft_iterations": 1}
    prompt, _ = llm.prompts[0]
    assert "draft" in prompt
    assert "add examples" in prompt


def test_writer_strips_blank_lines_around_draft(monkeypatch):
    post = "\n\nOpening paragraph about agents.\n\nSecond paragraph.\n"
    agent, llm = make_agent([post, "A Title That Is Long Enough"], monkeypatch=monkeypatch)

    result = agent({"topic": "AI", "research_data": ["fact"]})

    assert result["blog_post"] == "Opening paragraph about agents.\n\nSecond paragraph."
    title_prompt, _ = llm.prompts[1]
    assert "First paragraph of the blog:\nOpening paragraph about agents.\n" in title_prompt

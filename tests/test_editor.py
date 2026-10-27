"""Tests for the editor agents."""

import pytest

from src.agents import editor
from src.agents.editor import EditorAgent, SimpleEditorAgent
from src.state.schema import AgentStatus


class FakeLLM:
    def __init__(self, review="The post is clear and engaging."):
        self.review = review
        self.prompts = []

    def generate(self, prompt, **kwargs):
        self.prompts.append((prompt, kwargs))
        return self.review


@pytest.fixture
def fake_llm(monkeypatch):
    llm = FakeLLM()
    monkeypatch.setattr(editor, "LLMProvider", lambda: llm)
    return llm


def make_post(words_per_paragraph=100, paragraphs=3):
    return "\n\n".join(" ".join(["word"] * words_per_paragraph) for _ in range(paragraphs))


def test_editor_skips_without_blog_post(fake_llm):
    result = EditorAgent()({"topic": "AI"})

    assert result["agent_status"]["Editor"] == AgentStatus.COMPLETED
    assert "quality_score" not in result
    assert fake_llm.prompts == []


def test_editor_scores_good_post_without_revision(fake_llm):
    state = {"topic": "AI", "blog_post": make_post(), "word_count": 300, "tone": "casual"}

    result = EditorAgent()(state)

    assert result["editor_feedback"] == fake_llm.review
    assert result["quality_score"] == pytest.approx(1.0)
    assert result["needs_revision"] is False
    prompt, kwargs = fake_llm.prompts[0]
    assert "TOPIC: AI" in prompt
    assert "casual" in prompt
    assert kwargs == {"temperature": 0.3}


def test_editor_flags_negative_review_for_revision(fake_llm):
    fake_llm.review = "The intro is weak and the argument is unclear."
    state = {"topic": "AI", "blog_post": make_post(50, 1), "word_count": 500}

    result = EditorAgent()(state)

    assert result["quality_score"] < 0.7
    assert result["needs_revision"] is True


def test_editor_respects_configured_threshold(fake_llm):
    state = {"topic": "AI", "blog_post": make_post(), "word_count": 300}

    result = EditorAgent({"min_quality_score": 1.1})(state)

    assert result["needs_revision"] is True


def test_simple_editor_accepts_well_formed_post():
    state = {"blog_post": make_post(), "word_count": 300}

    result = SimpleEditorAgent()(state)

    assert result["quality_score"] == 1.0
    assert result["needs_revision"] is False
    assert result["editor_feedback"] == "Blog post meets basic quality standards."


def test_simple_editor_reports_each_issue():
    state = {"blog_post": "too short", "word_count": 500}

    result = SimpleEditorAgent()(state)

    feedback = result["editor_feedback"]
    assert "Word count is 2 (target: 500)" in feedback
    assert "more paragraphs" in feedback
    assert "too short" in feedback
    assert result["quality_score"] == pytest.approx(0.3)
    assert result["needs_revision"] is True

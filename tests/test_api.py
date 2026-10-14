"""Tests for API validation and route behavior without external providers."""

from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from src.agents.orchestrator import WorkflowExecutionError
from src.api.app import health
from src.api.routes import generate_blog
from src.api.schemas import GenerateRequest


class FakeOrchestrator:
    def run(self, **kwargs):
        return {
            "topic": kwargs["topic"],
            "blog_title": "A useful article",
            "blog_post": "First paragraph.\n\nSecond paragraph.",
            "blog_metadata": {"word_count": 5, "estimated_reading_time": 1},
            "research_sources": [{"title": "Example", "url": "https://example.com", "snippet": "Source"}],
            "quality_score": 0.9,
            "execution_time": {"Researcher": 0.1},
        }


def make_request(orchestrator):
    return SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(orchestrator=orchestrator))
    )


def test_health_and_dashboard_assets():
    from src.api.app import static_dir

    assert health()["status"] == "ok"
    assert (Path(static_dir) / "index.html").is_file()


def test_generate_returns_article_and_sources():
    response = generate_blog(
        GenerateRequest(topic="Community solar"), make_request(FakeOrchestrator())
    )

    assert response.title == "A useful article"
    assert response.sources[0]["url"] == "https://example.com"


def test_generate_rejects_invalid_input():
    with pytest.raises(ValidationError):
        GenerateRequest(topic="AI")
    with pytest.raises(ValidationError):
        GenerateRequest(topic="Valid topic", unexpected=True)


def test_workflow_errors_map_to_bad_gateway():
    class FailingOrchestrator:
        def run(self, **kwargs):
            raise WorkflowExecutionError("Writer failed")

    with pytest.raises(HTTPException) as error:
        generate_blog(
            GenerateRequest(topic="Community solar"),
            make_request(FailingOrchestrator()),
        )

    assert error.value.status_code == 502

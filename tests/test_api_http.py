"""HTTP-level tests for the FastAPI app: routing, rate limiting and error mapping."""

import pytest
from fastapi.testclient import TestClient

from src.agents.orchestrator import WorkflowExecutionError
from src.api import app as app_module


class FakeOrchestrator:
    def __init__(self, error=None):
        self.error = error
        self.calls = []

    def run(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return {
            "topic": kwargs["topic"],
            "blog_title": "A useful article",
            "blog_post": "First paragraph.",
            "blog_metadata": {"word_count": 2},
            "research_sources": [],
            "quality_score": 0.8,
            "execution_time": {"Writer": 0.1},
        }


@pytest.fixture
def client(monkeypatch):
    orchestrator = FakeOrchestrator()
    monkeypatch.setattr(app_module.app.state, "orchestrator", orchestrator, raising=False)
    app_module.request_times.clear()
    # no context manager, so the lifespan does not build a real orchestrator
    yield TestClient(app_module.app), orchestrator
    app_module.request_times.clear()


def test_health_endpoint(client):
    test_client, _ = client
    response = test_client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_dashboard_is_served(client):
    test_client, _ = client
    response = test_client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_generate_over_http(client):
    test_client, orchestrator = client
    response = test_client.post("/api/v1/generate", json={"topic": "Community solar"})

    assert response.status_code == 200
    assert response.json()["title"] == "A useful article"
    assert orchestrator.calls[0]["topic"] == "Community solar"


def test_generate_rejects_short_topic_with_422(client):
    test_client, orchestrator = client
    response = test_client.post("/api/v1/generate", json={"topic": "AI"})

    assert response.status_code == 422
    assert orchestrator.calls == []


def test_workflow_error_returns_502(client):
    test_client, orchestrator = client
    orchestrator.error = WorkflowExecutionError("research failed")
    response = test_client.post("/api/v1/generate", json={"topic": "Community solar"})

    assert response.status_code == 502
    assert response.json()["detail"] == "research failed"


def test_unexpected_error_returns_generic_500(client):
    test_client, orchestrator = client
    orchestrator.error = RuntimeError("secret internals")
    response = test_client.post("/api/v1/generate", json={"topic": "Community solar"})

    assert response.status_code == 500
    assert "secret internals" not in response.text


def test_rate_limit_blocks_after_limit(client, monkeypatch):
    test_client, orchestrator = client
    monkeypatch.setattr(app_module.settings, "rate_limit_requests", 2)
    body = {"topic": "Community solar"}

    assert test_client.post("/api/v1/generate", json=body).status_code == 200
    assert test_client.post("/api/v1/generate", json=body).status_code == 200
    blocked = test_client.post("/api/v1/generate", json=body)

    assert blocked.status_code == 429
    assert int(blocked.headers["Retry-After"]) >= 1
    assert len(orchestrator.calls) == 2


def test_rate_limit_only_applies_to_generate(client, monkeypatch):
    test_client, _ = client
    monkeypatch.setattr(app_module.settings, "rate_limit_requests", 1)

    for _ in range(3):
        assert test_client.get("/health").status_code == 200


def test_rate_limit_window_expires(client, monkeypatch):
    test_client, _ = client
    monkeypatch.setattr(app_module.settings, "rate_limit_requests", 1)
    monkeypatch.setattr(app_module.settings, "rate_limit_period", 10)
    now = [1000.0]
    monkeypatch.setattr(app_module, "monotonic", lambda: now[0])
    body = {"topic": "Community solar"}

    assert test_client.post("/api/v1/generate", json=body).status_code == 200
    assert test_client.post("/api/v1/generate", json=body).status_code == 429
    now[0] += 11
    assert test_client.post("/api/v1/generate", json=body).status_code == 200

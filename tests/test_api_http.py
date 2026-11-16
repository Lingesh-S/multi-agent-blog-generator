"""HTTP level tests for the API app, using a stubbed orchestrator."""

import pytest
from fastapi.testclient import TestClient

from src.agents.orchestrator import WorkflowExecutionError
from src.api import app as app_module

ORIGIN = "http://localhost:3000"
PREFLIGHT_HEADERS = {
    "Origin": ORIGIN,
    "Access-Control-Request-Method": "POST",
    "Access-Control-Request-Headers": "content-type",
}


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
            "quality_score": 0.9,
        }


@pytest.fixture
def orchestrator():
    return FakeOrchestrator()


@pytest.fixture
def client(orchestrator, monkeypatch):
    # No context manager, so the lifespan never builds a real orchestrator
    monkeypatch.setattr(app_module.app.state, "orchestrator", orchestrator, raising=False)
    if hasattr(app_module, "request_times"):
        app_module.request_times.clear()
    return TestClient(app_module.app)


@pytest.fixture
def rate_limit(monkeypatch):
    if not hasattr(app_module, "request_times"):
        pytest.skip("rate limiting is disabled in this environment")
    monkeypatch.setattr(app_module.settings, "rate_limit_requests", 2)
    monkeypatch.setattr(app_module.settings, "rate_limit_period", 60)


def generate(client, **overrides):
    return client.post(
        "/api/v1/generate",
        json={"topic": "Community solar", **overrides},
        headers={"Origin": ORIGIN},
    )


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_dashboard_is_served(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_generate_returns_article(client, orchestrator):
    response = generate(client, word_count=700)

    assert response.status_code == 200
    assert response.json()["title"] == "A useful article"
    assert response.json()["sources"] == []
    assert orchestrator.calls[0]["word_count"] == 700


def test_generate_rejects_invalid_payload(client, orchestrator):
    assert generate(client, topic="AI").status_code == 422
    assert generate(client, unexpected=True).status_code == 422
    assert orchestrator.calls == []


def test_workflow_error_returns_bad_gateway(client, orchestrator):
    orchestrator.error = WorkflowExecutionError("Writer failed")

    response = generate(client)

    assert response.status_code == 502
    assert response.json()["detail"] == "Writer failed"


def test_unexpected_error_hides_details(client, orchestrator):
    orchestrator.error = RuntimeError("secret connection string")

    response = generate(client)

    assert response.status_code == 500
    assert "secret" not in response.text


def test_rate_limit_blocks_extra_requests(client, rate_limit):
    assert generate(client).status_code == 200
    assert generate(client).status_code == 200

    blocked = generate(client)

    assert blocked.status_code == 429
    assert blocked.json() == {"detail": "Rate limit exceeded"}
    assert 1 <= int(blocked.headers["Retry-After"]) <= 60


def test_rate_limit_ignores_other_paths(client, rate_limit):
    for _ in range(5):
        assert client.get("/health").status_code == 200

    assert generate(client).status_code == 200


def test_preflight_requests_do_not_use_the_rate_limit(client, rate_limit):
    for _ in range(5):
        assert client.options("/api/v1/generate", headers=PREFLIGHT_HEADERS).status_code == 200

    assert generate(client).status_code == 200
    assert generate(client).status_code == 200


def test_rate_limited_response_keeps_cors_headers(client, rate_limit):
    generate(client)
    generate(client)

    blocked = generate(client)

    assert blocked.status_code == 429
    assert blocked.headers["access-control-allow-origin"] == ORIGIN

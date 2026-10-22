"""Tests for the command line interface without external providers."""

import json

import pytest
from click.testing import CliRunner

from src.cli import main as cli_main


RESULT = {
    "blog_title": "Café culture “explained”",
    "blog_post": "First paragraph.\n\nSecond paragraph with an emoji ☕.",
    "blog_metadata": {"word_count": 9, "paragraph_count": 2, "estimated_reading_time": 1},
    "quality_score": 0.0,
}


class FakeOrchestrator:
    def __init__(self, fail_on=None):
        self.calls = []
        self.fail_on = fail_on

    def run(self, **kwargs):
        self.calls.append(kwargs)
        if kwargs["topic"] == self.fail_on:
            raise RuntimeError("provider unavailable")
        return dict(RESULT, topic=kwargs["topic"])


@pytest.fixture
def orchestrator(monkeypatch):
    fake = FakeOrchestrator(fail_on="Broken topic")
    monkeypatch.setattr(cli_main, "MultiAgentOrchestrator", lambda: fake)
    monkeypatch.setattr(cli_main, "validate_configuration", lambda: (True, None))
    return fake


def test_generate_saves_markdown_with_unicode(orchestrator, tmp_path):
    output = tmp_path / "posts" / "article.md"

    result = CliRunner().invoke(
        cli_main.cli,
        ["generate", "--topic", "Coffee", "--words", "700", "--format", "markdown", "--output", str(output)],
    )

    assert result.exit_code == 0, result.output
    assert output.read_text(encoding="utf-8").startswith("# Café culture “explained”")
    assert "☕" in output.read_text(encoding="utf-8")
    assert orchestrator.calls[0]["word_count"] == 700


def test_generate_saves_json(orchestrator, tmp_path):
    output = tmp_path / "article.json"

    result = CliRunner().invoke(
        cli_main.cli, ["generate", "--topic", "Coffee", "--format", "json", "--output", str(output)]
    )

    assert result.exit_code == 0, result.output
    assert json.loads(output.read_text(encoding="utf-8"))["topic"] == "Coffee"


def test_generate_stops_on_invalid_configuration(orchestrator, monkeypatch):
    monkeypatch.setattr(cli_main, "validate_configuration", lambda: (False, "Missing required API keys: OPENAI_API_KEY"))

    result = CliRunner().invoke(cli_main.cli, ["generate", "--topic", "Coffee"])

    assert result.exit_code != 0
    assert "Missing required API keys" in result.output
    assert orchestrator.calls == []


def test_generate_reports_orchestrator_errors(orchestrator):
    result = CliRunner().invoke(cli_main.cli, ["generate", "--topic", "Broken topic"])

    assert result.exit_code != 0
    assert "provider unavailable" in result.output


def test_display_results_shows_zero_quality_score(capsys):
    cli_main._display_results(RESULT, "markdown")

    assert "Quality Score: 0.00" in capsys.readouterr().out


def test_batch_processes_topics_and_continues_after_errors(orchestrator, tmp_path):
    config = tmp_path / "batch.json"
    first = tmp_path / "first.md"
    config.write_text(
        json.dumps({
            "topics": [
                {"topic": "Thé à la menthe", "audience": "travellers", "output": str(first)},
                {"topic": "Broken topic", "output": str(tmp_path / "broken.md")},
            ]
        }, ensure_ascii=False),
        encoding="utf-8",
    )

    result = CliRunner().invoke(cli_main.cli, ["batch", str(config)])

    assert result.exit_code == 0, result.output
    assert first.read_text(encoding="utf-8").startswith("# Café culture")
    assert not (tmp_path / "broken.md").exists()
    assert orchestrator.calls[0]["target_audience"] == "travellers"
    assert orchestrator.calls[1]["word_count"] == 500


def test_batch_with_no_topics(orchestrator, tmp_path):
    config = tmp_path / "empty.json"
    config.write_text('{"topics": []}', encoding="utf-8")

    result = CliRunner().invoke(cli_main.cli, ["batch", str(config)])

    assert result.exit_code == 0
    assert "No topics found" in result.output
    assert orchestrator.calls == []

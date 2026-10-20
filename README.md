# Multi-Agent Blog Generator

Research a topic and turn it into an edited blog post with a coordinated team of AI agents. Use the web dashboard, the command line, or the HTTP API.

## What it does

- Researches topics with DuckDuckGo, Serper, or Tavily.
- Drafts and reviews articles with Ollama or OpenAI.
- Supports iterative editing, configurable audience, tone, and length.
- Caches successful search results with configurable TTL and size limits.
- Includes a responsive dashboard, REST API, CLI, Docker setup, and optional Prometheus metrics.

## Quick start

Requires Python 3.10 or newer. For local generation, install [Ollama](https://ollama.com/) and pull a model, or configure an OpenAI API key.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
ollama pull llama3
uvicorn src.api.app:app --reload
```

Open [http://localhost:8000](http://localhost:8000) for the dashboard, or use the CLI:

```bash
python -m src.cli.main generate --topic "Community solar" --audience "local leaders" --words 700 --format markdown --output article.md
```

## HTTP API

`POST /api/v1/generate` accepts JSON:

```json
{
  "topic": "Community solar",
  "user_requirements": "Focus on practical benefits and trade-offs",
  "target_audience": "local leaders",
  "tone": "professional",
  "word_count": 700
}
```

The response includes the article title and content, metadata, research sources, quality score, and per-agent execution times. Inputs are validated; provider/workflow failures return an error response. Interactive API docs are available at `/docs`, and `/health` reports service liveness. Generation requests are rate-limited in memory per client process; use an API gateway or shared limiter when deploying multiple workers.

## Configuration

Settings are loaded from environment variables or a local `.env` file. Copy `.env.example` to `.env` to start from a template with every option. The table below lists common options; the remaining settings are defined in `src/config/settings.py`.

| Variable | Default | Purpose |
| --- | --- | --- |
| `LLM_PROVIDER` | `ollama` | `ollama` or `openai` |
| `LLM_MODEL` | `llama3` | Model name for the selected provider |
| `OPENAI_API_KEY` | unset | Required when using OpenAI |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server address |
| `SEARCH_PROVIDER` | `duckduckgo` | `duckduckgo`, `serper`, or `tavily` |
| `SERPER_API_KEY` / `TAVILY_API_KEY` | unset | Required by the matching search provider |
| `CACHE_ENABLED` | `true` | Enable successful search result caching |
| `CACHE_TTL` | `3600` | Cache lifetime in seconds |
| `PROMETHEUS_ENABLED` | `false` | Expose HTTP metrics at `/metrics` |
| `CORS_ORIGINS` | `http://localhost:3000` | Allowed browser origins |

## Use cases

- Generate blog posts and newsletters for content marketing.
- Create technical explainers for developers and customers.
- Draft product descriptions based on researched features and audience needs.
- Turn current research into a first draft for editorial review.

## Docker

From the repository root, configure provider environment variables (or a local `.env` file) and start the API plus Ollama:

```bash
docker compose -f docker/docker-compose.yml up --build
```

The dashboard is available at `http://localhost:8000`. The compose setup starts Ollama and pulls the configured default model on first launch; first model download can take several minutes.

## Development

```bash
pip install -r requirements-dev.txt
pytest
```

`pytest.ini` runs the suite with coverage and writes an HTML report to `htmlcov/`. Tests that need a live LLM or internet access are marked `requires_llm` and `requires_search`; skip them with `pytest -m "not requires_llm and not requires_search"`.

Core modules live under `src/agents`, `src/tools`, `src/api`, `src/cli`, and `src/state`. See [docs/architecture.md](docs/architecture.md) for the workflow and [docs/QUICKSTART.md](docs/QUICKSTART.md) for API and deployment examples.

## License

MIT. See [LICENSE](LICENSE).

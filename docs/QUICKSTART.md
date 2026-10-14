# Quick Start

## Requirements

- Python 3.10 or newer
- Ollama running locally with a model installed, or an OpenAI API key
- Internet access for web research

## Install and run

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
ollama pull llama3
uvicorn src.api.app:app --reload
```

The dashboard runs at `http://localhost:8000`. The REST API documentation is at `http://localhost:8000/docs`.

To use OpenAI, set `LLM_PROVIDER=openai`, `LLM_MODEL` to a supported model, and `OPENAI_API_KEY` in your environment before starting the server. For Serper or Tavily search, set `SEARCH_PROVIDER` and the matching API key.

## Generate from the CLI

```bash
python -m src.cli.main generate \
  --topic "Machine learning in healthcare" \
  --audience "healthcare professionals" \
  --tone professional \
  --words 800 \
  --format markdown \
  --output article.md
```

Use `python -m src.cli.main check` to inspect configuration and optional provider connectivity.

## Generate over HTTP

```bash
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{"topic":"Community solar","target_audience":"local leaders","tone":"professional","word_count":700}'
```

The response contains the title, article content, metadata, research sources, quality score, and execution times. The service also provides `GET /health`. Set `PROMETHEUS_ENABLED=true` to expose `GET /metrics`.

## Docker

From the repository root:

```bash
docker compose -f docker/docker-compose.yml up --build
```

Compose starts the API and Ollama, then pulls the default `llama3` model. Initial startup can take a few minutes. Set provider environment variables in a local `.env` file when using a hosted LLM or paid search provider.

## Configuration

Configuration uses environment variables; names are case-insensitive. Common options include `LLM_PROVIDER`, `LLM_MODEL`, `OPENAI_API_KEY`, `OLLAMA_BASE_URL`, `SEARCH_PROVIDER`, `SERPER_API_KEY`, `TAVILY_API_KEY`, `EDITOR_ENABLED`, `CACHE_ENABLED`, `CACHE_TTL`, `RATE_LIMIT_ENABLED`, and `PROMETHEUS_ENABLED`.

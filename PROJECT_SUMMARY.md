# Project Summary

The Multi-Agent Blog Generator researches a topic, drafts an article, and reviews the result. The same generation workflow is available through a browser dashboard, REST API, Python interface, and command line.

## Workflow

1. The researcher searches the configured provider and collects snippets and source URLs.
2. The writer creates an article for the requested audience, tone, and length.
3. The editor reviews the draft and returns quality feedback. `IterativeOrchestrator` can send that feedback back to the writer for a bounded revision loop.
4. The orchestrator returns the article, sources, metadata, quality assessment, and per-agent execution times. Failed agents produce a workflow error instead of a successful-looking empty result.

## Interfaces

- Browser dashboard at `/` with generation controls, article metadata, source links, and copy action.
- `POST /api/v1/generate` with validated input and structured output.
- `GET /health`, interactive OpenAPI docs at `/docs`, and optional Prometheus metrics at `/metrics`.
- CLI commands: `generate`, `batch`, and `check`.
- Docker Compose runs the API with Ollama for local model serving.

## Providers and configuration

LLM providers: Ollama and OpenAI. Search providers: DuckDuckGo, Serper, and Tavily. Configuration is loaded from environment variables or `.env`; API keys are not stored in source. Search results can be cached in process with a configurable expiration and maximum entry count. API generation requests use a configurable in-memory per-client rate limit.

The in-memory cache and rate limiter are local to each process. Multi-worker deployments should use a shared cache and rate-limit service if cross-worker consistency is required.

## Repository layout

- `src/agents/`: researcher, writer, editor, and workflow graph.
- `src/api/`: FastAPI routes, request/response models, and dashboard assets.
- `src/cli/`: command-line entry point and output formatting.
- `src/config/`: validated environment settings.
- `src/state/`: workflow state and validation.
- `src/tools/`: LLM and search provider adapters.
- `tests/`: state schema tests.
- `docs/`: quick start and architecture guides.
- `docker/`: API image and Compose deployment.

## Run locally

See [README.md](README.md) for installation, provider configuration, API requests, and Docker commands. The default local model is Ollama `llama3`; a running Ollama server and installed model are required for generation unless OpenAI is configured.

"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from pathlib import Path
from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from src.agents.orchestrator import MultiAgentOrchestrator
from src.api.routes import router
from src.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.orchestrator = MultiAgentOrchestrator()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Research and generate blog posts with a coordinated team of AI agents.",
    lifespan=lifespan,
)
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)
app.include_router(router)

if settings.rate_limit_enabled:
    request_times = defaultdict(deque)
    rate_limit_lock = Lock()

    @app.middleware("http")
    async def limit_generation_requests(request, call_next):
        if request.url.path != "/api/v1/generate":
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = monotonic()
        with rate_limit_lock:
            cutoff = now - settings.rate_limit_period
            for address in list(request_times):
                while request_times[address] and request_times[address][0] <= cutoff:
                    request_times[address].popleft()
                if not request_times[address]:
                    del request_times[address]
            recent_requests = request_times[client_ip]
            if len(recent_requests) >= settings.rate_limit_requests:
                retry_after = max(1, int(recent_requests[0] + settings.rate_limit_period - now))
                return Response(
                    content='{"detail":"Rate limit exceeded"}',
                    status_code=429,
                    media_type="application/json",
                    headers={"Retry-After": str(retry_after)},
                )
            recent_requests.append(now)

        return await call_next(request)


@app.get("/health", tags=["system"])
def health() -> dict:
    return {
        "status": "ok",
        "application": settings.app_name,
        "version": settings.app_version,
    }


@app.get("/", include_in_schema=False)
def dashboard():
    from fastapi.responses import FileResponse

    return FileResponse(static_dir / "index.html")


if settings.prometheus_enabled:
    from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

    REQUEST_COUNT = Counter(
        "blog_generator_http_requests_total",
        "HTTP requests handled by the blog generator",
        ["method", "path", "status"],
    )
    REQUEST_DURATION = Histogram(
        "blog_generator_http_request_duration_seconds",
        "HTTP request duration in seconds",
        ["method", "path"],
    )

    @app.middleware("http")
    async def record_metrics(request, call_next):
        import time

        started_at = time.perf_counter()
        response = await call_next(request)
        route = request.scope.get("route")
        path = getattr(route, "path", "unmatched")
        REQUEST_COUNT.labels(request.method, path, str(response.status_code)).inc()
        REQUEST_DURATION.labels(request.method, path).observe(time.perf_counter() - started_at)
        return response

    @app.get("/metrics", include_in_schema=False)
    def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

"""HTTP routes for blog generation."""

import logging

from fastapi import APIRouter, HTTPException, Request, status

from src.agents.orchestrator import WorkflowExecutionError
from src.api.schemas import GenerateRequest, GenerateResponse

router = APIRouter(prefix="/api/v1", tags=["generation"])
logger = logging.getLogger("api")


@router.post(
    "/generate",
    response_model=GenerateResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate a researched blog post",
)
def generate_blog(payload: GenerateRequest, request: Request) -> GenerateResponse:
    """Run the synchronous agent workflow in FastAPI's worker thread pool."""
    try:
        result = request.app.state.orchestrator.run(
            topic=payload.topic,
            user_requirements=payload.user_requirements,
            target_audience=payload.target_audience,
            tone=payload.tone,
            word_count=payload.word_count,
        )
    except WorkflowExecutionError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected blog generation error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Blog generation failed; check server logs for details",
        ) from exc

    return GenerateResponse(
        topic=result["topic"],
        title=result.get("blog_title") or payload.topic,
        content=result["blog_post"],
        metadata=result.get("blog_metadata") or {},
        sources=result.get("research_sources") or [],
        quality_score=result.get("quality_score"),
        execution_time=result.get("execution_time") or {},
    )

"""Request and response models for the public API."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    """Options accepted by the blog generation endpoint."""

    model_config = {"extra": "forbid"}

    topic: str = Field(min_length=3, max_length=200)
    user_requirements: Optional[str] = Field(default=None, max_length=5000)
    target_audience: str = Field(default="general", min_length=1, max_length=200)
    tone: str = Field(default="professional", min_length=1, max_length=100)
    word_count: int = Field(default=500, ge=100, le=5000)


class GenerateResponse(BaseModel):
    """Generated article and the useful workflow metadata."""

    topic: str
    title: str
    content: str
    metadata: Dict[str, Any]
    sources: List[Dict[str, str]]
    quality_score: Optional[float] = None
    execution_time: Dict[str, float]


class HealthResponse(BaseModel):
    status: str
    application: str
    version: str

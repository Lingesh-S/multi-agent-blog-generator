"""Request and response models for the public API."""

from typing import Any

from pydantic import BaseModel, Field, field_validator


class GenerateRequest(BaseModel):
    """Options accepted by the blog generation endpoint."""

    model_config = {"extra": "forbid", "str_strip_whitespace": True}

    topic: str = Field(min_length=3, max_length=200)
    user_requirements: str | None = Field(default=None, max_length=5000)
    target_audience: str = Field(default="general", min_length=1, max_length=200)
    tone: str = Field(default="professional", min_length=1, max_length=100)
    word_count: int = Field(default=500, ge=100, le=5000)

    @field_validator("user_requirements")
    @classmethod
    def blank_requirements_to_none(cls, value: str | None) -> str | None:
        """The dashboard sends an empty string when no requirements are given."""
        return value or None


class GenerateResponse(BaseModel):
    """Generated article and the useful workflow metadata."""

    topic: str
    title: str
    content: str
    metadata: dict[str, Any]
    sources: list[dict[str, str]]
    quality_score: float | None = None
    execution_time: dict[str, float]


class HealthResponse(BaseModel):
    status: str
    application: str
    version: str

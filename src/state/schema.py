"""
State Schema for Multi-Agent System

Defines the shared state structure that all agents can read and write to.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from typing_extensions import TypedDict


class AgentStatus(str, Enum):
    """Status of agent execution"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ResearchQuality(str, Enum):
    """Quality assessment for research data"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class AgentState(TypedDict, total=False):
    """
    Shared state dictionary for the multi-agent system.

    This acts as the "clipboard" that all agents can read from and write to.
    TypedDict provides type hints for better IDE support and validation.
    """

    # Input
    topic: str
    user_requirements: str | None
    target_audience: str | None
    tone: str | None  # e.g., "professional", "casual", "technical"
    word_count: int | None

    # Research Phase
    research_data: list[str]
    research_sources: list[dict[str, str]]  # List of {url, title, snippet}
    research_quality: ResearchQuality
    research_timestamp: datetime | None

    # Writing Phase
    blog_post: str
    blog_title: str | None
    blog_metadata: dict[str, Any] | None
    draft_iterations: int

    # Editor Phase (NEW)
    editor_feedback: str | None
    quality_score: float | None  # 0.0 to 1.0
    needs_revision: bool

    # Execution Metadata
    agent_status: dict[str, AgentStatus]
    execution_time: dict[str, float]  # time in seconds per agent
    error_log: list[dict[str, Any]]

    # Version Control
    version: int
    last_modified_by: str | None  # which agent last modified the state
    last_modified_at: datetime | None


class WorkflowConfig(TypedDict, total=False):
    """Configuration for workflow execution"""

    max_research_results: int
    enable_editor: bool
    max_iterations: int
    timeout_seconds: int
    parallel_execution: bool


class AgentResponse(TypedDict):
    """Standard response format from agents"""

    success: bool
    agent_name: str
    data: dict[str, Any]
    error: str | None
    execution_time: float


def create_initial_state(
    topic: str,
    user_requirements: str | None = None,
    target_audience: str = "general",
    tone: str = "professional",
    word_count: int = 500
) -> AgentState:
    """
    Factory function to create initial state with defaults.

    Args:
        topic: The main topic for blog generation
        user_requirements: Additional requirements from user
        target_audience: Target audience for the blog
        tone: Writing tone (professional, casual, technical)
        word_count: Target word count for the blog

    Returns:
        AgentState: Initial state dictionary
    """
    return AgentState(
        # Input
        topic=topic,
        user_requirements=user_requirements,
        target_audience=target_audience,
        tone=tone,
        word_count=word_count,

        # Research Phase
        research_data=[],
        research_sources=[],
        research_quality=ResearchQuality.UNKNOWN,
        research_timestamp=None,

        # Writing Phase
        blog_post="",
        blog_title=None,
        blog_metadata=None,
        draft_iterations=0,

        # Editor Phase
        editor_feedback=None,
        quality_score=None,
        needs_revision=False,

        # Execution Metadata
        agent_status={},
        execution_time={},
        error_log=[],

        # Version Control
        version=1,
        last_modified_by=None,
        last_modified_at=datetime.now()
    )


def validate_state(state: AgentState) -> tuple[bool, str | None]:
    """
    Validate state structure and required fields.

    Returns:
        Tuple of (is_valid, error_message)
    """
    required_fields = ["topic"]

    for field in required_fields:
        if field not in state or not state[field]:
            return False, f"Missing required field: {field}"

    # Validate topic length
    if len(state["topic"]) < 3:
        return False, "Topic must be at least 3 characters long"

    if len(state["topic"]) > 200:
        return False, "Topic must be less than 200 characters"

    return True, None

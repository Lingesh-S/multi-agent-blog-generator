"""
Unit Tests for State Schema
"""

import pytest
from datetime import datetime

from src.state.schema import (
    AgentState,
    AgentStatus,
    ResearchQuality,
    create_initial_state,
    validate_state
)


class TestStateCreation:
    """Test state initialization"""
    
    def test_create_initial_state_basic(self):
        """Test basic state creation"""
        state = create_initial_state(topic="Test Topic")
        
        assert state["topic"] == "Test Topic"
        assert state["research_data"] == []
        assert state["blog_post"] == ""
        assert state["version"] == 1
    
    def test_create_initial_state_with_params(self):
        """Test state creation with parameters"""
        state = create_initial_state(
            topic="AI Agents",
            user_requirements="Focus on practical applications",
            target_audience="developers",
            tone="technical",
            word_count=1000
        )
        
        assert state["topic"] == "AI Agents"
        assert state["user_requirements"] == "Focus on practical applications"
        assert state["target_audience"] == "developers"
        assert state["tone"] == "technical"
        assert state["word_count"] == 1000


class TestStateValidation:
    """Test state validation"""
    
    def test_validate_valid_state(self):
        """Test validation of valid state"""
        state = create_initial_state(topic="Valid Topic")
        is_valid, error = validate_state(state)
        
        assert is_valid is True
        assert error is None
    
    def test_validate_missing_topic(self):
        """Test validation fails with missing topic"""
        state = AgentState(research_data=[], blog_post="")
        is_valid, error = validate_state(state)
        
        assert is_valid is False
        assert "topic" in error.lower()
    
    def test_validate_short_topic(self):
        """Test validation fails with very short topic"""
        state = create_initial_state(topic="AI")
        is_valid, error = validate_state(state)
        
        assert is_valid is False
        assert "3 characters" in error
    
    def test_validate_long_topic(self):
        """Test validation fails with very long topic"""
        state = create_initial_state(topic="x" * 250)
        is_valid, error = validate_state(state)
        
        assert is_valid is False
        assert "200 characters" in error


class TestEnums:
    """Test enum definitions"""
    
    def test_agent_status_values(self):
        """Test AgentStatus enum values"""
        assert AgentStatus.PENDING == "pending"
        assert AgentStatus.IN_PROGRESS == "in_progress"
        assert AgentStatus.COMPLETED == "completed"
        assert AgentStatus.FAILED == "failed"
    
    def test_research_quality_values(self):
        """Test ResearchQuality enum values"""
        assert ResearchQuality.HIGH == "high"
        assert ResearchQuality.MEDIUM == "medium"
        assert ResearchQuality.LOW == "low"
        assert ResearchQuality.UNKNOWN == "unknown"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

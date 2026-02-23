"""
Base Agent Class

Provides common functionality for all agents in the system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import time
import logging

from src.state.schema import AgentState, AgentStatus, AgentResponse


class BaseAgent(ABC):
    """
    Abstract base class for all agents.
    
    All agents must implement the execute() method.
    Provides common functionality like logging, error handling, and timing.
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize base agent.
        
        Args:
            name: Agent name (e.g., "Researcher", "Writer")
            config: Optional configuration dictionary
        """
        self.name = name
        self.config = config or {}
        self.logger = logging.getLogger(f"agent.{name.lower()}")
        self.execution_count = 0
        
    @abstractmethod
    def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute the agent's main logic.
        
        Args:
            state: Current state of the multi-agent system
            
        Returns:
            Dictionary with updates to apply to state
        """
        pass
    
    def __call__(self, state: AgentState) -> Dict[str, Any]:
        """
        Make the agent callable. Wraps execute() with common functionality.
        
        Args:
            state: Current state
            
        Returns:
            Dictionary with state updates
        """
        self.execution_count += 1
        start_time = time.time()
        
        try:
            self.logger.info(f"{self.name} starting execution #{self.execution_count}")
            
            # Update agent status to in_progress
            self._update_status(state, AgentStatus.IN_PROGRESS)
            
            # Execute the agent's logic
            result = self.execute(state)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Add metadata to result
            result.update({
                "last_modified_by": self.name,
                "last_modified_at": datetime.now(),
                "execution_time": {
                    **state.get("execution_time", {}),
                    self.name: execution_time
                },
                "agent_status": {
                    **state.get("agent_status", {}),
                    self.name: AgentStatus.COMPLETED
                }
            })
            
            self.logger.info(
                f"{self.name} completed in {execution_time:.2f}s",
                extra={"execution_time": execution_time, "execution_count": self.execution_count}
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(
                f"{self.name} failed after {execution_time:.2f}s: {str(e)}",
                exc_info=True
            )
            
            # Log error in state
            error_entry = {
                "agent": self.name,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "execution_count": self.execution_count
            }
            
            return {
                "agent_status": {
                    **state.get("agent_status", {}),
                    self.name: AgentStatus.FAILED
                },
                "error_log": state.get("error_log", []) + [error_entry],
                "execution_time": {
                    **state.get("execution_time", {}),
                    self.name: execution_time
                }
            }
    
    def _update_status(self, state: AgentState, status: AgentStatus) -> None:
        """Update agent status in state"""
        if "agent_status" not in state:
            state["agent_status"] = {}
        state["agent_status"][self.name] = status
    
    def validate_input(self, state: AgentState, required_fields: list) -> tuple[bool, Optional[str]]:
        """
        Validate that required fields are present in state.
        
        Args:
            state: Current state
            required_fields: List of required field names
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        for field in required_fields:
            if field not in state or state[field] is None:
                return False, f"Missing required field: {field}"
        return True, None
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value with fallback.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        return self.config.get(key, default)
    
    def log_metric(self, metric_name: str, value: float) -> None:
        """
        Log a metric for monitoring.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
        """
        self.logger.info(
            f"Metric: {metric_name}",
            extra={"metric": metric_name, "value": value, "agent": self.name}
        )


class ConditionalAgent(BaseAgent):
    """
    Base class for agents that may conditionally execute.
    
    Provides should_execute() method to determine if agent should run.
    """
    
    def should_execute(self, state: AgentState) -> bool:
        """
        Determine if this agent should execute based on state.
        
        Args:
            state: Current state
            
        Returns:
            True if agent should execute, False otherwise
        """
        return True
    
    def __call__(self, state: AgentState) -> Dict[str, Any]:
        """Override to add conditional execution logic"""
        
        if not self.should_execute(state):
            self.logger.info(f"{self.name} skipped (condition not met)")
            return {
                "agent_status": {
                    **state.get("agent_status", {}),
                    self.name: AgentStatus.COMPLETED
                }
            }
        
        return super().__call__(state)

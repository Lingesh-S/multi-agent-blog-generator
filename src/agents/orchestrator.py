"""
Multi-Agent Orchestrator

Coordinates the workflow between all agents using LangGraph.
"""

from typing import Dict, Any, Optional
import logging

from langgraph.graph import StateGraph, END

from src.state.schema import AgentState, create_initial_state, validate_state
from src.agents.researcher import ResearcherAgent
from src.agents.writer import WriterAgent
from src.agents.editor import EditorAgent
from src.config import get_settings


class MultiAgentOrchestrator:
    """
    Main orchestrator that builds and executes the multi-agent workflow.
    
    This class uses LangGraph to create a state machine that coordinates
    the execution of multiple specialized agents.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the orchestrator.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.settings = get_settings()
        self.logger = logging.getLogger("orchestrator")
        
        # Initialize agents
        self.researcher = ResearcherAgent(config=self.config.get("researcher"))
        self.writer = WriterAgent(config=self.config.get("writer"))
        self.editor = EditorAgent(config=self.config.get("editor")) if self.settings.editor_enabled else None
        
        # Build workflow graph
        self.app = self._build_graph()
        
        self.logger.info("Multi-Agent Orchestrator initialized")
    
    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow.
        
        Returns:
            Compiled StateGraph application
        """
        workflow = StateGraph(AgentState)
        
        # Add agent nodes
        workflow.add_node("Researcher", self.researcher)
        workflow.add_node("Writer", self.writer)
        
        # Add editor if enabled
        if self.editor is not None:
            workflow.add_node("Editor", self.editor)
        
        # Define workflow edges
        workflow.set_entry_point("Researcher")
        workflow.add_edge("Researcher", "Writer")
        
        if self.editor is not None:
            # With editor: Researcher -> Writer -> Editor -> END
            workflow.add_edge("Writer", "Editor")
            workflow.add_edge("Editor", END)
        else:
            # Without editor: Researcher -> Writer -> END
            workflow.add_edge("Writer", END)
        
        # Compile the graph
        app = workflow.compile()
        
        self.logger.info(f"Workflow built with {len(workflow.nodes)} agents")
        return app
    
    def run(
        self,
        topic: str,
        user_requirements: Optional[str] = None,
        target_audience: str = "general",
        tone: str = "professional",
        word_count: int = 500
    ) -> Dict[str, Any]:
        """
        Execute the complete multi-agent workflow.
        
        Args:
            topic: Main topic for blog generation
            user_requirements: Additional requirements
            target_audience: Target audience
            tone: Writing tone
            word_count: Target word count
            
        Returns:
            Final state dictionary with blog_post and metadata
        """
        self.logger.info(f"Starting workflow for topic: {topic}")
        
        # Create initial state
        initial_state = create_initial_state(
            topic=topic,
            user_requirements=user_requirements,
            target_audience=target_audience,
            tone=tone,
            word_count=word_count
        )
        
        # Validate initial state
        is_valid, error = validate_state(initial_state)
        if not is_valid:
            self.logger.error(f"Invalid initial state: {error}")
            raise ValueError(f"Invalid initial state: {error}")
        
        # Execute workflow
        try:
            result = self.app.invoke(initial_state)
            
            self.logger.info("Workflow completed successfully")
            self._log_execution_summary(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Workflow execution failed: {str(e)}", exc_info=True)
            raise
    
    def run_from_state(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute workflow from a given state.
        
        Useful for resuming from a checkpoint or running with custom state.
        
        Args:
            state: Initial state dictionary
            
        Returns:
            Final state dictionary
        """
        # Validate state
        is_valid, error = validate_state(state)
        if not is_valid:
            raise ValueError(f"Invalid state: {error}")
        
        return self.app.invoke(state)
    
    def _log_execution_summary(self, result: Dict[str, Any]) -> None:
        """Log summary of execution metrics"""
        
        execution_times = result.get("execution_time", {})
        total_time = sum(execution_times.values())
        
        self.logger.info("=" * 50)
        self.logger.info("EXECUTION SUMMARY")
        self.logger.info("=" * 50)
        
        for agent, time in execution_times.items():
            percentage = (time / total_time * 100) if total_time > 0 else 0
            self.logger.info(f"{agent}: {time:.2f}s ({percentage:.1f}%)")
        
        self.logger.info(f"Total Time: {total_time:.2f}s")
        
        # Log blog metadata
        metadata = result.get("blog_metadata", {})
        if metadata:
            self.logger.info(f"Word Count: {metadata.get('word_count', 0)}")
            self.logger.info(f"Reading Time: {metadata.get('estimated_reading_time', 0)} min")
        
        # Log quality score if available
        quality_score = result.get("quality_score")
        if quality_score:
            self.logger.info(f"Quality Score: {quality_score:.2f}")
        
        self.logger.info("=" * 50)


class IterativeOrchestrator(MultiAgentOrchestrator):
    """
    Extended orchestrator that supports iterative refinement.
    
    Allows the Writer to revise based on Editor feedback in a loop.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, max_iterations: int = 3):
        super().__init__(config)
        self.max_iterations = max_iterations
    
    def _build_graph(self) -> StateGraph:
        """
        Build workflow graph with iteration support.
        
        Returns:
            Compiled StateGraph with conditional routing
        """
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("Researcher", self.researcher)
        workflow.add_node("Writer", self.writer)
        
        if self.editor is not None:
            workflow.add_node("Editor", self.editor)
        
        # Set entry point
        workflow.set_entry_point("Researcher")
        workflow.add_edge("Researcher", "Writer")
        
        if self.editor is not None:
            # Add conditional routing
            workflow.add_edge("Writer", "Editor")
            
            # Add conditional edge from Editor
            workflow.add_conditional_edges(
                "Editor",
                self._should_continue_iterating,
                {
                    "continue": "Writer",  # Go back to writer for revision
                    "end": END  # Finish workflow
                }
            )
        else:
            workflow.add_edge("Writer", END)
        
        return workflow.compile()
    
    def _should_continue_iterating(self, state: AgentState) -> str:
        """
        Determine if iteration should continue.
        
        Args:
            state: Current state
            
        Returns:
            "continue" or "end"
        """
        draft_iterations = state.get("draft_iterations", 0)
        needs_revision = state.get("needs_revision", False)
        quality_score = state.get("quality_score", 1.0)
        
        # Check iteration limit
        if draft_iterations >= self.max_iterations:
            self.logger.info(f"Max iterations ({self.max_iterations}) reached")
            return "end"
        
        # Check if revision is needed
        if not needs_revision:
            self.logger.info("No revision needed")
            return "end"
        
        # Check quality threshold
        if quality_score >= 0.8:
            self.logger.info(f"Quality threshold met: {quality_score:.2f}")
            return "end"
        
        self.logger.info(f"Continuing iteration {draft_iterations + 1}")
        return "continue"

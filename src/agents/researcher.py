"""
Researcher Agent

Responsible for gathering information from the web about a given topic.
"""

from typing import Dict, Any, List
from datetime import datetime
import time

from src.agents.base import BaseAgent
from src.state.schema import AgentState, ResearchQuality
from src.tools.search import SearchTool
from src.config import get_settings


class ResearcherAgent(BaseAgent):
    """
    Agent that searches the web for information about a topic.
    
    Responsibilities:
    - Search the web using configured search provider
    - Extract relevant information
    - Assess research quality
    - Store results in state
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(name="Researcher", config=config)
        
        settings = get_settings()
        self.search_tool = SearchTool(
            provider=settings.search_provider,
            max_results=settings.search_max_results,
            timeout=settings.search_timeout
        )
        
        self.max_retries = settings.researcher_retries
        
    def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute research on the given topic.
        
        Args:
            state: Current state containing topic
            
        Returns:
            Dictionary with research_data and research_sources
        """
        # Validate input
        is_valid, error = self.validate_input(state, ["topic"])
        if not is_valid:
            raise ValueError(error)
        
        topic = state["topic"]
        user_requirements = state.get("user_requirements", "")
        
        self.logger.info(f"Researching topic: {topic}")
        
        # Build search query
        search_query = self._build_search_query(topic, user_requirements)
        
        # Perform search with retries
        results = self._search_with_retry(search_query)
        
        # Process and extract information
        research_data = self._extract_information(results)
        research_sources = self._format_sources(results)
        
        # Assess quality
        quality = self._assess_quality(research_data, results)
        
        self.logger.info(
            f"Research complete. Found {len(results)} sources, quality: {quality.value}"
        )
        
        # Log metrics
        self.log_metric("research_sources_count", len(results))
        self.log_metric("research_quality_score", self._quality_to_score(quality))
        
        return {
            "research_data": research_data,
            "research_sources": research_sources,
            "research_quality": quality,
            "research_timestamp": datetime.now()
        }
    
    def _build_search_query(self, topic: str, requirements: str) -> str:
        """
        Build optimized search query.
        
        Args:
            topic: Main topic
            requirements: Additional user requirements
            
        Returns:
            Optimized search query string
        """
        # Basic query
        query = f"key facts and latest news about {topic}"
        
        # Add requirements if present
        if requirements:
            query += f" {requirements}"
        
        # Add year for recency
        current_year = datetime.now().year
        query += f" {current_year}"
        
        return query
    
    def _search_with_retry(self, query: str) -> List[Dict[str, Any]]:
        """
        Perform search with retry logic.
        
        Args:
            query: Search query
            
        Returns:
            List of search results
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                self.logger.debug(f"Search attempt {attempt + 1}/{self.max_retries}")
                results = self.search_tool.search(query)
                
                if results:
                    return results
                    
            except Exception as e:
                last_error = e
                self.logger.warning(f"Search attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
        
        # If all retries failed
        error_msg = f"Search failed after {self.max_retries} attempts"
        if last_error:
            error_msg += f": {str(last_error)}"
        
        self.logger.error(error_msg)
        
        # Return empty results rather than failing completely
        return []
    
    def _extract_information(self, results: List[Dict[str, Any]]) -> List[str]:
        """
        Extract and format information from search results.
        
        Args:
            results: Raw search results
            
        Returns:
            List of formatted information strings
        """
        if not results:
            return ["No research data available. Please provide information about the topic."]
        
        extracted = []
        
        for idx, result in enumerate(results):
            snippet = result.get("snippet", "")
            title = result.get("title", "")
            
            if snippet:
                # Format with source attribution
                info = f"[Source {idx + 1}] {title}\n{snippet}"
                extracted.append(info)
        
        return extracted
    
    def _format_sources(self, results: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Format source information for citation.
        
        Args:
            results: Raw search results
            
        Returns:
            List of formatted source dictionaries
        """
        sources = []
        
        for result in results:
            source = {
                "url": result.get("link", ""),
                "title": result.get("title", ""),
                "snippet": result.get("snippet", "")
            }
            sources.append(source)
        
        return sources
    
    def _assess_quality(
        self, 
        research_data: List[str], 
        raw_results: List[Dict[str, Any]]
    ) -> ResearchQuality:
        """
        Assess the quality of research results.
        
        Args:
            research_data: Processed research data
            raw_results: Raw search results
            
        Returns:
            ResearchQuality enum value
        """
        # No results = LOW
        if not raw_results:
            return ResearchQuality.LOW
        
        # Check number of sources
        source_count = len(raw_results)
        
        # Check content length
        total_content = " ".join(research_data)
        content_length = len(total_content)
        
        # Scoring logic
        if source_count >= 4 and content_length >= 1000:
            return ResearchQuality.HIGH
        elif source_count >= 2 and content_length >= 500:
            return ResearchQuality.MEDIUM
        else:
            return ResearchQuality.LOW
    
    def _quality_to_score(self, quality: ResearchQuality) -> float:
        """Convert quality enum to numeric score for metrics"""
        mapping = {
            ResearchQuality.HIGH: 1.0,
            ResearchQuality.MEDIUM: 0.6,
            ResearchQuality.LOW: 0.3,
            ResearchQuality.UNKNOWN: 0.0
        }
        return mapping.get(quality, 0.0)

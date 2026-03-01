"""
Search Tools

Provides web search functionality using various providers.
"""

from typing import List, Dict, Any, Optional
import logging
from abc import ABC, abstractmethod

try:
    from duckduckgo_search import DDGS
    DUCKDUCKGO_AVAILABLE = True
except ImportError:
    DUCKDUCKGO_AVAILABLE = False


class SearchProvider(ABC):
    """Abstract base class for search providers"""
    
    @abstractmethod
    def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Execute search and return results"""
        pass


class DuckDuckGoSearch(SearchProvider):
    """DuckDuckGo search provider (free, no API key required)"""
    
    def __init__(self, timeout: int = 10):
        if not DUCKDUCKGO_AVAILABLE:
            raise ImportError(
                "duckduckgo-search not installed. "
                "Install with: pip install duckduckgo-search"
            )
        self.timeout = timeout
        self.logger = logging.getLogger("search.duckduckgo")
    
    def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search using DuckDuckGo.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of search result dictionaries
        """
        try:
            with DDGS() as ddgs:
                results = []
                
                # Perform text search
                for result in ddgs.text(query, max_results=max_results):
                    results.append({
                        "title": result.get("title", ""),
                        "link": result.get("href", ""),
                        "snippet": result.get("body", "")
                    })
                
                self.logger.info(f"Found {len(results)} results for query: {query}")
                return results
                
        except Exception as e:
            self.logger.error(f"DuckDuckGo search failed: {str(e)}")
            return []


class SerperSearch(SearchProvider):
    """Serper.dev search provider (requires API key)"""
    
    def __init__(self, api_key: str, timeout: int = 10):
        import requests
        self.api_key = api_key
        self.timeout = timeout
        self.base_url = "https://google.serper.dev/search"
        self.session = requests.Session()
        self.logger = logging.getLogger("search.serper")
    
    def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search using Serper API.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of search results
        """
        try:
            headers = {
                "X-API-KEY": self.api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "q": query,
                "num": max_results
            }
            
            response = self.session.post(
                self.base_url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for item in data.get("organic", [])[:max_results]:
                results.append({
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", "")
                })
            
            self.logger.info(f"Found {len(results)} results")
            return results
            
        except Exception as e:
            self.logger.error(f"Serper search failed: {str(e)}")
            return []


class TavilySearch(SearchProvider):
    """Tavily AI search provider (requires API key)"""
    
    def __init__(self, api_key: str, timeout: int = 10):
        import requests
        self.api_key = api_key
        self.timeout = timeout
        self.base_url = "https://api.tavily.com/search"
        self.session = requests.Session()
        self.logger = logging.getLogger("search.tavily")
    
    def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search using Tavily API.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of search results
        """
        try:
            payload = {
                "api_key": self.api_key,
                "query": query,
                "max_results": max_results,
                "search_depth": "advanced"
            }
            
            response = self.session.post(
                self.base_url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for item in data.get("results", [])[:max_results]:
                results.append({
                    "title": item.get("title", ""),
                    "link": item.get("url", ""),
                    "snippet": item.get("content", "")
                })
            
            self.logger.info(f"Found {len(results)} results")
            return results
            
        except Exception as e:
            self.logger.error(f"Tavily search failed: {str(e)}")
            return []


class SearchTool:
    """
    Main search tool that delegates to appropriate provider.
    """
    
    def __init__(
        self,
        provider: str = "duckduckgo",
        max_results: int = 5,
        timeout: int = 10,
        api_key: Optional[str] = None
    ):
        """
        Initialize search tool with specified provider.
        
        Args:
            provider: Search provider name (duckduckgo, serper, tavily)
            max_results: Maximum results to return
            timeout: Request timeout in seconds
            api_key: API key for paid providers
        """
        self.max_results = max_results
        self.logger = logging.getLogger("search.tool")
        
        # Initialize provider
        if provider == "duckduckgo":
            self.provider = DuckDuckGoSearch(timeout=timeout)
        elif provider == "serper":
            if not api_key:
                raise ValueError("Serper requires API key")
            self.provider = SerperSearch(api_key=api_key, timeout=timeout)
        elif provider == "tavily":
            if not api_key:
                raise ValueError("Tavily requires API key")
            self.provider = TavilySearch(api_key=api_key, timeout=timeout)
        else:
            raise ValueError(f"Unknown search provider: {provider}")
        
        self.logger.info(f"Initialized {provider} search provider")
    
    def search(self, query: str, max_results: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Execute search query.
        
        Args:
            query: Search query string
            max_results: Override default max results
            
        Returns:
            List of search result dictionaries
        """
        results_limit = max_results or self.max_results
        
        self.logger.debug(f"Searching for: {query} (max_results={results_limit})")
        
        results = self.provider.search(query, max_results=results_limit)
        
        return results

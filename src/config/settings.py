"""
Configuration Management

Handles environment variables and application settings.
"""

from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # LLM Configuration
    llm_provider: str = Field(default="ollama", description="LLM provider to use")
    llm_model: str = Field(default="llama3", description="Model name")
    llm_temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    llm_max_tokens: int = Field(default=2000, gt=0)
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    
    # Ollama Configuration
    ollama_base_url: str = Field(default="http://localhost:11434")
    
    # Search Configuration
    search_provider: str = Field(default="duckduckgo")
    search_max_results: int = Field(default=5, ge=1, le=20)
    search_timeout: int = Field(default=10, ge=1)
    
    # Optional Search APIs
    serper_api_key: Optional[str] = None
    tavily_api_key: Optional[str] = None
    
    # Application Configuration
    app_name: str = Field(default="Multi-Agent Blog Generator")
    app_version: str = Field(default="1.0.0")
    environment: str = Field(default="development")
    
    # Logging Configuration
    log_level: str = Field(default="INFO")
    log_file: str = Field(default="logs/app.log")
    log_format: str = Field(default="json")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000, ge=1024, le=65535)
    api_reload: bool = Field(default=True)
    api_workers: int = Field(default=1, ge=1)
    
    # CORS Configuration
    cors_origins: List[str] = Field(default=["http://localhost:3000"])
    cors_allow_credentials: bool = Field(default=True)
    
    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True)
    rate_limit_requests: int = Field(default=100)
    rate_limit_period: int = Field(default=3600)
    
    # Agent Configuration
    researcher_retries: int = Field(default=3, ge=1)
    writer_min_words: int = Field(default=300, ge=100)
    editor_enabled: bool = Field(default=True)
    
    # Cache Configuration
    cache_enabled: bool = Field(default=True)
    cache_ttl: int = Field(default=3600)
    cache_max_size: int = Field(default=1000)
    
    # Performance
    max_concurrent_agents: int = Field(default=5, ge=1)
    agent_timeout: int = Field(default=300, ge=30)
    
    # Database (optional)
    database_url: Optional[str] = Field(default="sqlite:///./data/app.db")
    
    # Monitoring (optional)
    sentry_dsn: Optional[str] = None
    prometheus_enabled: bool = Field(default=False)
    
    @validator("llm_provider")
    def validate_llm_provider(cls, v):
        allowed = ["ollama", "openai"]
        if v not in allowed:
            raise ValueError(f"LLM provider must be one of {allowed}")
        return v
    
    @validator("search_provider")
    def validate_search_provider(cls, v):
        allowed = ["duckduckgo", "serper", "tavily"]
        if v not in allowed:
            raise ValueError(f"Search provider must be one of {allowed}")
        return v
    
    @validator("environment")
    def validate_environment(cls, v):
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"Environment must be one of {allowed}")
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v):
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in allowed:
            raise ValueError(f"Log level must be one of {allowed}")
        return v_upper
    
    def validate_api_keys(self) -> List[str]:
        """Validate that required API keys are present based on configuration"""
        missing = []
        
        if self.llm_provider == "openai" and not self.openai_api_key:
            missing.append("OPENAI_API_KEY")
        
        if self.search_provider == "serper" and not self.serper_api_key:
            missing.append("SERPER_API_KEY")
            
        if self.search_provider == "tavily" and not self.tavily_api_key:
            missing.append("TAVILY_API_KEY")
        
        return missing
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses lru_cache to ensure settings are only loaded once.
    """
    return Settings()


def validate_configuration() -> tuple[bool, Optional[str]]:
    """
    Validate the complete configuration.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        settings = get_settings()
        
        # Check for missing API keys
        missing_keys = settings.validate_api_keys()
        if missing_keys:
            return False, f"Missing required API keys: {', '.join(missing_keys)}"
        
        # Validate log directory exists
        log_dir = os.path.dirname(settings.log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        return True, None
        
    except Exception as e:
        return False, f"Configuration error: {str(e)}"


# Export convenience function
def get_llm_config() -> dict:
    """Get LLM-specific configuration"""
    settings = get_settings()
    return {
        "provider": settings.llm_provider,
        "model": settings.llm_model,
        "temperature": settings.llm_temperature,
        "max_tokens": settings.llm_max_tokens,
        "api_key": settings.openai_api_key,
        "base_url": settings.ollama_base_url
    }


def get_search_config() -> dict:
    """Get search-specific configuration"""
    settings = get_settings()
    return {
        "provider": settings.search_provider,
        "max_results": settings.search_max_results,
        "timeout": settings.search_timeout,
        "serper_api_key": settings.serper_api_key,
        "tavily_api_key": settings.tavily_api_key
    }

"""
LLM Provider Abstraction

Provides unified interface for different LLM providers.
"""

from typing import Optional
from abc import ABC, abstractmethod
import logging

from src.config import get_llm_config


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """Generate text completion"""
        pass


class OllamaProvider(BaseLLMProvider):
    """Ollama local LLM provider"""
    
    def __init__(self, model: str, base_url: str):
        from langchain_ollama import ChatOllama
        
        self.model = model
        self.base_url = base_url
        self.llm = ChatOllama(
            model=model,
            base_url=base_url
        )
        self.logger = logging.getLogger("llm.ollama")
        self.logger.info(f"Initialized Ollama with model: {model}")
    
    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """
        Generate completion using Ollama.
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        try:
            # Update temperature for this call
            self.llm.temperature = temperature
            
            response = self.llm.invoke(prompt)
            return response.content
            
        except Exception as e:
            self.logger.error(f"Ollama generation failed: {str(e)}")
            raise


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider"""
    
    def __init__(self, model: str, api_key: str):
        from langchain_openai import ChatOpenAI
        
        self.model = model
        self.llm = ChatOpenAI(
            model=model,
            api_key=api_key
        )
        self.logger = logging.getLogger("llm.openai")
        self.logger.info(f"Initialized OpenAI with model: {model}")
    
    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """
        Generate completion using OpenAI.
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        try:
            # Update parameters for this call
            self.llm.temperature = temperature
            self.llm.max_tokens = max_tokens
            
            response = self.llm.invoke(prompt)
            return response.content
            
        except Exception as e:
            self.logger.error(f"OpenAI generation failed: {str(e)}")
            raise


class LLMProvider:
    """
    Main LLM provider that delegates to appropriate implementation.
    """
    
    def __init__(self, config: Optional[dict] = None):
        """
        Initialize LLM provider based on configuration.
        
        Args:
            config: Optional configuration dict, otherwise uses global settings
        """
        if config is None:
            config = get_llm_config()
        
        self.logger = logging.getLogger("llm.provider")
        
        provider_type = config["provider"]
        model = config["model"]
        
        # Initialize appropriate provider
        if provider_type == "ollama":
            base_url = config.get("base_url", "http://localhost:11434")
            self.provider = OllamaProvider(model=model, base_url=base_url)
            
        elif provider_type == "openai":
            api_key = config.get("api_key")
            if not api_key:
                raise ValueError("OpenAI API key required but not provided")
            self.provider = OpenAIProvider(model=model, api_key=api_key)
            
        else:
            raise ValueError(f"Unknown LLM provider: {provider_type}")
        
        self.default_temperature = config.get("temperature", 0.7)
        self.default_max_tokens = config.get("max_tokens", 2000)
        
        self.logger.info(f"LLM Provider initialized: {provider_type} ({model})")
    
    def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate text completion.
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature (uses default if None)
            max_tokens: Max tokens to generate (uses default if None)
            
        Returns:
            Generated text string
        """
        temp = temperature if temperature is not None else self.default_temperature
        tokens = max_tokens if max_tokens is not None else self.default_max_tokens
        
        self.logger.debug(f"Generating with temp={temp}, max_tokens={tokens}")
        
        return self.provider.generate(
            prompt=prompt,
            temperature=temp,
            max_tokens=tokens
        )

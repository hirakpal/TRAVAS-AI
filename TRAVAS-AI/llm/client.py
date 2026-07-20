"""LLM Client Factory

Creates and manages LLM client instances for different providers.
"""

from typing import Optional, List, Dict
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients"""

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    @abstractmethod
    def call(
        self,
        messages: List[Dict],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> str:
        """Call the LLM and get response"""
        pass


class OpenAIClient(BaseLLMClient):
    """OpenAI API Client"""

    def __init__(self, api_key: str, model: str = "gpt-4-turbo"):
        super().__init__(api_key, model)
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
        except ImportError:
            raise ImportError("openai package not installed. Install with: pip install openai")

    def call(
        self,
        messages: List[Dict],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> str:
        """Call OpenAI API"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude API Client"""

    def __init__(self, api_key: str, model: str = "claude-3-opus-20240229"):
        super().__init__(api_key, model)
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)
        except ImportError:
            raise ImportError("anthropic package not installed. Install with: pip install anthropic")

    def call(
        self,
        messages: List[Dict],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> str:
        """Call Anthropic API"""
        try:
            # Extract system prompt if present
            system_prompt = None
            if messages and messages[0].get("role") == "system":
                system_prompt = messages[0]["content"]
                messages = messages[1:]

            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system_prompt if system_prompt else "",
                messages=messages,
                temperature=temperature,
                **kwargs
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise


class GeminiClient(BaseLLMClient):
    """Google Gemini API Client"""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        super().__init__(api_key, model)
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.client = genai
        except ImportError:
            raise ImportError("google-generativeai package not installed. Install with: pip install google-generativeai")

    def call(
        self,
        messages: List[Dict],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> str:
        """Call Gemini API"""
        try:
            # Extract system instruction
            system_instruction = None
            if messages and messages[0].get("role") == "system":
                system_instruction = messages[0]["content"]
                messages = messages[1:]

            model = self.client.GenerativeModel(
                model_name=self.model,
                system_instruction=system_instruction
            )

            chat = model.start_chat()
            response = chat.send_message(
                messages[-1]["content"] if messages else ""
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise


class LLMClient:
    """Factory class for creating LLM clients"""

    _clients = {
        "openai": OpenAIClient,
        "anthropic": AnthropicClient,
        "claude": AnthropicClient,  # Alias
        "gemini": GeminiClient,
    }

    def __new__(
        cls,
        provider: str,
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ) -> BaseLLMClient:
        """
        Create an LLM client for the specified provider.

        Args:
            provider: LLM provider (openai, anthropic, gemini)
            api_key: API key for the provider
            model: Model name to use

        Returns:
            Initialized LLM client instance
        """
        provider = provider.lower()

        if provider not in cls._clients:
            raise ValueError(
                f"Unknown LLM provider: {provider}. "
                f"Supported: {', '.join(cls._clients.keys())}"
            )

        # Get default model if not specified
        if not model:
            from config.settings import Settings
            model = Settings.get_llm_model(provider)

        # Get API key from parameter or environment
        if not api_key:
            from config.settings import Settings
            api_key = Settings.get_llm_api_key(provider)

        if not api_key:
            raise ValueError(f"API key not provided for provider: {provider}")

        client_class = cls._clients[provider]
        logger.info(f"Creating {provider} client with model {model}")

        return client_class(api_key=api_key, model=model)

    @classmethod
    def register_provider(cls, name: str, client_class: type) -> None:
        """
        Register a custom LLM provider.

        Args:
            name: Provider name
            client_class: Client class (must inherit from BaseLLMClient)
        """
        if not issubclass(client_class, BaseLLMClient):
            raise TypeError(f"{client_class} must inherit from BaseLLMClient")
        cls._clients[name.lower()] = client_class
        logger.info(f"Registered LLM provider: {name}")

    @classmethod
    def get_available_providers(cls) -> list:
        """Get list of available LLM providers"""
        return list(cls._clients.keys())

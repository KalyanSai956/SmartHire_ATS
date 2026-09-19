from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class LLMProviderError(Exception):
    """Base exception for LLM provider failures."""


class LLMProviderConfigurationError(LLMProviderError):
    """Raised when a provider is not configured correctly."""


class LLMProviderResponseError(LLMProviderError):
    """Raised when a provider returns an invalid response."""


class BaseLLMProvider(ABC):
    """
    Common interface for all LLM providers.

    Interview Arena should communicate with this interface,
    not directly with Groq/OpenAI/etc.
    """

    provider_name: str = "unknown"

    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, str]],
        *,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """
        Generate a normal text response.
        """
        raise NotImplementedError

    @abstractmethod
    async def generate_json(
        self,
        messages: List[Dict[str, str]],
        *,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1500,
    ) -> Dict[str, Any]:
        """
        Generate and parse a structured JSON response.
        """
        raise NotImplementedError

    @abstractmethod
    def is_configured(self) -> bool:
        """
        Return whether the provider has the required configuration.
        """
        raise NotImplementedError

    def get_provider_info(self) -> Dict[str, Any]:
        return {
            "provider": self.provider_name,
            "configured": self.is_configured(),
        }
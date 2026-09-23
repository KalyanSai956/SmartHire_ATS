from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


# ============================================================
# EXCEPTIONS
# ============================================================


class LLMProviderError(Exception):
    """Base exception for LLM provider errors."""


class LLMProviderConfigurationError(LLMProviderError):
    """Raised when an LLM provider is not configured correctly."""


class LLMProviderResponseError(LLMProviderError):
    """Raised when an LLM provider returns an invalid response."""


# ============================================================
# USAGE
# ============================================================


@dataclass
class LLMUsage:
    """
    Token usage returned by an LLM provider.
    """

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


# ============================================================
# RESPONSE
# ============================================================


@dataclass
class LLMResponse:
    """
    Standard response returned by every SmartHire LLM provider.

    content:
        Raw text returned by the provider.

    parsed_json:
        Parsed JSON when generate_json() is used.

    usage:
        Token usage reported by the provider.
    """

    content: str

    usage: LLMUsage

    provider: str

    model: str

    parsed_json: Optional[Dict[str, Any]] = None


# ============================================================
# BASE PROVIDER
# ============================================================


class BaseLLMProvider(ABC):

    provider_name: str = "unknown"

    # --------------------------------------------------------
    # TEXT GENERATION
    # --------------------------------------------------------

    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, str]],
        *,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        raise NotImplementedError

    # --------------------------------------------------------
    # JSON GENERATION
    # --------------------------------------------------------

    @abstractmethod
    async def generate_json(
        self,
        messages: List[Dict[str, str]],
        *,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1500,
    ) -> LLMResponse:
        raise NotImplementedError

    # --------------------------------------------------------
    # CONFIGURATION
    # --------------------------------------------------------

    @abstractmethod
    def is_configured(self) -> bool:
        raise NotImplementedError

    # --------------------------------------------------------
    # PROVIDER INFO
    # --------------------------------------------------------

    def get_provider_info(self) -> Dict[str, Any]:
        return {
            "provider": self.provider_name,
            "configured": self.is_configured(),
        }
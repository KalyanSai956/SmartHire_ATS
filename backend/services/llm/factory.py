import logging
from typing import Optional

from backend.services.llm.base import (
    BaseLLMProvider,
    LLMProviderConfigurationError,
)
from backend.services.llm.groq_provider import GroqProvider


logger = logging.getLogger("smarthire.llm.factory")


SUPPORTED_PROVIDERS = {
    "groq",
}


def create_llm_provider(
    provider: str = "groq",
    *,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> BaseLLMProvider:

    normalized_provider = (
        provider.strip().lower()
    )

    if normalized_provider not in SUPPORTED_PROVIDERS:
        raise LLMProviderConfigurationError(
            f"Unsupported LLM provider: {provider}. "
            f"Supported providers: "
            f"{', '.join(sorted(SUPPORTED_PROVIDERS))}"
        )

    if normalized_provider == "groq":
        return GroqProvider(
            api_key=api_key,
            default_model=model,
        )

    raise LLMProviderConfigurationError(
        f"No implementation found for provider: "
        f"{normalized_provider}"
    )
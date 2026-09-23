from __future__ import annotations

import logging
from typing import Optional

from backend.services.llm.base import (
    BaseLLMProvider,
    LLMProviderConfigurationError,
)

from backend.services.llm.groq_provider import (
    GroqProvider,
)

from backend.services.llm.openai_provider import (
    OpenAIProvider,
)

from backend.services.llm.anthropic_provider import (
    AnthropicProvider,
)

from backend.services.llm.google_provider import (
    GoogleProvider,
)


logger = logging.getLogger(
    "smarthire.llm.factory"
)


SUPPORTED_PROVIDERS = {
    "groq",
    "openai",
    "anthropic",
    "google",
}


def create_llm_provider(
    provider: str = "groq",
    *,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> BaseLLMProvider:

    normalized_provider = (
        provider or ""
    ).strip().lower()

    if normalized_provider not in (
        SUPPORTED_PROVIDERS
    ):

        raise LLMProviderConfigurationError(
            (
                f"Unsupported LLM provider: "
                f"{provider}. "
                f"Supported providers: "
                f"{', '.join(sorted(SUPPORTED_PROVIDERS))}"
            )
        )

    if normalized_provider == "groq":

        return GroqProvider(
            api_key=api_key,
            default_model=model,
        )

    if normalized_provider == "openai":

        return OpenAIProvider(
            api_key=api_key,
            default_model=model,
        )

    if normalized_provider == "anthropic":

        return AnthropicProvider(
            api_key=api_key,
            default_model=model,
        )

    if normalized_provider == "google":

        return GoogleProvider(
            api_key=api_key,
            default_model=model,
        )

    raise LLMProviderConfigurationError(
        f"Could not create provider: {provider}"
    )
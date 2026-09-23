from __future__ import annotations

from typing import Optional

from backend.database.supabase_db import get_user_llm_credential
from backend.services.llm.credentials import decrypt_api_key
from backend.services.llm.gateway import LLMGateway


SUPPORTED_PROVIDERS = {
    "groq",
    "openai",
    "anthropic",
    "google",
}


DEFAULT_PROVIDER_PRIORITY = [
    "groq",
    "openai",
    "anthropic",
    "google",
]


async def create_user_llm_gateway(
    *,
    user_id: str,
    feature: str,
    provider: Optional[str] = None,
    usage_source: Optional[str] = None,
    model: Optional[str] = None,
) -> LLMGateway:
    """
    Create an LLM gateway for a user.

    Provider selection:

    1. Explicit provider:
       Use exactly that provider's BYOK credential.

    2. No explicit provider:
       Automatically select the first configured BYOK provider.

    3. No BYOK:
       Fall back to the platform Groq provider.
    """

    selected_provider = (
        provider.strip().lower()
        if isinstance(provider, str) and provider.strip()
        else None
    )

    # ---------------------------------------------------------
    # Explicit provider selection
    # ---------------------------------------------------------
    if selected_provider:

        if selected_provider not in SUPPORTED_PROVIDERS:
            raise ValueError(
                f"Unsupported LLM provider: {selected_provider}"
            )

        credential = await get_user_llm_credential(
            user_id=user_id,
            provider=selected_provider,
        )

        if not credential:
            raise ValueError(
                f"No API key is configured for provider "
                f"'{selected_provider}'. "
                f"Please connect it in AI Settings."
            )

        api_key = decrypt_api_key(
            credential["encrypted_api_key"]
        )

        selected_model = (
            model
            or credential.get("model")
            or None
        )

        return LLMGateway(
            provider=selected_provider,
            api_key=api_key,
            model=selected_model,
            user_id=user_id,
            feature=feature,
            usage_source=usage_source or "byok",
        )

    # ---------------------------------------------------------
    # Automatic BYOK selection
    # ---------------------------------------------------------
    for candidate in DEFAULT_PROVIDER_PRIORITY:

        credential = await get_user_llm_credential(
            user_id=user_id,
            provider=candidate,
        )

        if not credential:
            continue

        api_key = decrypt_api_key(
            credential["encrypted_api_key"]
        )

        selected_model = (
            model
            or credential.get("model")
            or None
        )

        return LLMGateway(
            provider=candidate,
            api_key=api_key,
            model=selected_model,
            user_id=user_id,
            feature=feature,
            usage_source=usage_source or "byok",
        )

    # ---------------------------------------------------------
    # Platform provider fallback
    # ---------------------------------------------------------
    return LLMGateway(
        provider="groq",
        api_key=None,
        model=model,
        user_id=user_id,
        feature=feature,
        usage_source=usage_source or "platform",
    )
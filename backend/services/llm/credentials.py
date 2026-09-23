from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from cryptography.fernet import (
    Fernet,
    InvalidToken,
)

from backend.core.config import (
    LLM_CREDENTIAL_ENCRYPTION_KEY,
)


logger = logging.getLogger(
    "smarthire.llm.credentials"
)


SUPPORTED_BYOK_PROVIDERS = {
    "groq",
    "openai",
    "anthropic",
    "google",
}


# ============================================================
# ENCRYPTION
# ============================================================

def _get_fernet() -> Fernet:

    key = (
        LLM_CREDENTIAL_ENCRYPTION_KEY
        or ""
    ).strip()

    if not key:

        raise RuntimeError(
            "LLM_CREDENTIAL_ENCRYPTION_KEY "
            "is not configured."
        )

    try:

        return Fernet(
            key.encode()
        )

    except Exception as exc:

        raise RuntimeError(
            "Invalid LLM credential encryption key."
        ) from exc


def encrypt_api_key(
    api_key: str,
) -> str:

    api_key = (
        api_key or ""
    ).strip()

    if not api_key:

        raise ValueError(
            "API key cannot be empty."
        )

    fernet = _get_fernet()

    encrypted = fernet.encrypt(
        api_key.encode()
    )

    return encrypted.decode()


def decrypt_api_key(
    encrypted_api_key: str,
) -> str:

    encrypted_api_key = (
        encrypted_api_key or ""
    ).strip()

    if not encrypted_api_key:

        raise ValueError(
            "Encrypted API key is empty."
        )

    fernet = _get_fernet()

    try:

        decrypted = fernet.decrypt(
            encrypted_api_key.encode()
        )

        return decrypted.decode()

    except InvalidToken as exc:

        raise RuntimeError(
            "Could not decrypt stored API key."
        ) from exc


# ============================================================
# VALIDATION
# ============================================================

def validate_provider(
    provider: str,
) -> str:

    normalized = (
        provider or ""
    ).strip().lower()

    if normalized not in SUPPORTED_BYOK_PROVIDERS:

        raise ValueError(
            (
                "Unsupported LLM provider. "
                "Supported providers: "
                "Groq, OpenAI, Anthropic, Google."
            )
        )

    return normalized


def mask_api_key(
    api_key: str,
) -> str:

    api_key = (
        api_key or ""
    ).strip()

    if len(api_key) <= 4:

        return "••••"

    return (
        "••••••••"
        + api_key[-4:]
    )


def get_last4(
    api_key: str,
) -> str:

    api_key = (
        api_key or ""
    ).strip()

    return (
        api_key[-4:]
        if len(api_key) >= 4
        else api_key
    )
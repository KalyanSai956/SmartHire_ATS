from __future__ import annotations

import logging
import uuid
from typing import Optional

from backend.database.supabase_db import save_llm_usage
from backend.services.llm.base import LLMUsage


logger = logging.getLogger(__name__)


async def record_llm_usage(
    *,
    usage: LLMUsage,
    provider: str,
    model: str,
    feature: str,
    user_id: Optional[str] = None,
    usage_source: str = "platform",
    request_id: Optional[str] = None,
) -> None:
    """
    Persist LLM token usage.

    Usage tracking must never break the actual AI request.
    If persistence fails, log the error and continue.
    """

    if user_id is None:
        logger.warning(
            "Skipping LLM usage persistence because user_id is missing."
        )
        return

    resolved_request_id = request_id or str(uuid.uuid4())

    try:
        await save_llm_usage(
            user_id=user_id,
            provider=provider,
            model=model,
            feature=feature,
            usage_source=usage_source,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            total_tokens=usage.total_tokens,
            request_id=resolved_request_id,
        )

    except Exception:
        logger.exception(
            "Failed to persist LLM usage "
            "(provider=%s, model=%s, feature=%s, user_id=%s)",
            provider,
            model,
            feature,
            user_id,
        )
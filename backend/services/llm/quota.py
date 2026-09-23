from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Literal

from backend.database.supabase_db import (
    count_user_resume_analyses,
    get_user_llm_credentials,
)


logger = logging.getLogger("smarthire.llm.quota")


# ============================================================
# FREE QUOTA CONFIGURATION
# ============================================================

FREE_RESUME_ANALYSES = 3


QuotaFeature = Literal[
    "resume_analysis",
]


# ============================================================
# EXCEPTION
# ============================================================

class FreeQuotaExceededError(Exception):
    """
    Raised when a user has exhausted the free platform quota.
    """

    def __init__(
        self,
        *,
        feature: QuotaFeature,
        used: int,
        limit: int,
    ):
        self.feature = feature
        self.used = used
        self.limit = limit

        super().__init__(
            f"Free {feature} quota exhausted."
        )


# ============================================================
# RESULT
# ============================================================

@dataclass
class QuotaStatus:
    feature: QuotaFeature
    used: int
    limit: int

    @property
    def remaining(self) -> int:
        return max(
            self.limit - self.used,
            0,
        )

    @property
    def exhausted(self) -> bool:
        return self.used >= self.limit

    def to_dict(self) -> dict:
        return {
            "feature": self.feature,
            "used": self.used,
            "limit": self.limit,
            "remaining": self.remaining,
            "exhausted": self.exhausted,
        }


# ============================================================
# CHECK WHETHER USER HAS BYOK
# ============================================================

async def user_has_byok(
    user_id: str,
) -> bool:

    credentials = await get_user_llm_credentials(
        user_id
    )

    return bool(credentials)


# ============================================================
# GET QUOTA STATUS
# ============================================================

async def get_quota_status(
    user_id: str,
    feature: QuotaFeature,
) -> QuotaStatus:

    if feature == "resume_analysis":

        used = await count_user_resume_analyses(
            user_id
        )

        limit = FREE_RESUME_ANALYSES

    else:

        raise ValueError(
            f"Unsupported quota feature: {feature}"
        )

    return QuotaStatus(
        feature=feature,
        used=used,
        limit=limit,
    )


# ============================================================
# REQUIRE FREE QUOTA
# ============================================================

async def require_free_quota(
    user_id: str,
    feature: QuotaFeature,
) -> QuotaStatus:

    quota = await get_quota_status(
        user_id=user_id,
        feature=feature,
    )

    logger.info(
        "Quota check user=%s feature=%s used=%s limit=%s remaining=%s",
        user_id,
        feature,
        quota.used,
        quota.limit,
        quota.remaining,
    )

    if quota.exhausted:

        raise FreeQuotaExceededError(
            feature=feature,
            used=quota.used,
            limit=quota.limit,
        )

    return quota


# ============================================================
# REQUIRE FREE QUOTA OR BYOK
# ============================================================

async def require_free_quota_or_byok(
    user_id: str,
    feature: QuotaFeature,
) -> QuotaStatus:

    # --------------------------------------------------------
    # If the user has ANY configured BYOK provider,
    # they are allowed to continue even after free quota.
    # --------------------------------------------------------

    if await user_has_byok(user_id):

        logger.info(
            "BYOK detected for user=%s feature=%s; "
            "free quota does not block request.",
            user_id,
            feature,
        )

        return await get_quota_status(
            user_id=user_id,
            feature=feature,
        )

    # --------------------------------------------------------
    # No BYOK → enforce the 3-use platform quota.
    # --------------------------------------------------------

    return await require_free_quota(
        user_id=user_id,
        feature=feature,
    )
from fastapi import APIRouter, Depends

from backend.api.auth import get_current_user
from backend.database.supabase_db import get_user_llm_credentials
from backend.services.llm.quota import get_quota_status


router = APIRouter(
    prefix="/api/v1/usage",
    tags=["Usage"],
)


@router.get("/quota")
async def get_usage_quota(
    user_id: str = Depends(get_current_user),
):
    resume_quota = await get_quota_status(
        user_id=user_id,
        feature="resume_analysis",
    )

    credentials = await get_user_llm_credentials(
        user_id=user_id
    )

    connected_providers = [
        {
            "provider": item["provider"],
            "model": item.get("model"),
            "key_last4": item.get("key_last4"),
        }
        for item in credentials
    ]

    return {
        "resume": {
            "used": resume_quota.used,
            "limit": resume_quota.limit,
            "remaining": resume_quota.remaining,
        },
        "byok": {
            "connected": len(connected_providers) > 0,
            "providers": connected_providers,
        },
    }
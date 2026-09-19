import logging
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from backend.api.auth import get_current_user
from backend.models.schemas import (
    CareerProfileResponse,
    CareerProfileUpdate,
)

logger = logging.getLogger("ats_resume_scorer")

router = APIRouter(
    prefix="/api/v1/profile",
    tags=["Profile"],
)


@router.get("", response_model=CareerProfileResponse)
async def get_profile(
    user_id: str = Depends(get_current_user),
):
    """
    Return the career profile for the currently authenticated user.
    """

    from backend.database.supabase_db import get_user_profile

    profile = await get_user_profile(user_id)

    if profile is None:
        return CareerProfileResponse(
            user_id=user_id,
            username="",
            skills=[],
            target_roles=[],
            experience="",
            resume_filename=None,
            onboarding_completed=False,
        )

    return CareerProfileResponse(
        user_id=user_id,
        username=profile.get("username") or "",
        skills=profile.get("skills") or [],
        target_roles=profile.get("target_roles") or [],
        experience=profile.get("experience") or "",
        resume_filename=profile.get("resume_filename"),
        onboarding_completed=bool(
            profile.get("onboarding_completed", False)
        ),
    )


@router.put("", response_model=CareerProfileResponse)
async def update_profile(
    data: CareerProfileUpdate,
    user_id: str = Depends(get_current_user),
):
    """
    Create or update the authenticated user's career profile.
    """

    username = data.username.strip()
    experience = data.experience.strip()

    if not username:
        raise HTTPException(
            status_code=400,
            detail="Username is required.",
        )

    if len(username) < 2:
        raise HTTPException(
            status_code=400,
            detail="Username must contain at least 2 characters.",
        )

    skills = [
        skill.strip()
        for skill in data.skills
        if skill and skill.strip()
    ]

    target_roles = [
        role.strip()
        for role in data.target_roles
        if role and role.strip()
    ]

    if not skills:
        raise HTTPException(
            status_code=400,
            detail="Please add at least one skill.",
        )

    if not target_roles:
        raise HTTPException(
            status_code=400,
            detail="Please add at least one target role.",
        )

    from backend.database.supabase_db import upsert_user_profile

    profile = await upsert_user_profile(
        user_id=user_id,
        username=username,
        skills=skills,
        target_roles=target_roles,
        experience=experience,
        onboarding_completed=False,
    )

    if profile is None:
        raise HTTPException(
            status_code=500,
            detail="Could not save your career profile.",
        )

    return CareerProfileResponse(
        user_id=user_id,
        username=profile.get("username") or username,
        skills=profile.get("skills") or skills,
        target_roles=profile.get("target_roles") or target_roles,
        experience=profile.get("experience") or experience,
        resume_filename=profile.get("resume_filename"),
        onboarding_completed=bool(
            profile.get("onboarding_completed", False)
        ),
    )


@router.post(
    "/resume",
    response_model=CareerProfileResponse,
)
async def upload_profile_resume(
    resume: UploadFile = File(
        ...,
        description="Resume file — PDF or DOCX, max 5 MB",
    ),
    user_id: str = Depends(get_current_user),
):
    """
    Parse and save the user's resume as part of onboarding.
    """

    filename = resume.filename or "resume"

    allowed_extensions = {".pdf", ".docx"}
    extension = ""

    if "." in filename:
        extension = "." + filename.rsplit(".", 1)[1].lower()

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX resume files are supported.",
        )

    file_bytes = await resume.read()

    if not file_bytes:
        raise HTTPException(
            status_code=400,
            detail="The uploaded resume is empty.",
        )

    if len(file_bytes) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="Resume must be smaller than 5 MB.",
        )

    try:
        from backend.services.resume_parser import parse_resume_file

        resume_text, _metadata = parse_resume_file(
            file_bytes,
            filename,
        )

    except Exception as exc:
        logger.exception(
            "Profile resume parsing failed"
        )

        raise HTTPException(
            status_code=422,
            detail=f"Could not read or parse the resume: {exc}",
        )

    if not resume_text.strip():
        raise HTTPException(
            status_code=422,
            detail="No readable text was found in the resume.",
        )

    from backend.database.supabase_db import (
        update_profile_resume,
    )

    profile = await update_profile_resume(
        user_id=user_id,
        filename=filename,
        resume_text=resume_text,
    )

    if profile is None:
        raise HTTPException(
            status_code=500,
            detail="Could not save the resume.",
        )

    return CareerProfileResponse(
        user_id=user_id,
        username=profile.get("username") or "",
        skills=profile.get("skills") or [],
        target_roles=profile.get("target_roles") or [],
        experience=profile.get("experience") or "",
        resume_filename=profile.get("resume_filename"),
        onboarding_completed=bool(
            profile.get("onboarding_completed", False)
        ),
    )


@router.post(
    "/complete",
    response_model=CareerProfileResponse,
)
async def complete_onboarding(
    user_id: str = Depends(get_current_user),
):
    """
    Mark onboarding as completed.

    A profile and resume must exist before completion.
    """

    from backend.database.supabase_db import (
        get_user_profile,
        mark_onboarding_completed,
    )

    profile = await get_user_profile(user_id)

    if profile is None:
        raise HTTPException(
            status_code=400,
            detail="Career profile has not been created yet.",
        )

    if not profile.get("username"):
        raise HTTPException(
            status_code=400,
            detail="Username is required.",
        )

    if not profile.get("skills"):
        raise HTTPException(
            status_code=400,
            detail="At least one skill is required.",
        )

    if not profile.get("target_roles"):
        raise HTTPException(
            status_code=400,
            detail="At least one target role is required.",
        )

    if not profile.get("resume_text"):
        raise HTTPException(
            status_code=400,
            detail="Please upload your resume before completing onboarding.",
        )

    updated = await mark_onboarding_completed(user_id)

    if updated is None:
        raise HTTPException(
            status_code=500,
            detail="Could not complete onboarding.",
        )

    return CareerProfileResponse(
        user_id=user_id,
        username=updated.get("username") or "",
        skills=updated.get("skills") or [],
        target_roles=updated.get("target_roles") or [],
        experience=updated.get("experience") or "",
        resume_filename=updated.get("resume_filename"),
        onboarding_completed=True,
    )
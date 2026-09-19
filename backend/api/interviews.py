import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from backend.api.auth import get_current_user
from backend.database.supabase_db import (
    supabase_rest_get,
    supabase_rest_post,
    supabase_rest_patch,
)
from backend.services.interview_question_generator import (
    generate_interview_questions,
)
import httpx

logger = logging.getLogger("smarthire.interviews")


router = APIRouter(
    prefix="/api/v1/interviews",
    tags=["Interviews"],
)


# ============================================================
# CONSTANTS
# ============================================================

VALID_INTERVIEW_TYPES = {
    "technical",
    "behavioral",
    "mixed",
}

VALID_DIFFICULTIES = {
    "easy",
    "medium",
    "hard",
}

VALID_STATUSES = {
    "not_started",
    "active",
    "paused",
    "completed",
    "abandoned",
}


# ============================================================
# SCHEMAS
# ============================================================

class InterviewConfiguration(BaseModel):
    question_count: int = Field(
        default=10,
        ge=5,
        le=20,
        description="Number of interview questions",
    )

    duration_minutes: int = Field(
        default=30,
        ge=10,
        le=90,
        description="Maximum interview duration in minutes",
    )

    focus_areas: List[str] = Field(
        default_factory=list,
        description="Skills or topics the interview should focus on",
    )

    include_coding: bool = Field(
        default=False,
        description="Whether coding questions should be included",
    )

    include_system_design: bool = Field(
        default=False,
        description="Whether system design questions should be included",
    )

    @field_validator("focus_areas")
    @classmethod
    def validate_focus_areas(cls, value: List[str]) -> List[str]:
        cleaned: List[str] = []

        for item in value:
            item = item.strip()

            if not item:
                continue

            if len(item) > 100:
                raise ValueError(
                    "Each focus area must be 100 characters or less."
                )

            if item.lower() not in [
                existing.lower() for existing in cleaned
            ]:
                cleaned.append(item)

        if len(cleaned) > 10:
            raise ValueError(
                "You can specify a maximum of 10 focus areas."
            )

        return cleaned


class InterviewSessionCreate(BaseModel):
    role: str = Field(
        ...,
        min_length=2,
        max_length=200,
    )

    job_description: str = Field(
        default="",
        max_length=20000,
    )

    interview_type: str = Field(
        default="mixed",
    )

    difficulty: str = Field(
        default="medium",
    )

    configuration: InterviewConfiguration = Field(
        default_factory=InterviewConfiguration,
    )


class InterviewSessionResponse(BaseModel):
    id: str
    user_id: str

    role: str
    job_description: str

    interview_type: str
    difficulty: str

    status: str

    current_question_number: int

    configuration: dict = Field(
        default_factory=dict
    )

    started_at: Any = None
    completed_at: Any = None

    created_at: Any
    updated_at: Any


# ============================================================
# UTILITY
# ============================================================

def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

class InterviewQuestionResponse(BaseModel):
    id: str
    session_id: str
    question: str
    category: str
    difficulty: str
    skill: str
    expected_topics: List[str] = Field(
        default_factory=list
    )
    question_order: int
    created_at: Any = None
class InterviewQuestionGenerationResponse(BaseModel):
    session_id: str
    generated_count: int
    questions: List[InterviewQuestionResponse]
# ============================================================
# VALIDATION
# ============================================================

def _validate_create_payload(
    payload: InterviewSessionCreate,
) -> Dict[str, Any]:

    interview_type = payload.interview_type.strip().lower()
    difficulty = payload.difficulty.strip().lower()

    if interview_type not in VALID_INTERVIEW_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Invalid interview_type. "
                "Allowed values: technical, behavioral, mixed."
            ),
        )

    if difficulty not in VALID_DIFFICULTIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Invalid difficulty. "
                "Allowed values: easy, medium, hard."
            ),
        )

    # Behavioral interviews cannot contain technical formats.
    if interview_type == "behavioral":

        if payload.configuration.include_coding:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Coding questions cannot be enabled "
                    "for a behavioral interview."
                ),
            )

        if payload.configuration.include_system_design:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "System design cannot be enabled "
                    "for a behavioral interview."
                ),
            )

    role = payload.role.strip()

    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role cannot be empty.",
        )

    return {
        "role": role,
        "job_description": payload.job_description.strip(),
        "interview_type": interview_type,
        "difficulty": difficulty,
        "configuration": {
            "question_count": payload.configuration.question_count,
            "duration_minutes": payload.configuration.duration_minutes,
            "focus_areas": payload.configuration.focus_areas,
            "include_coding": payload.configuration.include_coding,
            "include_system_design": (
                payload.configuration.include_system_design
            ),
        },
    }


# ============================================================
# RESPONSE TRANSFORMATION
# ============================================================

def _session_dict(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a Supabase row into the API response shape.
    """

    return {
        "id": str(row["id"]),
        "user_id": str(row["user_id"]),

        "role": row.get("role", ""),

        "job_description": row.get(
            "job_description",
            "",
        ),

        "interview_type": row.get(
            "interview_type",
            "mixed",
        ),

        "difficulty": row.get(
            "difficulty",
            "medium",
        ),

        "status": row.get(
            "status",
            "not_started",
        ),

        "current_question_number": row.get(
            "current_question_number",
            0,
        ),

        "configuration": row.get(
            "configuration",
            {},
        ),

        "started_at": row.get(
            "started_at"
        ),

        "completed_at": row.get(
            "completed_at"
        ),

        "created_at": row.get(
            "created_at"
        ),

        "updated_at": row.get(
            "updated_at"
        ),
    }


# ============================================================
# DATABASE HELPERS
# ============================================================

async def _get_owned_session(
    session_id: str,
    user_id: str,
) -> Dict[str, Any]:
    """
    Retrieve one interview session belonging to the authenticated user.

    Uses the existing SmartHire Supabase REST architecture.
    """

    try:
        rows = await supabase_rest_get(
            "interview_sessions",
            {
                "id": f"eq.{session_id}",
                "user_id": f"eq.{user_id}",
                "limit": "1",
            },
        )

    except Exception as exc:
        logger.exception(
            "Failed to retrieve interview session %s",
            session_id,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve interview session.",
        ) from exc

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Interview session not found "
                "or does not belong to this user."
            ),
        )

    return rows[0]


async def _update_owned_session(
    session_id: str,
    user_id: str,
    data: Dict[str, Any],
    allowed_statuses: List[str],
) -> Dict[str, Any]:
    """
    Update an owned session only when its current state is one
    of the expected states.
    """

    status_filters = (
        f"in.({','.join(allowed_statuses)})"
        if len(allowed_statuses) > 1
        else f"eq.{allowed_statuses[0]}"
    )

    params = {
        "id": f"eq.{session_id}",
        "user_id": f"eq.{user_id}",
        "status": status_filters,
    }

    try:
        rows = await supabase_rest_patch(
            "interview_sessions",
            params,
            data,
        )

    except Exception as exc:
        logger.exception(
            "Failed to update interview session %s",
            session_id,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not update interview session.",
        ) from exc

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Interview session state changed. Please refresh and try again.",
        )

    return rows[0]


# ============================================================
# CREATE SESSION
# ============================================================

@router.post(
    "",
    response_model=InterviewSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_interview_session(
    payload: InterviewSessionCreate,
    user_id: str = Depends(get_current_user),
):
    """
    Create a new interview session.

    Newly created sessions always start in:
        not_started
    """

    validated = _validate_create_payload(payload)

    data = {
        "user_id": user_id,
        "role": validated["role"],
        "job_description": validated["job_description"],
        "interview_type": validated["interview_type"],
        "difficulty": validated["difficulty"],
        "status": "not_started",
        "current_question_number": 0,
        "configuration": validated["configuration"],
    }

    try:
        rows = await supabase_rest_post(
            "interview_sessions",
            data,
        )

    except Exception as exc:
        logger.exception(
            "Failed to create interview session."
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create interview session.",
        ) from exc

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Interview session was not created.",
        )

    return _session_dict(rows[0])


# ============================================================
# LIST USER SESSIONS
# ============================================================

@router.get(
    "",
    response_model=List[InterviewSessionResponse],
)
async def list_interview_sessions(
    user_id: str = Depends(get_current_user),
):
    """
    Return the authenticated user's interview sessions.

    Newest sessions are returned first.
    """

    try:
        rows = await supabase_rest_get(
            "interview_sessions",
            {
                "user_id": f"eq.{user_id}",
                "order": "created_at.desc",
            },
        )

    except Exception as exc:
        logger.exception(
            "Failed to list interview sessions."
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not load interview sessions.",
        ) from exc

    return [
        _session_dict(row)
        for row in rows
    ]


# ============================================================
# GET ONE SESSION
# ============================================================

@router.get(
    "/{session_id}",
    response_model=InterviewSessionResponse,
)
async def get_interview_session(
    session_id: str,
    user_id: str = Depends(get_current_user),
):
    """
    Retrieve one interview session owned by the user.
    """

    row = await _get_owned_session(
        session_id,
        user_id,
    )

    return _session_dict(row)


# ============================================================
# GET CONFIGURATION
# ============================================================

@router.get(
    "/{session_id}/configuration",
)
async def get_interview_configuration(
    session_id: str,
    user_id: str = Depends(get_current_user),
):
    """
    Return the configuration for an owned interview session.
    """

    session = await _get_owned_session(
        session_id,
        user_id,
    )

    return {
        "session_id": session["id"],
        "configuration": session.get(
            "configuration",
            {},
        ),
    }


# ============================================================
# UPDATE CONFIGURATION
# ============================================================

@router.put(
    "/{session_id}/configuration",
)
async def update_interview_configuration(
    session_id: str,
    configuration: InterviewConfiguration,
    user_id: str = Depends(get_current_user),
):
    """
    Update configuration for an owned interview session.

    Configuration can only be changed before the interview starts.
    """

    session = await _get_owned_session(
        session_id,
        user_id,
    )

    current_status = session.get(
        "status",
        "not_started",
    )

    if current_status != "not_started":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Interview configuration can only be changed "
                "before the interview starts."
            ),
        )

    interview_type = session.get(
        "interview_type",
        "mixed",
    )

    if interview_type == "behavioral":

        if configuration.include_coding:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Coding questions cannot be enabled "
                    "for a behavioral interview."
                ),
            )

        if configuration.include_system_design:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "System design cannot be enabled "
                    "for a behavioral interview."
                ),
            )

    updated_configuration = {
        "question_count": configuration.question_count,
        "duration_minutes": configuration.duration_minutes,
        "focus_areas": configuration.focus_areas,
        "include_coding": configuration.include_coding,
        "include_system_design": (
            configuration.include_system_design
        ),
    }

    try:
        rows = await supabase_rest_patch(
            "interview_sessions",
            {
                "id": f"eq.{session_id}",
                "user_id": f"eq.{user_id}",
                "status": "eq.not_started",
            },
            {
                "configuration": updated_configuration,
                "updated_at": _utc_now(),
            },
        )

    except Exception as exc:
        logger.exception(
            "Failed to update interview configuration for session %s",
            session_id,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update interview configuration.",
        ) from exc

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Interview configuration could not be updated "
                "because the session is no longer in the "
                "not_started state."
            ),
        )

    return {
        "session_id": session_id,
        "configuration": updated_configuration,
    }


# ============================================================
# START SESSION
# ============================================================

@router.post(
    "/{session_id}/start",
    response_model=InterviewSessionResponse,
)
async def start_interview_session(
    session_id: str,
    user_id: str = Depends(get_current_user),
):
    """
    Transition:

        not_started → active
    """

    row = await _get_owned_session(
        session_id,
        user_id,
    )

    current_status = row.get(
        "status",
        "not_started",
    )

    if current_status != "not_started":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Cannot start an interview from "
                f"'{current_status}' state."
            ),
        )

    now = _utc_now()

    update_data = {
        "status": "active",
        "started_at": now,
        "current_question_number": 0,
        "updated_at": now,
    }

    updated_row = await _update_owned_session(
        session_id,
        user_id,
        update_data,
        ["not_started"],
    )

    return _session_dict(updated_row)


# ============================================================
# PAUSE SESSION
# ============================================================

@router.post(
    "/{session_id}/pause",
    response_model=InterviewSessionResponse,
)
async def pause_interview_session(
    session_id: str,
    user_id: str = Depends(get_current_user),
):
    """
    Transition:

        active → paused
    """

    row = await _get_owned_session(
        session_id,
        user_id,
    )

    current_status = row.get(
        "status",
        "not_started",
    )

    if current_status != "active":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Cannot pause an interview from "
                f"'{current_status}' state."
            ),
        )

    updated_row = await _update_owned_session(
        session_id,
        user_id,
        {
            "status": "paused",
            "updated_at": _utc_now(),
        },
        ["active"],
    )

    return _session_dict(updated_row)


# ============================================================
# RESUME SESSION
# ============================================================

@router.post(
    "/{session_id}/resume",
    response_model=InterviewSessionResponse,
)
async def resume_interview_session(
    session_id: str,
    user_id: str = Depends(get_current_user),
):
    """
    Transition:

        paused → active
    """

    row = await _get_owned_session(
        session_id,
        user_id,
    )

    current_status = row.get(
        "status",
        "not_started",
    )

    if current_status != "paused":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Cannot resume an interview from "
                f"'{current_status}' state."
            ),
        )

    updated_row = await _update_owned_session(
        session_id,
        user_id,
        {
            "status": "active",
            "updated_at": _utc_now(),
        },
        ["paused"],
    )

    return _session_dict(updated_row)


# ============================================================
# COMPLETE SESSION
# ============================================================

@router.post(
    "/{session_id}/complete",
    response_model=InterviewSessionResponse,
)
async def complete_interview_session(
    session_id: str,
    user_id: str = Depends(get_current_user),
):
    """
    Transition:

        active → completed
        paused → completed

    Completion timestamp is recorded.
    """

    row = await _get_owned_session(
        session_id,
        user_id,
    )

    current_status = row.get(
        "status",
        "not_started",
    )

    if current_status not in {
        "active",
        "paused",
    }:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Cannot complete an interview from "
                f"'{current_status}' state."
            ),
        )

    now = _utc_now()

    updated_row = await _update_owned_session(
        session_id,
        user_id,
        {
            "status": "completed",
            "completed_at": now,
            "updated_at": now,
        },
        ["active", "paused"],
    )

    return _session_dict(updated_row)
# ============================================================
# GET INTERVIEW QUESTIONS
# ============================================================

@router.get(
    "/{session_id}/questions",
    response_model=List[InterviewQuestionResponse],
)
async def get_interview_questions(
    session_id: str,
    user_id: str = Depends(get_current_user),
):
    """
    Return all persisted questions for an owned interview session.
    Questions are returned in interview order.
    """

    # Verify that the session belongs to the authenticated user.
    await _get_owned_session(
        session_id=session_id,
        user_id=user_id,
    )

    try:
        rows = await supabase_rest_get(
            "interview_questions",
            {
                "session_id": f"eq.{session_id}",
                "order": "question_order.asc",
            },
        )

    except Exception as exc:
        logger.exception(
            "Failed to load interview questions for session %s",
            session_id,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not load interview questions.",
        ) from exc

    return [
        InterviewQuestionResponse(
            id=str(row["id"]),
            session_id=str(row["session_id"]),
            question=row.get("question", ""),
            category=row.get("category", "technical"),
            difficulty=row.get("difficulty", "medium"),
            skill=row.get("skill", ""),
            expected_topics=row.get("expected_topics", []) or [],
            question_order=int(row.get("question_order", 0)),
            created_at=row.get("created_at"),
        )
        for row in rows
    ]
# ============================================================
# PHASE 4D — QUESTION GENERATION
# ============================================================
@router.post(
    "/{session_id}/questions/generate",
    response_model=InterviewQuestionGenerationResponse,
)
async def generate_questions_for_interview(
    session_id: str,
    user_id: str = Depends(get_current_user),
):
    """
    Generate and persist personalized interview questions.

    Questions are generated using:
    - interview role
    - job description
    - interview type
    - difficulty
    - interview configuration
    - candidate career profile
    - candidate resume
    """

    # --------------------------------------------------------
    # 1. Load owned interview session
    # --------------------------------------------------------

    session = await _get_owned_session(
        session_id=session_id,
        user_id=user_id,
    )

    current_status = session.get(
        "status",
        "not_started",
    )

    # --------------------------------------------------------
    # Return existing questions if generation already happened
    # --------------------------------------------------------

    try:
        existing_rows = await supabase_rest_get(
            "interview_questions",
            {
                "session_id": f"eq.{session_id}",
                "order": "question_order.asc",
            },
        )

    except Exception as exc:
        logger.exception(
            "Failed to check existing interview questions "
            "for session %s",
            session_id,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not check existing interview questions.",
        ) from exc

    if existing_rows:
        logger.info(
            "Questions already exist for session %s. "
            "Returning existing questions.",
            session_id,
        )

        response_questions = [
            InterviewQuestionResponse(
                id=str(row["id"]),
                session_id=str(row["session_id"]),
                question=row.get("question", ""),
                category=row.get(
                    "category",
                    "technical",
                ),
                difficulty=row.get(
                    "difficulty",
                    "medium",
                ),
                skill=row.get(
                    "skill",
                    "",
                ),
                expected_topics=row.get(
                    "expected_topics",
                    [],
                ) or [],
                question_order=int(
                    row.get(
                        "question_order",
                        0,
                    )
                ),
                created_at=row.get("created_at"),
            )
            for row in existing_rows
        ]

        return InterviewQuestionGenerationResponse(
            session_id=session_id,
            generated_count=len(response_questions),
            questions=response_questions,
        )

    # No questions exist yet, so generation is allowed only
    # before the interview starts.
    if current_status != "not_started":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Questions can only be generated "
                "before the interview starts."
            ),
        )

    # --------------------------------------------------------
    # 2. Read configuration
    # --------------------------------------------------------

    configuration = (
        session.get("configuration")
        or {}
    )

    question_count = int(
        configuration.get(
            "question_count",
            10,
        )
    )

    focus_areas = configuration.get(
        "focus_areas",
        [],
    ) or []

    include_coding = bool(
        configuration.get(
            "include_coding",
            False,
        )
    )

    include_system_design = bool(
        configuration.get(
            "include_system_design",
            False,
        )
    )

    interview_type = (
        session.get(
            "interview_type",
            "mixed",
        )
        or "mixed"
    ).strip().lower()

    difficulty = (
        session.get(
            "difficulty",
            "medium",
        )
        or "medium"
    ).strip().lower()

    role = (
        session.get(
            "role",
            "",
        )
        or ""
    ).strip()

    job_description = (
        session.get(
            "job_description",
            "",
        )
        or ""
    ).strip()

    # --------------------------------------------------------
    # 3. Load candidate profile
    # --------------------------------------------------------

    try:
        profile_rows = await supabase_rest_get(
            "profiles",
            {
                "user_id": f"eq.{user_id}",
                "select": (
                    "username,skills,target_roles,"
                    "experience,resume_filename,resume_text"
                ),
                "limit": "1",
            },
        )

    except Exception as exc:
        logger.exception(
            "Failed to load candidate profile "
            "for interview generation."
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not load your career profile.",
        ) from exc

    if not profile_rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Career profile not found. "
                "Complete your profile before "
                "starting an interview."
            ),
        )

    profile = profile_rows[0]

    # --------------------------------------------------------
    # 4. Generate questions using LLM
    # --------------------------------------------------------

    try:
        generated = await generate_interview_questions(
            role=role,
            job_description=job_description,
            interview_type=interview_type,
            difficulty=difficulty,
            question_count=question_count,
            focus_areas=focus_areas,
            include_coding=include_coding,
            include_system_design=include_system_design,
            profile=profile,
        )

    except ValueError as exc:
        logger.exception(
            "Generated question validation failed."
        )

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:
        logger.exception(
            "LLM question generation failed."
        )

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        logger.exception(
            "Unexpected interview question generation error."
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "An unexpected error occurred while "
                "generating interview questions."
            ),
        ) from exc

    # --------------------------------------------------------
    # 5. Prepare database rows
    # --------------------------------------------------------

    question_rows = []

    for index, question in enumerate(
        generated.questions,
        start=1,
    ):
        question_rows.append(
            {
                "session_id": session_id,
                "question": question.question,
                "category": question.category,
                "difficulty": question.difficulty,
                "skill": question.skill,
                "expected_topics": question.expected_topics,
                "question_order": index,
            }
        )

    if not question_rows:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The AI did not generate any interview questions.",
        )

    # --------------------------------------------------------
    # 6. Persist questions
    # --------------------------------------------------------

    try:
        rows = await supabase_rest_post(
            "interview_questions",
            question_rows,
        )

    except httpx.HTTPStatusError as exc:
        # Another request may have generated the questions
        # at the same time. Supabase returns 409 because
        # (session_id, question_order) is unique.
        if exc.response.status_code == 409:
            logger.info(
                "Concurrent question generation detected "
                "for session %s. Loading existing questions.",
                session_id,
            )

            try:
                existing_rows = await supabase_rest_get(
                    "interview_questions",
                    {
                        "session_id": f"eq.{session_id}",
                        "order": "question_order.asc",
                    },
                )

            except Exception as fetch_exc:
                logger.exception(
                    "Failed to load existing questions after "
                    "generation conflict for session %s.",
                    session_id,
                )

                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=(
                        "Questions were generated concurrently, "
                        "but the existing questions could not "
                        "be loaded."
                    ),
                ) from fetch_exc

            if existing_rows:
                response_questions = [
                    InterviewQuestionResponse(
                        id=str(row["id"]),
                        session_id=str(row["session_id"]),
                        question=row.get("question", ""),
                        category=row.get(
                            "category",
                            "technical",
                        ),
                        difficulty=row.get(
                            "difficulty",
                            "medium",
                        ),
                        skill=row.get(
                            "skill",
                            "",
                        ),
                        expected_topics=row.get(
                            "expected_topics",
                            [],
                        ) or [],
                        question_order=int(
                            row.get(
                                "question_order",
                                0,
                            )
                        ),
                        created_at=row.get(
                            "created_at",
                        ),
                    )
                    for row in existing_rows
                ]

                return InterviewQuestionGenerationResponse(
                    session_id=session_id,
                    generated_count=len(response_questions),
                    questions=response_questions,
                )

        logger.exception(
            "Failed to persist generated interview questions."
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Questions were generated but could not "
                "be saved."
            ),
        ) from exc

    except Exception as exc:
        logger.exception(
            "Failed to persist generated interview questions."
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Questions were generated but could not "
                "be saved."
            ),
        ) from exc

    # --------------------------------------------------------
    # 7. Verify persistence
    # --------------------------------------------------------

    if len(rows) != len(question_rows):
        logger.error(
            "Question persistence mismatch: generated=%s saved=%s",
            len(question_rows),
            len(rows),
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Generated questions were not saved completely."
            ),
        )

    # --------------------------------------------------------
    # 8. Build normalized response
    # --------------------------------------------------------

    response_questions = []

    for row in sorted(
        rows,
        key=lambda item: item.get(
            "question_order",
            0,
        ),
    ):
        response_questions.append(
            InterviewQuestionResponse(
                id=str(row["id"]),
                session_id=str(row["session_id"]),
                question=row.get(
                    "question",
                    "",
                ),
                category=row.get(
                    "category",
                    "technical",
                ),
                difficulty=row.get(
                    "difficulty",
                    difficulty,
                ),
                skill=row.get(
                    "skill",
                    "",
                ),
                expected_topics=row.get(
                    "expected_topics",
                    [],
                ) or [],
                question_order=int(
                    row.get(
                        "question_order",
                        0,
                    )
                ),
                created_at=row.get(
                    "created_at",
                ),
            )
        )

    return InterviewQuestionGenerationResponse(
        session_id=session_id,
        generated_count=len(response_questions),
        questions=response_questions,
    )
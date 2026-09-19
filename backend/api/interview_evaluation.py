"""
SmartHire Interview Answer + Evaluation API.

Phase 4E:
- submit candidate answers
- evaluate answers
- persist evaluations
- retrieve evaluations

The API layer owns database persistence.
The evaluation engine owns LLM/rubric logic.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

import httpx

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from pydantic import BaseModel, Field, field_validator

from backend.api.auth import get_current_user
from backend.core.config import (
    SUPABASE_KEY,
    SUPABASE_URL,
)
from backend.services.interview.evaluation_engine import (
    InterviewEvaluationEngine,
)


logger = logging.getLogger(
    "smarthire.interview.evaluation_api"
)


router = APIRouter(
    prefix="/api/v1/interviews",
    tags=["Interview Evaluation"],
)


# ============================================================
# DATABASE HELPERS
# ============================================================

def _supabase_headers() -> Dict[str, str]:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError(
            "Supabase configuration is missing."
        )

    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def _supabase_url(
    table: str,
) -> str:
    return (
        f"{SUPABASE_URL.rstrip('/')}"
        f"/rest/v1/{table}"
    )


async def _select(
    table: str,
    params: Dict[str, str],
) -> List[Dict[str, Any]]:
    """
    Select rows from Supabase REST API.
    """

    try:
        async with httpx.AsyncClient(
            timeout=30.0
        ) as client:
            response = await client.get(
                _supabase_url(table),
                headers=_supabase_headers(),
                params=params,
            )

            response.raise_for_status()

            data = response.json()

            return (
                data
                if isinstance(data, list)
                else []
            )

    except httpx.HTTPStatusError as exc:
        logger.exception(
            "Supabase select failed for %s.",
            table,
        )

        raise RuntimeError(
            f"Supabase select failed for {table}."
        ) from exc

    except Exception as exc:
        logger.exception(
            "Supabase select error for %s.",
            table,
        )

        raise RuntimeError(
            f"Could not query {table}."
        ) from exc


async def _insert(
    table: str,
    payload: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Insert one row into Supabase.
    """

    try:
        async with httpx.AsyncClient(
            timeout=30.0
        ) as client:
            response = await client.post(
                _supabase_url(table),
                headers=_supabase_headers(),
                json=payload,
            )

            response.raise_for_status()

            data = response.json()

            return (
                data
                if isinstance(data, list)
                else []
            )

    except Exception as exc:
        logger.exception(
            "Supabase insert failed for %s.",
            table,
        )

        raise RuntimeError(
            f"Could not insert into {table}."
        ) from exc


async def _upsert(
    table: str,
    payload: Dict[str, Any],
    conflict: str,
) -> List[Dict[str, Any]]:
    """
    Upsert one row into Supabase.
    """

    headers = _supabase_headers()

    headers["Prefer"] = (
        f"resolution=merge-duplicates,"
        f"return=representation"
    )

    try:
        async with httpx.AsyncClient(
            timeout=30.0
        ) as client:
            response = await client.post(
                _supabase_url(table),
                headers=headers,
                params={
                    "on_conflict": conflict,
                },
                json=payload,
            )

            response.raise_for_status()

            data = response.json()

            return (
                data
                if isinstance(data, list)
                else []
            )

    except Exception as exc:
        logger.exception(
            "Supabase upsert failed for %s.",
            table,
        )

        raise RuntimeError(
            f"Could not upsert {table}."
        ) from exc


# ============================================================
# SCHEMAS
# ============================================================

class SubmitAnswerRequest(BaseModel):
    answer_text: str = Field(
        ...,
        min_length=1,
        max_length=20000,
    )

    answer_source: Literal["voice"] = "voice"

    @field_validator("answer_text")
    @classmethod
    def validate_answer_text(
        cls,
        value: str,
    ) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "Answer cannot be empty."
            )

        return value


class InterviewAnswerResponse(BaseModel):
    id: str
    session_id: str
    question_id: str
    answer_text: str
    answer_source: str
    answered_at: Any
    created_at: Any


class EvaluationResponse(BaseModel):
    id: str
    session_id: str
    answer_id: str

    technical_score: int
    relevance_score: int
    clarity_score: int
    depth_score: int
    overall_score: int

    feedback: str
    strengths: List[str] = Field(
        default_factory=list
    )
    weaknesses: List[str] = Field(
        default_factory=list
    )


# ============================================================
# OWNERSHIP HELPERS
# ============================================================

async def _get_owned_session(
    session_id: str,
    user_id: str,
) -> Dict[str, Any]:
    rows = await _select(
        "interview_sessions",
        {
            "id": f"eq.{session_id}",
            "user_id": f"eq.{user_id}",
            "limit": "1",
        },
    )

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Interview session not found "
                "or does not belong to this user."
            ),
        )

    return rows[0]


async def _get_owned_question(
    session_id: str,
    question_id: str,
) -> Dict[str, Any]:
    rows = await _select(
        "interview_questions",
        {
            "id": f"eq.{question_id}",
            "session_id": f"eq.{session_id}",
            "limit": "1",
        },
    )

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview question not found.",
        )

    return rows[0]


async def _get_owned_answer(
    session_id: str,
    answer_id: str,
) -> Dict[str, Any]:
    rows = await _select(
        "interview_answers",
        {
            "id": f"eq.{answer_id}",
            "session_id": f"eq.{session_id}",
            "limit": "1",
        },
    )

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview answer not found.",
        )

    return rows[0]


def _answer_response(
    row: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "id": str(row["id"]),
        "session_id": str(
            row["session_id"]
        ),
        "question_id": str(
            row["question_id"]
        ),
        "answer_text": row.get(
            "answer_text",
            "",
        ),
        "answer_source": row.get(
            "answer_source",
            "text",
        ),
        "answered_at": row.get(
            "answered_at"
        ),
        "created_at": row.get(
            "created_at"
        ),
    }


def _evaluation_response(
    row: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "id": str(row["id"]),
        "session_id": str(
            row["session_id"]
        ),
        "answer_id": str(
            row["answer_id"]
        ),
        "technical_score": int(
            row.get(
                "technical_score",
                0,
            )
        ),
        "relevance_score": int(
            row.get(
                "relevance_score",
                0,
            )
        ),
        "clarity_score": int(
            row.get(
                "clarity_score",
                0,
            )
        ),
        "depth_score": int(
            row.get(
                "depth_score",
                0,
            )
        ),
        "overall_score": int(
            row.get(
                "overall_score",
                0,
            )
        ),
        "feedback": row.get(
            "feedback",
            "",
        ),
        "strengths": row.get(
            "strengths",
            [],
        ) or [],
        "weaknesses": row.get(
            "weaknesses",
            [],
        ) or [],
    }


# ============================================================
# SUBMIT ANSWER
# ============================================================

@router.post(
    "/{session_id}/questions/{question_id}/answer",
    response_model=InterviewAnswerResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_interview_answer(
    session_id: str,
    question_id: str,
    payload: SubmitAnswerRequest,
    user_id: str = Depends(
        get_current_user
    ),
):
    """
    Save a candidate answer.

    The database has a unique constraint on question_id,
    so submitting an answer for the same question again
    should update the existing answer instead of creating
    duplicates.
    """

    session = await _get_owned_session(
        session_id,
        user_id,
    )

    await _get_owned_question(
        session_id,
        question_id,
    )

    now = datetime.now(
        timezone.utc
    ).isoformat()

    data = {
        "session_id": session_id,
        "question_id": question_id,
        "answer_text": payload.answer_text,
        "answer_source": payload.answer_source,
        "answered_at": now,
    }

    try:
        rows = await _upsert(
            "interview_answers",
            data,
            conflict="question_id",
        )

    except Exception as exc:
        logger.exception(
            "Failed to save interview answer."
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save interview answer.",
        ) from exc

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Interview answer was not saved.",
        )

    # --------------------------------------------------------
    # Update current question number
    # --------------------------------------------------------

    question_rows = await _select(
        "interview_questions",
        {
            "id": f"eq.{question_id}",
            "session_id": f"eq.{session_id}",
            "limit": "1",
        },
    )

    if question_rows:
        question_order = int(
            question_rows[0].get(
                "question_order",
                0,
            )
        )

        try:
            headers = _supabase_headers()

            async with httpx.AsyncClient(
                timeout=30.0
            ) as client:
                await client.patch(
                    _supabase_url(
                        "interview_sessions"
                    ),
                    headers=headers,
                    params={
                        "id": f"eq.{session_id}",
                        "user_id": f"eq.{user_id}",
                    },
                    json={
                        "current_question_number":
                            question_order,
                        "updated_at": now,
                    },
                )

        except Exception:
            # Answer has already been safely saved.
            # Position update should not destroy the answer.
            logger.warning(
                "Could not update current question "
                "number for session %s.",
                session_id,
            )

    return _answer_response(
        rows[0]
    )


# ============================================================
# EVALUATE ANSWER
# ============================================================

@router.post(
    "/{session_id}/answers/{answer_id}/evaluate",
    response_model=EvaluationResponse,
)
async def evaluate_interview_answer(
    session_id: str,
    answer_id: str,
    user_id: str = Depends(
        get_current_user
    ),
):
    """
    Evaluate a saved candidate answer.
    """

    session = await _get_owned_session(
        session_id,
        user_id,
    )

    answer = await _get_owned_answer(
        session_id,
        answer_id,
    )

    question = await _get_owned_question(
        session_id,
        str(answer["question_id"]),
    )

    expected_topics = (
        question.get(
            "expected_topics",
            [],
        )
        or []
    )

    engine = InterviewEvaluationEngine(
        provider="groq"
    )

    try:
        evaluation = (
            await engine.evaluate_answer(
                question=question.get(
                    "question",
                    "",
                ),
                category=question.get(
                    "category",
                    "technical",
                ),
                difficulty=question.get(
                    "difficulty",
                    "medium",
                ),
                skill=question.get(
                    "skill",
                    "",
                ),
                expected_topics=[
                    str(topic)
                    for topic in expected_topics
                ],
                candidate_answer=answer.get(
                    "answer_text",
                    "",
                ),
                role=session.get(
                    "role",
                    "",
                ),
                job_description=session.get(
                    "job_description",
                    "",
                ),
            )
        )

    except ValueError as exc:
        logger.exception(
            "Interview evaluation validation failed."
        )

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:
        logger.exception(
            "Interview evaluation provider failed."
        )

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "Interview evaluation service failed. "
                "Please retry."
            ),
        ) from exc

    except Exception as exc:
        logger.exception(
            "Unexpected interview evaluation failure."
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not evaluate interview answer.",
        ) from exc

    evaluation_data = {
        "session_id": session_id,
        "answer_id": answer_id,
        "technical_score": (
            evaluation.technical_score
        ),
        "relevance_score": (
            evaluation.relevance_score
        ),
        "clarity_score": (
            evaluation.clarity_score
        ),
        "depth_score": (
            evaluation.depth_score
        ),
        "overall_score": (
            evaluation.overall_score
        ),
        "feedback": evaluation.feedback,
        "strengths": evaluation.strengths,
        "weaknesses": evaluation.weaknesses,
    }

    try:
        rows = await _upsert(
            "interview_evaluations",
            evaluation_data,
            conflict="answer_id",
        )

    except Exception as exc:
        logger.exception(
            "Failed to persist interview evaluation."
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save interview evaluation.",
        ) from exc

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Interview evaluation was not saved.",
        )

    return _evaluation_response(
        rows[0]
    )


# ============================================================
# GET EVALUATION
# ============================================================

@router.get(
    "/{session_id}/answers/{answer_id}/evaluation",
    response_model=EvaluationResponse,
)
async def get_interview_evaluation(
    session_id: str,
    answer_id: str,
    user_id: str = Depends(
        get_current_user
    ),
):
    """
    Retrieve the evaluation belonging to an answer.
    """

    await _get_owned_session(
        session_id,
        user_id,
    )

    await _get_owned_answer(
        session_id,
        answer_id,
    )

    rows = await _select(
        "interview_evaluations",
        {
            "answer_id": f"eq.{answer_id}",
            "session_id": f"eq.{session_id}",
            "limit": "1",
        },
    )

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Evaluation has not been generated "
                "for this answer yet."
            ),
        )

    return _evaluation_response(
        rows[0]
    )
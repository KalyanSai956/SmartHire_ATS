"""
SmartHire Phase 4F — Adaptive Interview API.

Flow:

Candidate Answer
      ↓
Existing 4E Evaluation
      ↓
Read Evaluation
      ↓
Adaptive Engine
      ↓
Generate Next Question
      ↓
Replace Next Question Slot
      ↓
Persist Question
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.api.auth import get_current_user
from backend.services.interview.adaptive_engine import (
    AdaptiveInterviewEngine,
)


logger = logging.getLogger(
    "smarthire.api.interview_adaptive"
)


router = APIRouter(
    prefix="/api/v1/interviews",
    tags=["Adaptive Interviews"],
)


# ============================================================
# SUPABASE CONFIG
# ============================================================

SUPABASE_URL = os.getenv(
    "SUPABASE_URL",
    "",
)

SUPABASE_KEY = os.getenv(
    "SUPABASE_KEY",
    "",
)


def _supabase_headers() -> Dict[str, str]:
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }


def _supabase_table_url(
    table: str,
) -> str:
    return (
        f"{SUPABASE_URL.rstrip('/')}"
        f"/rest/v1/{table}"
    )


# ============================================================
# RESPONSE MODEL
# ============================================================

class AdaptiveNextQuestionResponse(BaseModel):
    question_id: str
    question: str
    category: str
    difficulty: str
    skill: str
    expected_topics: List[str]

    strategy: str
    focus_dimension: str
    reason: str
    priority: str

    question_order: int


# ============================================================
# DATABASE HELPERS
# ============================================================

async def _get_owned_session(
    client: httpx.AsyncClient,
    session_id: str,
    user_id: str,
) -> Dict[str, Any]:

    response = await client.get(
        _supabase_table_url(
            "interview_sessions"
        ),
        headers=_supabase_headers(),
        params={
            "id": f"eq.{session_id}",
            "user_id": f"eq.{user_id}",
            "select": "*",
            "limit": "1",
        },
    )

    response.raise_for_status()

    rows = response.json()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail="Interview session not found.",
        )

    return rows[0]


async def _get_owned_question(
    client: httpx.AsyncClient,
    session_id: str,
    question_id: str,
) -> Dict[str, Any]:

    response = await client.get(
        _supabase_table_url(
            "interview_questions"
        ),
        headers=_supabase_headers(),
        params={
            "id": f"eq.{question_id}",
            "session_id": f"eq.{session_id}",
            "select": "*",
            "limit": "1",
        },
    )

    response.raise_for_status()

    rows = response.json()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail="Interview question not found.",
        )

    return rows[0]


async def _get_latest_evaluation(
    client: httpx.AsyncClient,
    answer_id: str,
) -> Dict[str, Any]:

    response = await client.get(
        _supabase_table_url(
            "interview_evaluations"
        ),
        headers=_supabase_headers(),
        params={
            "answer_id": f"eq.{answer_id}",
            "select": "*",
            "limit": "1",
        },
    )

    response.raise_for_status()

    rows = response.json()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=(
                "No evaluation exists for this answer. "
                "Evaluate the answer before requesting "
                "the next adaptive question."
            ),
        )

    return rows[0]


async def _get_answer(
    client: httpx.AsyncClient,
    answer_id: str,
    question_id: str,
) -> Dict[str, Any]:

    response = await client.get(
        _supabase_table_url(
            "interview_answers"
        ),
        headers=_supabase_headers(),
        params={
            "id": f"eq.{answer_id}",
            "question_id": f"eq.{question_id}",
            "select": "*",
            "limit": "1",
        },
    )

    response.raise_for_status()

    rows = response.json()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail="Interview answer not found.",
        )

    return rows[0]


async def _get_previous_questions(
    client: httpx.AsyncClient,
    session_id: str,
) -> List[Dict[str, Any]]:

    response = await client.get(
        _supabase_table_url(
            "interview_questions"
        ),
        headers=_supabase_headers(),
        params={
            "session_id": f"eq.{session_id}",
            "select": (
                "id,question,category,difficulty,"
                "skill,expected_topics,question_order"
            ),
            "order": "question_order.asc",
        },
    )

    response.raise_for_status()

    return response.json()


async def _insert_question(
    client: httpx.AsyncClient,
    payload: Dict[str, Any],
) -> Dict[str, Any]:

    response = await client.post(
        _supabase_table_url(
            "interview_questions"
        ),
        headers={
            **_supabase_headers(),
            "Prefer": "return=representation",
        },
        json=payload,
    )

    response.raise_for_status()

    rows = response.json()

    if not rows:
        raise RuntimeError(
            "Supabase did not return the inserted question."
        )

    return rows[0]


async def _update_question(
    client: httpx.AsyncClient,
    question_id: str,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Replace an existing question slot with an adaptive question.

    We deliberately keep the same question_order and question ID.
    This prevents adaptive questions from becoming Q11, Q12, etc.
    when the configured interview length is 10.
    """

    response = await client.patch(
        _supabase_table_url(
            "interview_questions"
        ),
        headers={
            **_supabase_headers(),
            "Prefer": "return=representation",
        },
        params={
            "id": f"eq.{question_id}",
        },
        json=payload,
    )

    response.raise_for_status()

    rows = response.json()

    if not rows:
        raise RuntimeError(
            "Supabase did not return the updated question."
        )

    return rows[0]


async def _update_session_question_number(
    client: httpx.AsyncClient,
    session_id: str,
    next_question_number: int,
) -> None:

    response = await client.patch(
        _supabase_table_url(
            "interview_sessions"
        ),
        headers=_supabase_headers(),
        params={
            "id": f"eq.{session_id}",
        },
        json={
            "current_question_number": (
                next_question_number
            ),
        },
    )

    # Question persistence is already complete.
    # This update should not destroy a valid generated question.
    if response.status_code >= 400:
        logger.warning(
            "Could not update current question number: %s",
            response.text,
        )


# ============================================================
# ENDPOINT
# ============================================================

@router.post(
    "/{session_id}/questions/"
    "{question_id}/adaptive-next",
    response_model=AdaptiveNextQuestionResponse,
)
async def generate_adaptive_next_question(
    session_id: str,
    question_id: str,
    answer_id: str,
    user_id: str = Depends(get_current_user),
):
    """
    Generate the next adaptive interview question.

    Required flow:

    1. Candidate answers current question.
    2. Existing Phase 4E endpoint evaluates the answer.
    3. This endpoint reads that evaluation.
    4. Phase 4F determines the next strategy.
    5. LLM generates the next question.
    6. The next configured question slot is replaced.
    7. Interview remains within the configured question count.
    """

    if not SUPABASE_URL or not SUPABASE_KEY:
        raise HTTPException(
            status_code=500,
            detail="Supabase configuration is missing.",
        )

    try:
        async with httpx.AsyncClient(
            timeout=60.0
        ) as client:

            # ------------------------------------------------
            # OWNERSHIP
            # ------------------------------------------------

            session = await _get_owned_session(
                client,
                session_id,
                user_id,
            )

            current_question = (
                await _get_owned_question(
                    client,
                    session_id,
                    question_id,
                )
            )

            answer = await _get_answer(
                client,
                answer_id,
                question_id,
            )

            evaluation = await _get_latest_evaluation(
                client,
                answer_id,
            )

            # ------------------------------------------------
            # PREVIOUS QUESTIONS
            # ------------------------------------------------

            previous_questions = (
                await _get_previous_questions(
                    client,
                    session_id,
                )
            )

            # ------------------------------------------------
            # SESSION CONFIGURATION
            # ------------------------------------------------

            configuration = (
                session.get("configuration")
                or {}
            )

            role = (
                configuration.get("role")
                or session.get("role")
                or ""
            )

            job_description = (
                session.get("job_description")
                or ""
            )

            configured_question_count = int(
                configuration.get(
                    "question_count",
                    10,
                )
                or 10
            )

            # ------------------------------------------------
            # CURRENT QUESTION ORDER
            # ------------------------------------------------

            current_order = int(
                current_question.get(
                    "question_order",
                    0,
                )
                or 0
            )

            next_order = current_order + 1

            # ------------------------------------------------
            # SAFETY
            #
            # The frontend normally does not call adaptive-next
            # for the final question.
            #
            # Keep this guard on the backend too.
            # ------------------------------------------------

            if next_order > configured_question_count:
                logger.info(
                    "Adaptive generation skipped because "
                    "question %s is the final configured slot.",
                    current_order,
                )

                raise HTTPException(
                    status_code=400,
                    detail=(
                        "The current question is the final "
                        "configured interview question."
                    ),
                )

            # ------------------------------------------------
            # ADAPTIVE ENGINE
            # ------------------------------------------------

            engine = AdaptiveInterviewEngine(
                provider="groq"
            )

            previous_question_texts = [
                item.get("question", "")
                for item in previous_questions
                if item.get("question")
            ]

            result = (
                await engine.generate_next_question(
                    current_question=(
                        current_question.get(
                            "question",
                            "",
                        )
                    ),
                    current_category=(
                        current_question.get(
                            "category",
                            "technical",
                        )
                    ),
                    current_difficulty=(
                        current_question.get(
                            "difficulty",
                            "medium",
                        )
                    ),
                    current_skill=(
                        current_question.get(
                            "skill",
                            "",
                        )
                    ),
                    current_expected_topics=(
                        current_question.get(
                            "expected_topics",
                            [],
                        )
                        or []
                    ),
                    technical_score=int(
                        evaluation.get(
                            "technical_score",
                            0,
                        )
                    ),
                    relevance_score=int(
                        evaluation.get(
                            "relevance_score",
                            0,
                        )
                    ),
                    clarity_score=int(
                        evaluation.get(
                            "clarity_score",
                            0,
                        )
                    ),
                    depth_score=int(
                        evaluation.get(
                            "depth_score",
                            0,
                        )
                    ),
                    role=role,
                    job_description=job_description,
                    previous_questions=(
                        previous_question_texts
                    ),
                    candidate_answer=(
                        answer.get(
                            "answer_text",
                            "",
                        )
                    ),
                )
            )

            # ------------------------------------------------
            # FIND THE NEXT QUESTION SLOT
            # ------------------------------------------------

            existing_next_question = None

            for item in previous_questions:
                item_order = int(
                    item.get(
                        "question_order",
                        0,
                    )
                    or 0
                )

                if item_order == next_order:
                    existing_next_question = item
                    break

            # ------------------------------------------------
            # PREPARE ADAPTIVE QUESTION
            # ------------------------------------------------

            question_payload = {
                "question": (
                    result.question.question
                ),
                "category": (
                    result.question.category
                ),
                "difficulty": (
                    result.question.difficulty
                ),
                "skill": (
                    result.question.skill
                ),
                "expected_topics": (
                    result.question.expected_topics
                ),
                "question_order": next_order,
            }

            # ------------------------------------------------
            # REPLACE EXISTING SLOT
            # ------------------------------------------------

            if existing_next_question:
                logger.info(
                    "Replacing adaptive question slot %s "
                    "for session %s.",
                    next_order,
                    session_id,
                )

                persisted_question = (
                    await _update_question(
                        client,
                        str(
                            existing_next_question["id"]
                        ),
                        question_payload,
                    )
                )

            # ------------------------------------------------
            # INSERT ONLY IF THE SLOT DOES NOT EXIST
            # ------------------------------------------------

            else:
                logger.info(
                    "Creating adaptive question slot %s "
                    "for session %s.",
                    next_order,
                    session_id,
                )

                persisted_question = (
                    await _insert_question(
                        client,
                        {
                            "session_id": session_id,
                            **question_payload,
                        },
                    )
                )

            # ------------------------------------------------
            # UPDATE SESSION POSITION
            # ------------------------------------------------

            await _update_session_question_number(
                client,
                session_id,
                next_order,
            )

            # ------------------------------------------------
            # RESPONSE
            # ------------------------------------------------

            return AdaptiveNextQuestionResponse(
                question_id=str(
                    persisted_question["id"]
                ),
                question=(
                    persisted_question["question"]
                ),
                category=(
                    persisted_question["category"]
                ),
                difficulty=(
                    persisted_question["difficulty"]
                ),
                skill=(
                    persisted_question.get(
                        "skill",
                        "",
                    )
                    or ""
                ),
                expected_topics=(
                    persisted_question.get(
                        "expected_topics",
                        [],
                    )
                    or []
                ),
                strategy=(
                    result.decision.strategy
                ),
                focus_dimension=(
                    result.decision.focus_dimension
                ),
                reason=(
                    result.decision.reason
                ),
                priority=(
                    result.decision.priority
                ),
                question_order=next_order,
            )

    except HTTPException:
        raise

    except httpx.HTTPError as exc:
        logger.exception(
            "Supabase request failed during adaptive interview."
        )

        raise HTTPException(
            status_code=502,
            detail=(
                "Interview database request failed."
            ),
        ) from exc

    except RuntimeError as exc:
        logger.exception(
            "Adaptive interviewer failed."
        )

        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        logger.exception(
            "Unexpected adaptive interviewer error."
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Adaptive interview generation failed."
            ),
        ) from exc
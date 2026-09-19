"""
SmartHire Phase 4J
Interview Report + Interview History API
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.api.auth import get_current_user
from backend.services.interview.report_engine import (
    build_interview_report,
)


logger = logging.getLogger("smarthire.api.interview_reports")


router = APIRouter(
    prefix="/api/v1/interviews",
    tags=["Interview Reports"],
)


# ============================================================
# SUPABASE
# ============================================================

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()


def _supabase_headers() -> Dict[str, str]:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError(
            "SUPABASE_URL or SUPABASE_KEY is not configured."
        )

    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }


def _supabase_url(table: str) -> str:
    return (
        f"{SUPABASE_URL.rstrip('/')}"
        f"/rest/v1/{table}"
    )


# ============================================================
# RESPONSE MODELS
# ============================================================

class InterviewReportResponse(BaseModel):
    id: str | None = None
    session_id: str

    role: str
    interview_type: str
    difficulty: str
    status: str

    total_questions: int
    answered_questions: int
    evaluated_questions: int

    overall_score: int
    technical_score: int
    communication_score: int
    problem_solving_score: int

    strengths: List[str]
    weaknesses: List[str]
    recommended_topics: List[str]

    summary: str

    questions: List[Dict[str, Any]]

    created_at: str | None = None


class InterviewHistoryItem(BaseModel):
    session_id: str

    role: str
    interview_type: str
    difficulty: str
    status: str

    total_questions: int
    answered_questions: int
    evaluated_questions: int

    overall_score: int | None = None
    technical_score: int | None = None
    communication_score: int | None = None
    problem_solving_score: int | None = None

    created_at: str | None = None
    completed_at: str | None = None


# ============================================================
# DATABASE HELPERS
# ============================================================

async def _select(
    client: httpx.AsyncClient,
    table: str,
    params: Dict[str, str],
) -> List[Dict[str, Any]]:

    response = await client.get(
        _supabase_url(table),
        headers=_supabase_headers(),
        params=params,
    )

    response.raise_for_status()

    data = response.json()

    if not isinstance(data, list):
        return []

    return data


async def _get_owned_session(
    client: httpx.AsyncClient,
    session_id: str,
    user_id: str,
) -> Dict[str, Any]:

    rows = await _select(
        client,
        "interview_sessions",
        {
            "id": f"eq.{session_id}",
            "user_id": f"eq.{user_id}",
            "select": "*",
            "limit": "1",
        },
    )

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview session not found.",
        )

    return rows[0]


async def _get_session_data(
    client: httpx.AsyncClient,
    session_id: str,
) -> Dict[str, List[Dict[str, Any]]]:

    questions = await _select(
        client,
        "interview_questions",
        {
            "session_id": f"eq.{session_id}",
            "select": "*",
            "order": "question_order.asc",
        },
    )

    answers = await _select(
        client,
        "interview_answers",
        {
            "session_id": f"eq.{session_id}",
            "select": "*",
            "order": "created_at.asc",
        },
    )

    evaluations = await _select(
        client,
        "interview_evaluations",
        {
            "session_id": f"eq.{session_id}",
            "select": "*",
            "order": "created_at.asc",
        },
    )

    return {
        "questions": questions,
        "answers": answers,
        "evaluations": evaluations,
    }


async def _get_existing_report(
    client: httpx.AsyncClient,
    session_id: str,
) -> Dict[str, Any] | None:

    rows = await _select(
        client,
        "interview_reports",
        {
            "session_id": f"eq.{session_id}",
            "select": "*",
            "limit": "1",
        },
    )

    return rows[0] if rows else None


async def _persist_report(
    client: httpx.AsyncClient,
    report: Dict[str, Any],
) -> Dict[str, Any]:

    payload = {
        "session_id": report["session_id"],
        "overall_score": report["overall_score"],
        "technical_score": report["technical_score"],
        "communication_score": report["communication_score"],
        "problem_solving_score": report["problem_solving_score"],
        "strengths": report["strengths"],
        "weaknesses": report["weaknesses"],
        "recommended_topics": report[
            "recommended_topics"
        ],
        "summary": report["summary"],
    }

    response = await client.post(
        _supabase_url("interview_reports"),
        headers={
            **_supabase_headers(),
            "Prefer": "resolution=merge-duplicates,return=representation",
        },
        params={
            "on_conflict": "session_id",
        },
        json=payload,
    )

    response.raise_for_status()

    rows = response.json()

    if not rows:
        raise RuntimeError(
            "Interview report was not persisted."
        )

    return rows[0]


# ============================================================
# BUILD REPORT
# ============================================================

async def _build_and_persist_report(
    client: httpx.AsyncClient,
    session: Dict[str, Any],
) -> Dict[str, Any]:

    session_id = str(session["id"])

    data = await _get_session_data(
        client,
        session_id,
    )

    report = build_interview_report(
        session=session,
        questions=data["questions"],
        answers=data["answers"],
        evaluations=data["evaluations"],
    )

    persisted = await _persist_report(
        client,
        report,
    )

    report["id"] = persisted.get("id")
    report["created_at"] = persisted.get(
        "created_at"
    )

    return report


# ============================================================
# GET SINGLE INTERVIEW REPORT
# ============================================================

@router.get(
    "/{session_id}/report",
    response_model=InterviewReportResponse,
)
async def get_interview_report(
    session_id: str,
    user_id: str = Depends(get_current_user),
):

    try:
        async with httpx.AsyncClient(
            timeout=30.0
        ) as client:

            session = await _get_owned_session(
                client,
                session_id,
                user_id,
            )

            if session.get("status") != "completed":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        "Interview report is available "
                        "after the interview is completed."
                    ),
                )

            report = await _build_and_persist_report(
                client,
                session,
            )

            return report

    except HTTPException:
        raise

    except httpx.HTTPError as exc:
        logger.exception(
            "Supabase request failed while building report."
        )

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not load interview report.",
        ) from exc

    except Exception as exc:
        logger.exception(
            "Unexpected interview report failure."
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not generate interview report.",
        ) from exc


# ============================================================
# INTERVIEW HISTORY
# ============================================================

@router.get(
    "/history",
    response_model=List[InterviewHistoryItem],
)
async def get_interview_history(
    user_id: str = Depends(get_current_user),
):

    try:
        async with httpx.AsyncClient(
            timeout=30.0
        ) as client:

            sessions = await _select(
                client,
                "interview_sessions",
                {
                    "user_id": f"eq.{user_id}",
                    "select": "*",
                    "order": "created_at.desc",
                },
            )

            if not sessions:
                return []

            session_ids = [
                str(item["id"])
                for item in sessions
            ]

            reports = await _select(
                client,
                "interview_reports",
                {
                    "session_id": (
                        "in.("
                        + ",".join(session_ids)
                        + ")"
                    ),
                    "select": "*",
                },
            )

            report_by_session = {
                str(item["session_id"]): item
                for item in reports
            }

            answers = await _select(
                client,
                "interview_answers",
                {
                    "session_id": (
                        "in.("
                        + ",".join(session_ids)
                        + ")"
                    ),
                    "select": "session_id,id",
                },
            )

            evaluations = await _select(
                client,
                "interview_evaluations",
                {
                    "session_id": (
                        "in.("
                        + ",".join(session_ids)
                        + ")"
                    ),
                    "select": "session_id,id",
                },
            )

            answer_counts: Dict[str, int] = {}

            for answer in answers:
                key = str(answer["session_id"])
                answer_counts[key] = (
                    answer_counts.get(key, 0) + 1
                )

            evaluation_counts: Dict[str, int] = {}

            for evaluation in evaluations:
                key = str(evaluation["session_id"])
                evaluation_counts[key] = (
                    evaluation_counts.get(key, 0) + 1
                )

            result = []

            for session in sessions:

                session_id = str(session["id"])

                configuration = (
                    session.get("configuration")
                    or {}
                )

                report = report_by_session.get(
                    session_id
                )

                question_count = int(
                    configuration.get(
                        "question_count",
                        10,
                    )
                    or 10
                )

                result.append(
                    {
                        "session_id": session_id,
                        "role": session.get(
                            "role",
                            "",
                        ),
                        "interview_type": session.get(
                            "interview_type",
                            "mixed",
                        ),
                        "difficulty": session.get(
                            "difficulty",
                            "medium",
                        ),
                        "status": session.get(
                            "status",
                            "not_started",
                        ),
                        "total_questions": question_count,
                        "answered_questions": (
                            answer_counts.get(
                                session_id,
                                0,
                            )
                        ),
                        "evaluated_questions": (
                            evaluation_counts.get(
                                session_id,
                                0,
                            )
                        ),
                        "overall_score": (
                            report.get(
                                "overall_score"
                            )
                            if report
                            else None
                        ),
                        "technical_score": (
                            report.get(
                                "technical_score"
                            )
                            if report
                            else None
                        ),
                        "communication_score": (
                            report.get(
                                "communication_score"
                            )
                            if report
                            else None
                        ),
                        "problem_solving_score": (
                            report.get(
                                "problem_solving_score"
                            )
                            if report
                            else None
                        ),
                        "created_at": session.get(
                            "created_at"
                        ),
                        "completed_at": session.get(
                            "completed_at"
                        ),
                    }
                )

            return result

    except Exception as exc:
        logger.exception(
            "Failed to load interview history."
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not load interview history.",
        ) from exc
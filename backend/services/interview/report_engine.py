"""
SmartHire Interview Report Engine.

Phase 4J.1

Responsibilities:
- Aggregate persisted interview questions, answers, and evaluations.
- Calculate the final interview score.
- Preserve question-by-question performance.
- Calculate aggregate technical, communication, and
  problem-solving metrics.
- Collect demonstrated strengths and weaknesses.
- Produce data ready for interview_reports persistence.

This module does NOT access Supabase.

Database access belongs to the API layer.
"""

from __future__ import annotations

from typing import Any, Dict, List


# ============================================================
# HELPERS
# ============================================================


def _safe_int(
    value: Any,
    default: int = 0,
) -> int:
    """
    Convert a value into a bounded integer score.
    """

    try:
        number = int(value)
    except (TypeError, ValueError):
        return default

    return max(
        0,
        min(100, number),
    )


def _unique_strings(
    values: List[str],
    limit: int = 10,
) -> List[str]:
    """
    Remove empty and duplicate strings while preserving order.
    """

    result: List[str] = []
    seen = set()

    for value in values:
        text = str(value or "").strip()

        if not text:
            continue

        normalized = text.lower()

        if normalized in seen:
            continue

        seen.add(normalized)
        result.append(text)

        if len(result) >= limit:
            break

    return result


# ============================================================
# QUESTION REPORT
# ============================================================


def _build_question_report(
    question: Dict[str, Any],
    answer: Dict[str, Any] | None,
    evaluation: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """
    Build the report representation for one interview question.
    """

    question_id = str(
        question.get("id", "")
    )

    question_order = _safe_int(
        question.get("question_order", 0)
    )

    result: Dict[str, Any] = {
        "question_id": question_id,
        "question_order": question_order,
        "question": question.get(
            "question",
            "",
        ),
        "category": question.get(
            "category",
            "technical",
        ),
        "difficulty": question.get(
            "difficulty",
            "medium",
        ),
        "skill": question.get(
            "skill",
            "",
        ) or "",
        "answer": None,
        "evaluation": None,
        "answered": False,
    }

    if answer:
        result["answer"] = {
            "id": str(
                answer.get("id", "")
            ),
            "answer_text": answer.get(
                "answer_text",
                "",
            ),
            "answer_source": answer.get(
                "answer_source",
                "voice",
            ),
            "answered_at": answer.get(
                "answered_at"
            ),
        }

        result["answered"] = bool(
            str(
                answer.get(
                    "answer_text",
                    "",
                )
            ).strip()
        )

    if evaluation:
        result["evaluation"] = {
            "id": str(
                evaluation.get("id", "")
            ),
            "technical_score": _safe_int(
                evaluation.get(
                    "technical_score"
                )
            ),
            "relevance_score": _safe_int(
                evaluation.get(
                    "relevance_score"
                )
            ),
            "clarity_score": _safe_int(
                evaluation.get(
                    "clarity_score"
                )
            ),
            "depth_score": _safe_int(
                evaluation.get(
                    "depth_score"
                )
            ),
            "overall_score": _safe_int(
                evaluation.get(
                    "overall_score"
                )
            ),
            "feedback": evaluation.get(
                "feedback",
                "",
            ),
            "strengths": (
                evaluation.get(
                    "strengths",
                    [],
                )
                or []
            ),
            "weaknesses": (
                evaluation.get(
                    "weaknesses",
                    [],
                )
                or []
            ),
        }

    return result


# ============================================================
# MAIN REPORT BUILDER
# ============================================================


def build_interview_report(
    *,
    session: Dict[str, Any],
    questions: List[Dict[str, Any]],
    answers: List[Dict[str, Any]],
    evaluations: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Build a complete interview report from persisted data.

    The function intentionally does not call an LLM.

    All numerical interview scores are derived from the
    persisted evaluation records.
    """

    # --------------------------------------------------------
    # INDEX ANSWERS
    # --------------------------------------------------------

    answers_by_question: Dict[str, Dict[str, Any]] = {}

    for answer in answers:
        question_id = str(
            answer.get("question_id", "")
        )

        if question_id:
            answers_by_question[question_id] = answer

    # --------------------------------------------------------
    # INDEX EVALUATIONS
    # --------------------------------------------------------

    evaluations_by_answer: Dict[str, Dict[str, Any]] = {}

    for evaluation in evaluations:
        answer_id = str(
            evaluation.get("answer_id", "")
        )

        if answer_id:
            evaluations_by_answer[answer_id] = evaluation

    # --------------------------------------------------------
    # BUILD QUESTION REPORTS
    # --------------------------------------------------------

    question_reports: List[Dict[str, Any]] = []

    for question in sorted(
        questions,
        key=lambda item: _safe_int(
            item.get("question_order", 0)
        ),
    ):
        question_id = str(
            question.get("id", "")
        )

        answer = answers_by_question.get(
            question_id
        )

        evaluation = None

        if answer:
            answer_id = str(
                answer.get("id", "")
            )

            evaluation = evaluations_by_answer.get(
                answer_id
            )

        question_reports.append(
            _build_question_report(
                question=question,
                answer=answer,
                evaluation=evaluation,
            )
        )

    # --------------------------------------------------------
    # ONLY EVALUATED ANSWERS COUNT TOWARD FINAL SCORE
    # --------------------------------------------------------

    evaluated_questions = [
        item
        for item in question_reports
        if item.get("evaluation") is not None
    ]

    total_questions = len(
        question_reports
    )

    answered_questions = sum(
        1
        for item in question_reports
        if item.get("answered")
    )

    evaluated_count = len(
        evaluated_questions
    )

    # --------------------------------------------------------
    # EMPTY INTERVIEW
    # --------------------------------------------------------

    if evaluated_count == 0:
        return {
            "session_id": str(
                session.get("id", "")
            ),
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
                "",
            ),
            "total_questions": total_questions,
            "answered_questions": answered_questions,
            "evaluated_questions": 0,
            "overall_score": 0,
            "technical_score": 0,
            "communication_score": 0,
            "problem_solving_score": 0,
            "strengths": [],
            "weaknesses": [],
            "recommended_topics": [],
            "summary": "No evaluated interview answers are available yet.",
            "questions": question_reports,
        }

    # --------------------------------------------------------
    # SCORE AGGREGATION
    # --------------------------------------------------------

    technical_scores: List[int] = []
    relevance_scores: List[int] = []
    clarity_scores: List[int] = []
    depth_scores: List[int] = []
    overall_scores: List[int] = []

    for item in evaluated_questions:
        evaluation = item["evaluation"]

        technical_scores.append(
            _safe_int(
                evaluation.get(
                    "technical_score"
                )
            )
        )

        relevance_scores.append(
            _safe_int(
                evaluation.get(
                    "relevance_score"
                )
            )
        )

        clarity_scores.append(
            _safe_int(
                evaluation.get(
                    "clarity_score"
                )
            )
        )

        depth_scores.append(
            _safe_int(
                evaluation.get(
                    "depth_score"
                )
            )
        )

        overall_scores.append(
            _safe_int(
                evaluation.get(
                    "overall_score"
                )
            )
        )

    def average(
        values: List[int],
    ) -> int:
        if not values:
            return 0

        return max(
            0,
            min(
                100,
                round(
                    sum(values) / len(values)
                ),
            ),
        )

    overall_score = average(
        overall_scores
    )

    technical_score = average(
        technical_scores
    )

    # --------------------------------------------------------
    # COMMUNICATION
    # --------------------------------------------------------
    #
    # The current evaluation model has no separate
    # communication_score.
    #
    # Clarity is therefore used as the current communication
    # proxy.
    #
    # This keeps the report deterministic and consistent with
    # the existing evaluation model.
    # --------------------------------------------------------

    communication_score = average(
        clarity_scores
    )

    # --------------------------------------------------------
    # PROBLEM SOLVING
    # --------------------------------------------------------
    #
    # The current evaluation model has no separate
    # problem_solving_score.
    #
    # Depth is therefore used as the current problem-solving
    # proxy.
    #
    # Later, if the evaluation model adds an explicit
    # problem-solving dimension, this calculation can be
    # upgraded without changing the report UI.
    # --------------------------------------------------------

    problem_solving_score = average(
        depth_scores
    )

    # --------------------------------------------------------
    # STRENGTHS / WEAKNESSES
    # --------------------------------------------------------

    strengths: List[str] = []
    weaknesses: List[str] = []

    for item in evaluated_questions:
        evaluation = item["evaluation"]

        strengths.extend(
            evaluation.get(
                "strengths",
                [],
            )
            or []
        )

        weaknesses.extend(
            evaluation.get(
                "weaknesses",
                [],
            )
            or []
        )

    strengths = _unique_strings(
        strengths,
        limit=10,
    )

    weaknesses = _unique_strings(
        weaknesses,
        limit=10,
    )

    # --------------------------------------------------------
    # RECOMMENDED TOPICS
    # --------------------------------------------------------
    #
    # Topics are derived deterministically from questions
    # associated with weaker evaluations.
    #
    # We do not call the LLM here.
    # --------------------------------------------------------

    recommended_topics: List[str] = []

    for item in evaluated_questions:
        evaluation = item["evaluation"]

        question_score = _safe_int(
            evaluation.get(
                "overall_score"
            )
        )

        if question_score >= 60:
            continue

        skill = str(
            item.get(
                "skill",
                "",
            )
            or ""
        ).strip()

        if skill:
            recommended_topics.append(
                skill
            )

    recommended_topics = _unique_strings(
        recommended_topics,
        limit=10,
    )

    # --------------------------------------------------------
    # FINAL REPORT
    # --------------------------------------------------------
# ============================================================
# FINAL REPORT
# ============================================================

    summary = (
    f"Interview completed with an overall score of {overall_score}/100. "
    f"Technical performance was {technical_score}/100, "
    f"communication was {communication_score}/100, "
    f"and problem-solving performance was {problem_solving_score}/100."
)

    return {
    "session_id": str(
        session.get("id", "")
    ),
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
        "",
    ),
    "total_questions": total_questions,
    "answered_questions": answered_questions,
    "evaluated_questions": evaluated_count,
    "overall_score": overall_score,
    "technical_score": technical_score,
    "communication_score": communication_score,
    "problem_solving_score": problem_solving_score,
    "strengths": strengths,
    "weaknesses": weaknesses,
    "recommended_topics": recommended_topics,
    "summary": summary,
    "questions": question_reports,
}
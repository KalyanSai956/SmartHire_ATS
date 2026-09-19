"""
SmartHire Interview Evaluation Engine.

Responsibilities:
- evaluate candidate answers using the existing LLM Gateway
- enforce explicit evaluation rubrics
- validate structured LLM output
- calculate a consistent overall score
- return data ready for interview_evaluations persistence

This module does NOT directly access Supabase.
Database persistence belongs to the API layer.
"""

import json
import logging
from typing import Any, Dict, List

from pydantic import BaseModel, Field, field_validator

from backend.services.interview.rubrics import (
    build_evaluation_rubric,
)
from backend.services.llm.gateway import (
    LLMGateway,
)


logger = logging.getLogger(
    "smarthire.interview.evaluation"
)


# ============================================================
# PYDANTIC MODELS
# ============================================================

class InterviewEvaluationResult(BaseModel):
    """
    Structured result returned by the evaluation engine.
    """

    technical_score: int = Field(
        ...,
        ge=0,
        le=100,
    )

    relevance_score: int = Field(
        ...,
        ge=0,
        le=100,
    )

    clarity_score: int = Field(
        ...,
        ge=0,
        le=100,
    )

    depth_score: int = Field(
        ...,
        ge=0,
        le=100,
    )

    overall_score: int = Field(
        ...,
        ge=0,
        le=100,
    )

    feedback: str = Field(
        ...,
        min_length=1,
        max_length=5000,
    )

    strengths: List[str] = Field(
        default_factory=list,
    )

    weaknesses: List[str] = Field(
        default_factory=list,
    )

    @field_validator(
        "feedback",
        mode="before",
    )
    @classmethod
    def clean_feedback(
        cls,
        value: Any,
    ) -> str:
        value = str(value or "").strip()

        if not value:
            raise ValueError(
                "Feedback cannot be empty."
            )

        return value

    @field_validator(
        "strengths",
        "weaknesses",
        mode="before",
    )
    @classmethod
    def clean_lists(
        cls,
        value: Any,
    ) -> List[str]:
        if value is None:
            return []

        if not isinstance(value, list):
            value = [value]

        cleaned = []

        for item in value:
            text = str(item).strip()

            if text:
                cleaned.append(text)

        return cleaned[:10]


# ============================================================
# ENGINE
# ============================================================

class InterviewEvaluationEngine:
    """
    Evaluates one candidate answer.

    The engine is deliberately provider-agnostic.
    It uses the existing SmartHire LLM abstraction.
    """

    def __init__(
    self,
    provider: str = "groq",
    api_key: str | None = None,
    model: str | None = None,
):
        """
    Initialize the interview evaluation engine.

    LLMGateway is responsible for creating the actual
    provider instance. We therefore pass the provider
    configuration directly to the gateway.
    """

        self.gateway = LLMGateway(
        provider=provider,
        api_key=api_key,
        model=model,
    )

    # ========================================================
    # PUBLIC METHOD
    # ========================================================

    async def evaluate_answer(
        self,
        *,
        question: str,
        category: str,
        difficulty: str,
        skill: str,
        expected_topics: List[str],
        candidate_answer: str,
        role: str = "",
        job_description: str = "",
    ) -> InterviewEvaluationResult:
        """
        Evaluate one candidate answer.
        """

        question = (question or "").strip()
        candidate_answer = (
            candidate_answer or ""
        ).strip()

        if not question:
            raise ValueError(
                "Question cannot be empty."
            )

        if not candidate_answer:
            raise ValueError(
                "Candidate answer cannot be empty."
            )

        prompt = self._build_prompt(
            question=question,
            category=category,
            difficulty=difficulty,
            skill=skill,
            expected_topics=expected_topics,
            candidate_answer=candidate_answer,
            role=role,
            job_description=job_description,
        )

        try:
           raw_result = await self.gateway.generate_json(
    messages=[
        {
            "role": "system",
            "content": (
                "You are an expert technical interviewer and "
                "candidate evaluator. Evaluate the candidate's "
                "answer objectively using the supplied rubric. "
                "Return only valid JSON."
            ),
        },
        {
            "role": "user",
            "content": prompt,
        },
    ]
)

        except Exception as exc:
            logger.exception(
                "Interview answer evaluation failed."
            )

            raise RuntimeError(
                "LLM evaluation failed."
            ) from exc

        result = self._validate_llm_result(
            raw_result
        )

        # The LLM provides dimension scores.
        # SmartHire calculates the final overall score
        # deterministically so the final score cannot drift
        # independently from the four dimensions.
        result.overall_score = (
            self._calculate_overall_score(
                technical=result.technical_score,
                relevance=result.relevance_score,
                clarity=result.clarity_score,
                depth=result.depth_score,
            )
        )

        return result

    # ========================================================
    # PROMPT
    # ========================================================

    def _build_prompt(
        self,
        *,
        question: str,
        category: str,
        difficulty: str,
        skill: str,
        expected_topics: List[str],
        candidate_answer: str,
        role: str,
        job_description: str,
    ) -> str:
        rubric = build_evaluation_rubric(
            category
        )

        expected_topics_text = (
            "\n".join(
                f"- {topic}"
                for topic in expected_topics
                if topic
            )
            or "- No explicit expected topics."
        )

        job_description_text = (
            job_description[:8000]
            if job_description
            else "No job description provided."
        )

        role_text = (
            role
            if role
            else "Not specified."
        )

        return f"""
You are SmartHire's interview evaluation engine.

Evaluate ONE candidate answer against ONE interview question.

Return the result as VALID JSON.

Do not return Markdown.
Do not wrap the JSON in ``` fences.
Do not include commentary outside the JSON.

============================================================
INTERVIEW CONTEXT
============================================================

Role:
{role_text}

Question category:
{category}

Difficulty:
{difficulty}

Primary skill:
{skill or "Not specified."}

============================================================
QUESTION
============================================================

{question}

============================================================
EXPECTED TOPICS
============================================================

{expected_topics_text}

These are evaluation guidance, not mandatory keywords.
A candidate can demonstrate understanding using different
wording or an alternative technically valid explanation.

============================================================
JOB DESCRIPTION
============================================================

{job_description_text}

Use the job description only as contextual information.
Do not penalize the candidate for information unrelated to
the question.

============================================================
CANDIDATE ANSWER
============================================================

{candidate_answer}

============================================================
RUBRIC
============================================================

{rubric}

============================================================
IMPORTANT EVALUATION RULES
============================================================

1. Evaluate ONLY the answer provided.

2. Do not invent facts about the candidate.

3. Do not assume that the candidate knows something that they
   did not demonstrate.

4. Do not require exact wording from expected_topics.

5. A concise answer can still receive a strong score if it is
   correct and sufficiently addresses the question.

6. Do not reward technical buzzwords without demonstrated
   understanding.

7. If the answer is partially correct, score each dimension
   according to the actual evidence.

8. If the candidate completely misunderstands the question,
   relevance and technical scores should reflect that.

9. For behavioral answers, evaluate the actual situation,
   actions, reasoning, and outcome present in the answer.

10. For project answers, do not assume that the candidate
    actually built anything unless their answer provides
    evidence of understanding.

11. Keep feedback specific and actionable.

12. Strengths should describe things demonstrated in the
    answer.

13. Weaknesses should identify concrete missing or weak areas.

============================================================
REQUIRED JSON FORMAT
============================================================

{{
  "technical_score": 0,
  "relevance_score": 0,
  "clarity_score": 0,
  "depth_score": 0,
  "overall_score": 0,
  "feedback": "Specific actionable feedback.",
  "strengths": [
    "Demonstrated strength"
  ],
  "weaknesses": [
    "Specific improvement area"
  ]
}}

The four dimension scores MUST be integers from 0 to 100.

The overall_score field may be provided, but SmartHire will
recalculate it from the four dimension scores.

Return JSON now.
"""

    # ========================================================
    # VALIDATION
    # ========================================================

    @staticmethod
    def _validate_llm_result(
        raw_result: Any,
    ) -> InterviewEvaluationResult:
        """
        Convert the LLM result into a validated Pydantic model.
        """

        if isinstance(raw_result, str):
            raw_result = raw_result.strip()

            try:
                raw_result = json.loads(
                    raw_result
                )

            except json.JSONDecodeError as exc:
                logger.error(
                    "LLM returned invalid JSON."
                )

                raise ValueError(
                    "LLM evaluation returned invalid JSON."
                ) from exc

        if not isinstance(raw_result, dict):
            raise ValueError(
                "LLM evaluation must be a JSON object."
            )

        required_fields = [
            "technical_score",
            "relevance_score",
            "clarity_score",
            "depth_score",
            "feedback",
        ]

        missing_fields = [
            field
            for field in required_fields
            if field not in raw_result
        ]

        if missing_fields:
            raise ValueError(
                "LLM evaluation is missing required fields: "
                + ", ".join(missing_fields)
            )

        try:
            return InterviewEvaluationResult(
                **raw_result
            )

        except Exception as exc:
            logger.exception(
                "LLM evaluation failed schema validation."
            )

            raise ValueError(
                "LLM evaluation returned invalid evaluation data."
            ) from exc

    # ========================================================
    # OVERALL SCORE
    # ========================================================

    @staticmethod
    def _calculate_overall_score(
        *,
        technical: int,
        relevance: int,
        clarity: int,
        depth: int,
    ) -> int:
        """
        Calculate a deterministic overall score.

        Technical understanding receives the highest weight.
        """

        weighted_score = (
            technical * 0.35
            + relevance * 0.25
            + clarity * 0.15
            + depth * 0.25
        )

        return max(
            0,
            min(
                100,
                round(weighted_score),
            ),
        )
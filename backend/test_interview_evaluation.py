"""
Phase 4E — Interview Evaluation Engine Test

Tests:
1. Rubric construction
2. Groq provider connectivity
3. Structured JSON evaluation
4. Pydantic validation
5. Deterministic overall score calculation
"""

import asyncio
import json

from backend.services.interview.evaluation_engine import (
    InterviewEvaluationEngine,
)
from backend.services.interview.rubrics import (
    build_evaluation_rubric,
)


# ============================================================
# TEST DATA
# ============================================================

QUESTION = """
Explain the difference between threading and multiprocessing
in Python. When would you choose one over the other?
"""

CATEGORY = "technical"

DIFFICULTY = "medium"

SKILL = "Python"

EXPECTED_TOPICS = [
    "GIL",
    "I/O-bound workloads",
    "CPU-bound workloads",
    "threading",
    "multiprocessing",
]

CANDIDATE_ANSWER = """
Python threading is useful when the program is waiting on I/O
because multiple threads can make progress while one thread is
waiting. The GIL means CPU-bound Python code does not normally
get true parallel execution across threads.

For CPU-bound workloads, multiprocessing can be better because
each process has its own Python interpreter and GIL, allowing
work to run in parallel across CPU cores.

Threads are usually lighter and have shared memory, while
processes have more isolation but higher overhead for creating
and communicating between them.
"""


# ============================================================
# TEST
# ============================================================

async def main():
    print("=" * 70)
    print("PHASE 4E — INTERVIEW EVALUATION ENGINE TEST")
    print("=" * 70)

    # --------------------------------------------------------
    # 1. RUBRIC
    # --------------------------------------------------------

    print("\n[1/4] Testing evaluation rubric...")

    rubric = build_evaluation_rubric(
        CATEGORY
    )

    assert "TECHNICAL SCORE" in rubric
    assert "RELEVANCE SCORE" in rubric
    assert "CLARITY SCORE" in rubric
    assert "DEPTH SCORE" in rubric
    assert "0-100" in rubric

    print("Rubric loaded successfully.")

    # --------------------------------------------------------
    # 2. CREATE ENGINE
    # --------------------------------------------------------

    print("\n[2/4] Initializing Groq evaluation engine...")

    engine = InterviewEvaluationEngine(
        provider="groq"
    )

    provider_info = (
        engine.gateway.get_provider_info()
    )

    print("Provider info:")
    print(provider_info)

    assert provider_info["provider"] == "groq"
    assert provider_info["configured"] is True

    # --------------------------------------------------------
    # 3. EVALUATE
    # --------------------------------------------------------

    print("\n[3/4] Evaluating candidate answer...")
    print("\nQuestion:")
    print(QUESTION.strip())

    print("\nCandidate answer:")
    print(CANDIDATE_ANSWER.strip())

    result = await engine.evaluate_answer(
        question=QUESTION,
        category=CATEGORY,
        difficulty=DIFFICULTY,
        skill=SKILL,
        expected_topics=EXPECTED_TOPICS,
        candidate_answer=CANDIDATE_ANSWER,
        role="Python Backend Developer",
        job_description=(
            "Looking for a Python backend developer with "
            "knowledge of concurrency, APIs and scalable "
            "backend services."
        ),
    )

    # --------------------------------------------------------
    # 4. VALIDATION
    # --------------------------------------------------------

    print("\n[4/4] Validating evaluation result...")

    assert 0 <= result.technical_score <= 100
    assert 0 <= result.relevance_score <= 100
    assert 0 <= result.clarity_score <= 100
    assert 0 <= result.depth_score <= 100
    assert 0 <= result.overall_score <= 100

    assert result.feedback.strip()

    assert isinstance(
        result.strengths,
        list,
    )

    assert isinstance(
        result.weaknesses,
        list,
    )

    # Recalculate independently to verify
    # deterministic overall score.
    expected_overall = round(
        result.technical_score * 0.35
        + result.relevance_score * 0.25
        + result.clarity_score * 0.15
        + result.depth_score * 0.25
    )

    assert (
        result.overall_score
        == expected_overall
    )

    print("\nEvaluation result:")
    print("-" * 70)

    print(
        f"Technical Score : "
        f"{result.technical_score}/100"
    )

    print(
        f"Relevance Score : "
        f"{result.relevance_score}/100"
    )

    print(
        f"Clarity Score   : "
        f"{result.clarity_score}/100"
    )

    print(
        f"Depth Score     : "
        f"{result.depth_score}/100"
    )

    print(
        f"Overall Score   : "
        f"{result.overall_score}/100"
    )

    print("\nStrengths:")

    for item in result.strengths:
        print(f"  + {item}")

    print("\nWeaknesses:")

    for item in result.weaknesses:
        print(f"  - {item}")

    print("\nFeedback:")
    print(result.feedback)

    print("\nRaw validated JSON:")
    print(
        json.dumps(
            result.model_dump(),
            indent=2,
        )
    )

    print("\n" + "=" * 70)
    print("PHASE 4E TEST PASSED")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
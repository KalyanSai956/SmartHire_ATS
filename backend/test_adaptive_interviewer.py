"""
Phase 4F — Adaptive Interviewer Test

Tests:

1. Weak technical/depth performance produces
   a targeted follow-up strategy.

2. Strong performance increases difficulty.

3. Normal performance continues at the current level.

4. Groq generates a valid adaptive question.

Run:

    python -m backend.test_adaptive_interviewer
"""

import asyncio
import json


from backend.services.interview.adaptive_engine import (
    AdaptiveInterviewEngine,
)


# ============================================================
# TEST DATA
# ============================================================

CURRENT_QUESTION = (
    "Explain the difference between threading and "
    "multiprocessing in Python. When would you choose "
    "one over the other?"
)

CURRENT_ANSWER = """
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

EXPECTED_TOPICS = [
    "GIL behavior",
    "threading vs multiprocessing",
    "CPU-bound vs I/O-bound tasks",
    "process creation overhead",
]


# ============================================================
# TESTS
# ============================================================

async def main():

    print("=" * 70)
    print("PHASE 4F — ADAPTIVE INTERVIEWER TEST")
    print("=" * 70)

    # --------------------------------------------------------
    # 1. Weak performance
    # --------------------------------------------------------

    print()
    print("[1/4] Testing weak-performance adaptation...")

    engine = AdaptiveInterviewEngine(
        provider="groq"
    )

    weak_decision = engine._build_adaptive_decision(
        current_category="technical",
        current_difficulty="medium",
        current_skill="Python",
        technical_score=48,
        relevance_score=72,
        clarity_score=78,
        depth_score=45,
    )

    print()
    print("Weak-performance decision:")
    print("- Strategy :", weak_decision.strategy)
    print("- Focus    :", weak_decision.focus_dimension)
    print("- Skill    :", weak_decision.focus_skill)
    print("- Category :", weak_decision.next_category)
    print("- Difficulty:", weak_decision.next_difficulty)
    print("- Priority :", weak_decision.priority)
    print("- Reason   :", weak_decision.reason)

    assert weak_decision.strategy in {
        "targeted_technical_follow_up",
        "depth_follow_up",
    }

    assert weak_decision.priority == "high"

    print()
    print("Weak adaptation passed.")

    # --------------------------------------------------------
    # 2. Strong performance
    # --------------------------------------------------------

    print()
    print("[2/4] Testing strong-performance adaptation...")

    strong_decision = engine._build_adaptive_decision(
        current_category="technical",
        current_difficulty="medium",
        current_skill="Python",
        technical_score=94,
        relevance_score=92,
        clarity_score=90,
        depth_score=91,
    )

    print()
    print("Strong-performance decision:")
    print("- Strategy :", strong_decision.strategy)
    print("- Focus    :", strong_decision.focus_dimension)
    print("- Category :", strong_decision.next_category)
    print("- Difficulty:", strong_decision.next_difficulty)
    print("- Reason   :", strong_decision.reason)

    assert (
        strong_decision.strategy
        == "increase_difficulty"
    )

    assert (
        strong_decision.next_difficulty
        == "hard"
    )

    print()
    print("Strong adaptation passed.")

    # --------------------------------------------------------
    # 3. Normal performance
    # --------------------------------------------------------

    print()
    print("[3/4] Testing normal-performance adaptation...")

    normal_decision = engine._build_adaptive_decision(
        current_category="technical",
        current_difficulty="medium",
        current_skill="FastAPI",
        technical_score=72,
        relevance_score=76,
        clarity_score=80,
        depth_score=68,
    )

    print()
    print("Normal-performance decision:")
    print("- Strategy :", normal_decision.strategy)
    print("- Focus    :", normal_decision.focus_dimension)
    print("- Category :", normal_decision.next_category)
    print("- Difficulty:", normal_decision.next_difficulty)
    print("- Reason   :", normal_decision.reason)

    assert (
        normal_decision.strategy
        == "reinforce_and_progress"
    )

    assert (
        normal_decision.next_difficulty
        == "medium"
    )

    print()
    print("Normal adaptation passed.")

    # --------------------------------------------------------
    # 4. Real Groq generation
    # --------------------------------------------------------

    print()
    print("[4/4] Generating adaptive question with Groq...")

    result = await engine.generate_next_question(
        current_question=CURRENT_QUESTION,
        current_category="technical",
        current_difficulty="medium",
        current_skill="Python",
        current_expected_topics=EXPECTED_TOPICS,
        technical_score=48,
        relevance_score=72,
        clarity_score=78,
        depth_score=45,
        role="Python Backend Developer",
        job_description=(
            "Looking for a Python backend developer with "
            "experience in FastAPI, APIs, concurrency, "
            "databases, and scalable backend services."
        ),
        candidate_answer=CURRENT_ANSWER,
        previous_questions=[
            CURRENT_QUESTION,
        ],
    )

    print()
    print("Adaptive decision:")
    print("- Strategy :", result.decision.strategy)
    print("- Focus    :", result.decision.focus_dimension)
    print("- Skill    :", result.decision.focus_skill)
    print("- Category :", result.decision.next_category)
    print("- Difficulty:", result.decision.next_difficulty)
    print("- Priority :", result.decision.priority)
    print("- Reason   :", result.decision.reason)

    print()
    print("Generated next question:")
    print("-" * 70)
    print("Question :", result.question.question)
    print("Category :", result.question.category)
    print("Difficulty:", result.question.difficulty)
    print("Skill    :", result.question.skill)
    print(
        "Expected topics:",
        ", ".join(
            result.question.expected_topics
        ),
    )

    assert result.question.question

    assert (
        result.question.category
        == result.decision.next_category
    )

    assert (
        result.question.difficulty
        == result.decision.next_difficulty
    )

    assert isinstance(
        result.question.expected_topics,
        list,
    )

    print()
    print("Raw adaptive result:")
    print(
        json.dumps(
            result.model_dump(),
            indent=2,
        )
    )

    print()
    print("=" * 70)
    print("PHASE 4F TEST PASSED")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
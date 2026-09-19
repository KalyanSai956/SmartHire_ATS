import asyncio

from backend.services.interview_question_generator import (
    generate_interview_questions,
)


async def main():

    profile = {
        "username": "Sai",
        "skills": [
            "Python",
            "FastAPI",
            "React",
            "JavaScript",
            "MongoDB",
            "Machine Learning",
        ],
        "target_roles": [
            "Python Developer",
            "AI/ML Engineer",
        ],
        "experience": (
            "Fresher with academic and personal projects."
        ),
        "resume_filename": "resume.pdf",
        "resume_text": """
        Built SmartHire ATS using React, FastAPI,
        Python, spaCy, Sentence Transformers and Groq.

        Built CodeGuardian AI for GitHub repository
        intelligence and AI-powered code review.

        Developed MERN pharmacy management system.
        """,
    }

    print("=" * 60)
    print("PHASE 4D — INTERVIEW QUESTION GENERATION TEST")
    print("=" * 60)

    print("\nGenerating questions...\n")

    result = await generate_interview_questions(
        role="Python / AI-ML Engineer",
        job_description="""
        We are looking for a Python/AI-ML Engineer.

        Requirements:
        - Strong Python programming
        - FastAPI or backend development
        - REST APIs
        - Machine learning fundamentals
        - NLP experience
        - Familiarity with LLM applications
        - Problem solving
        """,
        interview_type="mixed",
        difficulty="medium",
        question_count=5,
        focus_areas=[
            "Python",
            "FastAPI",
            "Machine Learning",
            "NLP",
        ],
        include_coding=False,
        include_system_design=False,
        profile=profile,
    )

    print(
        f"Generated: {len(result.questions)} questions"
    )

    for index, question in enumerate(
        result.questions,
        start=1,
    ):
        print(f"\nQuestion {index}")
        print("-" * 40)
        print(f"Question: {question.question}")
        print(f"Category: {question.category}")
        print(f"Difficulty: {question.difficulty}")
        print(f"Skill: {question.skill}")
        print(
            "Expected topics: "
            + ", ".join(question.expected_topics)
        )

    assert len(result.questions) == 5

    question_texts = [
        question.question.strip().lower()
        for question in result.questions
    ]

    assert len(question_texts) == len(
        set(question_texts)
    )

    for question in result.questions:

        assert question.category in {
            "technical",
            "behavioral",
            "project",
            "problem_solving",
            "system_design",
            "coding",
        }

        assert question.difficulty in {
            "easy",
            "medium",
            "hard",
        }

        assert question.question.strip()

    print("\n" + "=" * 60)
    print("PHASE 4D TEST PASSED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
from backend.services.interview.report_engine import build_interview_report


def main():
    session = {
        "id": "test-session-001",
        "role": "Backend Engineer",
        "interview_type": "mixed",
        "difficulty": "medium",
        "status": "completed",
    }

    questions = [
        {
            "id": "q1",
            "question_order": 1,
            "question": "Explain Redis.",
            "category": "technical",
            "difficulty": "medium",
            "skill": "Redis",
        },
        {
            "id": "q2",
            "question_order": 2,
            "question": "Explain graceful worker shutdown.",
            "category": "system_design",
            "difficulty": "medium",
            "skill": "Distributed Systems",
        },
    ]

    answers = [
        {
            "id": "a1",
            "question_id": "q1",
            "answer_text": "Redis is an in-memory data store.",
            "answer_source": "voice",
        },
        {
            "id": "a2",
            "question_id": "q2",
            "answer_text": "Workers should stop accepting new jobs and finish active jobs.",
            "answer_source": "voice",
        },
    ]

    evaluations = [
        {
            "id": "e1",
            "answer_id": "a1",
            "technical_score": 90,
            "relevance_score": 90,
            "clarity_score": 80,
            "depth_score": 80,
            "overall_score": 85,
            "feedback": "Good explanation.",
            "strengths": ["Clear Redis fundamentals"],
            "weaknesses": ["Could explain persistence"],
        },
        {
            "id": "e2",
            "answer_id": "a2",
            "technical_score": 80,
            "relevance_score": 90,
            "clarity_score": 90,
            "depth_score": 70,
            "overall_score": 81,
            "feedback": "Good shutdown approach.",
            "strengths": ["Understands graceful shutdown"],
            "weaknesses": ["Could discuss signal handling"],
        },
    ]

    report = build_interview_report(
        session=session,
        questions=questions,
        answers=answers,
        evaluations=evaluations,
    )

    print("\n=== INTERVIEW REPORT TEST ===")
    print("Role:", report["role"])
    print("Total questions:", report["total_questions"])
    print("Answered:", report["answered_questions"])
    print("Evaluated:", report["evaluated_questions"])
    print("Overall:", report["overall_score"])
    print("Technical:", report["technical_score"])
    print("Communication:", report["communication_score"])
    print("Problem solving:", report["problem_solving_score"])

    print("\nQuestions:")

    for item in report["questions"]:
        print(
            f"Q{item['question_order']}: "
            f"{item['evaluation']['overall_score']}/100"
        )

    print("\nStrengths:")
    for item in report["strengths"]:
        print("-", item)

    print("\nWeaknesses:")
    for item in report["weaknesses"]:
        print("-", item)


if __name__ == "__main__":
    main()
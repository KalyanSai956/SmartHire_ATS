from backend.services.jd_intelligence_engine import (
    analyze_job_description,
)


SAMPLE_JD = """
Python Backend Developer

We are looking for a Python Backend Developer to build scalable
backend applications and APIs.

Requirements:
- Strong Python programming skills
- FastAPI or Django experience
- REST API development
- SQL and database knowledge
- MongoDB experience
- Docker
- Git and GitHub
- 2+ years of backend development experience
- Strong problem solving skills

Responsibilities:
- Build and maintain scalable backend applications
- Design and develop REST APIs
- Work with databases and backend services
- Collaborate with frontend engineers
- Write clean and maintainable code

Preferred Qualifications:
- Machine Learning experience
- NLP knowledge
- Kubernetes experience

Education:
- Bachelor's degree in Computer Science or related field
"""


def main():
    print("=" * 70)
    print("PHASE 3E — JD INTELLIGENCE TEST")
    print("=" * 70)

    result = analyze_job_description(SAMPLE_JD)

    print("\n[1] JOB PROFILE")

    print(f"Job Title: {result.job_title}")
    print(f"Seniority: {result.seniority}")
    print(f"Domain: {result.domain}")

    print("\n[2] REQUIRED SKILLS")

    for skill in result.required_skills:
        print(f"- {skill}")

    print("\n[3] PREFERRED SKILLS")

    for skill in result.preferred_skills:
        print(f"- {skill}")

    print("\n[4] EXPERIENCE")

    print(
        f"Minimum Years: "
        f"{result.experience_requirement.minimum_years}"
    )

    print(
        f"Raw: "
        f"{result.experience_requirement.raw_text}"
    )

    print("\n[5] RESPONSIBILITIES")

    for responsibility in result.responsibilities:
        print(f"- {responsibility}")

    print("\n[6] EDUCATION")

    for education in result.education_requirements:
        print(f"- {education}")

    print("\n[7] TECHNICAL REQUIREMENTS")

    for requirement in result.technical_requirements:
        print(
            f"- {requirement.requirement} "
            f"[{requirement.priority}]"
        )

    print("\n[8] SOFT SKILLS")

    for requirement in result.soft_skill_requirements:
        print(
            f"- {requirement.requirement} "
            f"[{requirement.priority}]"
        )

    print("\n[9] KEYWORDS")

    for keyword in result.keywords:
        print(f"- {keyword}")

    print("\n[10] JD QUALITY")

    print(f"Quality Score: {result.jd_quality_score}")

    print("\nStrengths:")

    for strength in result.strengths:
        print(f"- {strength}")

    print("\nWeaknesses:")

    for weakness in result.weaknesses:
        print(f"- {weakness}")

    # ---------------------------------------------------------------
    # Assertions
    # ---------------------------------------------------------------

    assert result.job_title is not None

    assert "python" in result.required_skills
    assert "fastapi" in result.required_skills
    assert "docker" in result.required_skills
    assert "git" in result.required_skills

    assert "machine learning" in result.preferred_skills
    assert "nlp" in result.preferred_skills
    assert "kubernetes" in result.preferred_skills

    assert result.experience_requirement.minimum_years == 2.0

    assert len(result.responsibilities) >= 3

    assert result.jd_quality_score > 0

    assert result.must_have_count > 0
    assert result.preferred_count > 0

    print("\n" + "=" * 70)
    print("PHASE 3E JD INTELLIGENCE TEST PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()
from backend.services.resume_parser import parse_resume_profile
from backend.services.resume_quality_engine import analyze_resume_quality
from backend.services.advanced_ats_engine import calculate_advanced_ats_score


sample_resume = """
Pasupuleti Sai Kalyan
7013225581
kalyansai956@gmail.com
linkedin.com/in/saikalyanpasupuleti
github.com/KalyanSai956

PROFILE SUMMARY

Computer Science graduate with a strong foundation in software engineering,
backend development and AI.

EDUCATION

Mohan Babu University
Bachelor of Technology in Computer Science and Engineering
July 2022 – May 2026
CGPA: 8.98/10

EXPERIENCE

Projxty
Web Development Intern
Aug 2025 – Oct 2025

• Implemented responsive and reusable UI components using React.js.
• Architected and integrated backend APIs using Node.js and Express.js.
• Managed MongoDB databases.

PROJECTS

SmartHire ATS | Python, FastAPI, spaCy, Sentence Transformers, Groq API
• Built an AI-powered ATS resume analysis platform.
• Implemented resume parsing and semantic matching.

CodeGuardian AI | Node.js, Redis, Docker
• Built an AI-powered repository intelligence platform.

SKILLS

Programming Languages: Java, Python, JavaScript, SQL
Web & Backend: React.js, Node.js, Express.js, FastAPI
AI & Machine Learning: NLP, spaCy, Sentence Transformers
Tools: Git, GitHub, Docker, Postman

CERTIFICATIONS

Python Essentials - Cisco - 2025
AI and Machine Learning Program - Apna College - 2026

ACHIEVEMENTS

200+ LeetCode Problems
Academic Excellence
"""


sample_job_description = """
We are looking for a Python Backend Developer.

Requirements:
- Strong Python programming skills
- FastAPI or Django experience
- REST API development
- SQL and database knowledge
- MongoDB experience
- Docker
- Git and GitHub
- Experience building scalable backend applications
- Knowledge of AI, NLP or machine learning is a plus
"""


def main():
    print("\n==============================")
    print("ADVANCED ATS ENGINE TEST")
    print("==============================\n")

    profile = parse_resume_profile(sample_resume)

    quality_result = analyze_resume_quality(profile)

    result = calculate_advanced_ats_score(
        profile=profile,
        job_description=sample_job_description,
        quality_result=quality_result,
    )

    print("ATS Score:", result.ats_score)
    print("JD Match:", result.jd_match)

    print("\nScore Breakdown:")

    breakdown = result.score_breakdown

    print("Keyword Match:", breakdown.keyword_match)
    print("Semantic Match:", breakdown.semantic_match)
    print("Skills Match:", breakdown.skills_match)
    print("Experience Match:", breakdown.experience_match)
    print("Project Match:", breakdown.project_match)
    print("Resume Quality:", breakdown.resume_quality)

    print("\nKeyword Analysis:")

    print("Total Keywords:", result.keyword_analysis.total_keywords)
    print(
        "Matched Keywords:",
        len(result.keyword_analysis.matched_keywords),
    )
    print(
        "Missing Keywords:",
        len(result.keyword_analysis.missing_keywords),
    )

    print("\nMatched Skills:")

    for skill in result.matched_skills:
        print("-", skill)

    print("\nMissing Skills:")

    for skill in result.missing_skills:
        print("-", skill)

    print("\nMatched Experience Terms:")

    for term in result.matched_experience_terms:
        print("-", term)

    print("\nMatched Project Terms:")

    for term in result.matched_project_terms:
        print("-", term)

    print("\nExplanation:")

    for item in result.explanation:
        print("-", item)

    print("\n==============================")
    print("TEST PASSED")
    print("==============================")


if __name__ == "__main__":
    main()
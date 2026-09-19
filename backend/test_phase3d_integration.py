from backend.services.resume_parser import parse_resume_profile
from backend.services.resume_quality_engine import analyze_resume_quality
from backend.services.advanced_ats_engine import (
    calculate_advanced_ats_score,
)

from sentence_transformers import SentenceTransformer


SAMPLE_RESUME = """
Pasupuleti Sai Kalyan
+91 9876543210
saikalyan@example.com
linkedin.com/in/saikalyanpasupuleti
github.com/saikalyanpasupuleti

SUMMARY
Computer Science graduate with experience building AI-powered web
applications and backend systems using Python, FastAPI, React, Node.js,
MongoDB and machine learning technologies.

EDUCATION
Mohan Babu University
Bachelor of Technology
Computer Science and Engineering
July 2022 - May 2026
8.98/10

EXPERIENCE
Projxty
Web Development Intern
August 2025 - October 2025

- Built web applications using React, Node.js, Express.js and MongoDB.
- Developed backend APIs and integrated frontend services.
- Worked with Git and GitHub for version control.

PROJECTS
SmartHire ATS
Python, FastAPI, spaCy, Sentence Transformers, Groq

AI-powered resume screening platform using Python and FastAPI.
Built resume analysis and semantic matching functionality.

CodeGuardian AI
Node.js, Redis, Docker, GitHub

AI-powered GitHub code review and auto-fix platform.
Built automated code analysis and repair workflows.

SKILLS
Java, Python, JavaScript, SQL, React.js, Node.js, Express.js,
FastAPI, NLP, spaCy, Sentence Transformers, Git, GitHub,
Docker, Postman

CERTIFICATIONS
Python Essentials - Cisco - 2025
AI and ML Program - 2026

ACHIEVEMENTS
200+ LeetCode Problems
Academic Excellence
"""


SAMPLE_JD = """
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


print("=" * 70)
print("PHASE 3D INTEGRATION TEST")
print("=" * 70)


# ------------------------------------------------------------
# 1. Structured resume
# ------------------------------------------------------------

profile = parse_resume_profile(
    SAMPLE_RESUME
)

print("\n[1] Resume Profile")
print("Name:", profile.contact.name)
print("Skills:", profile.skills)
print("Education:", len(profile.education))
print("Experience:", len(profile.experience))
print("Projects:", len(profile.projects))


# ------------------------------------------------------------
# 2. Resume quality
# ------------------------------------------------------------

quality = analyze_resume_quality(
    profile
)

print("\n[2] Resume Quality")
print("Overall:", quality.overall_score)
print("Experience:", quality.experience_score)
print("Projects:", quality.projects_score)
print("Content:", quality.content_score)


# ------------------------------------------------------------
# 3. Embedding model
# ------------------------------------------------------------

print("\n[3] Loading embedding model...")

embedder = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


# ------------------------------------------------------------
# 4. Advanced ATS
# ------------------------------------------------------------

advanced = calculate_advanced_ats_score(
    resume_profile=profile,
    job_description=SAMPLE_JD,
    embedder=embedder,
    resume_quality_score=quality.overall_score,
)


print("\n[4] Advanced ATS")

print("ATS Score:", advanced.ats_score)
print("JD Match:", advanced.jd_match)

print("\nScore Breakdown:")

print(
    "Keyword:",
    advanced.score_breakdown.keyword_match,
)

print(
    "Semantic:",
    advanced.score_breakdown.semantic_match,
)

print(
    "Skills:",
    advanced.score_breakdown.skills_match,
)

print(
    "Experience:",
    advanced.score_breakdown.experience_match,
)

print(
    "Projects:",
    advanced.score_breakdown.project_match,
)

print(
    "Resume Quality:",
    advanced.score_breakdown.resume_quality,
)


print("\nMatched Skills:")

for skill in advanced.matched_skills:
    print("-", skill)


print("\nMissing Skills:")

for skill in advanced.missing_skills:
    print("-", skill)


print("\nMatched Experience Terms:")

for term in advanced.matched_experience_terms:
    print("-", term)


print("\nMatched Project Terms:")

for term in advanced.matched_project_terms:
    print("-", term)


print("\nKeyword Analysis")

print(
    "Total:",
    advanced.keyword_analysis.total_keywords,
)

print(
    "Matched:",
    len(
        advanced.keyword_analysis.matched_keywords
    ),
)

print(
    "Missing:",
    len(
        advanced.keyword_analysis.missing_keywords
    ),
)


print("\nExplanation:")

for item in advanced.explanation:
    print("-", item)


# ------------------------------------------------------------
# Assertions
# ------------------------------------------------------------

assert profile.contact.name == "Pasupuleti Sai Kalyan"

assert len(profile.skills) > 0

assert quality.overall_score >= 0
assert quality.overall_score <= 100

assert advanced.ats_score >= 0
assert advanced.ats_score <= 100

assert advanced.jd_match >= 0
assert advanced.jd_match <= 100

assert advanced.score_breakdown.keyword_match >= 0
assert advanced.score_breakdown.semantic_match >= 0
assert advanced.score_breakdown.skills_match >= 0

assert advanced.keyword_analysis.total_keywords >= 0

print("\n" + "=" * 70)
print("PHASE 3D INTEGRATION TEST PASSED")
print("=" * 70)
from backend.services.resume_parser import parse_resume_profile
from backend.services.resume_quality_engine import analyze_resume_quality


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


def main():
    print("\n==============================")
    print("RESUME QUALITY ENGINE TEST")
    print("==============================\n")

    profile = parse_resume_profile(sample_resume)

    result = analyze_resume_quality(profile)

    print("Overall Score:", result.overall_score)

    print("\nCategory Scores:")
    print("Contact:", result.contact_score)
    print("Structure:", result.structure_score)
    print("Experience:", result.experience_score)
    print("Projects:", result.projects_score)
    print("Skills:", result.skills_score)
    print("Content:", result.content_score)

    print("\nResume Statistics:")
    print("Total bullets:", result.bullet_count)
    print("Quantified bullets:", result.quantified_bullet_count)
    print("Metrics detected:", result.metrics_count)

    print("\nStrengths:")
    for item in result.strengths:
        print("-", item)

    print("\nWeaknesses:")
    for item in result.weaknesses:
        print("-", item)

    print("\nRecommendations:")
    for item in result.recommendations:
        print("-", item)

    print("\nFindings:")
    for finding in result.findings:
        print(
            f"- [{finding.severity.upper()}] "
            f"{finding.category}: {finding.message}"
        )

    print("\n==============================")
    print("TEST PASSED")
    print("==============================")


if __name__ == "__main__":
    main()
from backend.services.resume_parser import parse_resume_profile


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
    profile = parse_resume_profile(sample_resume)

    print("\n==============================")
    print("STRUCTURED RESUME TEST")
    print("==============================\n")

    print("Name:", profile.contact.name)
    print("Email:", profile.contact.email)
    print("Phone:", profile.contact.phone)
    print("LinkedIn:", profile.contact.linkedin)
    print("GitHub:", profile.contact.github)

    print("\nSummary:")
    print(profile.summary)

    print("\nEducation:")
    for item in profile.education:
        print("-", item.model_dump())

    print("\nExperience:")
    for item in profile.experience:
        print("-", item.model_dump())

    print("\nProjects:")
    for item in profile.projects:
        print("-", item.model_dump())

    print("\nSkills:")
    print(profile.skills)

    print("\nCertifications:")
    for item in profile.certifications:
        print("-", item.model_dump())

    print("\nAchievements:")
    for item in profile.achievements:
        print("-", item.model_dump())

    print("\n==============================")
    print("TEST PASSED")
    print("==============================")


if __name__ == "__main__":
    main()
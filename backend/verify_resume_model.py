from backend.models.schemas import (
    ResumeProfile,
    ResumeContact,
    ResumeEducation,
    ResumeExperience,
    ResumeProject,
    ResumeCertification,
    ResumeAchievement,
)


def main():
    profile = ResumeProfile(
        contact=ResumeContact(
            name="Sai Kalyan",
            email="test@example.com",
            phone="9999999999",
            linkedin="https://linkedin.com/in/example",
            github="https://github.com/example",
        ),
        summary="Computer Science graduate interested in software engineering and AI.",
        education=[
            ResumeEducation(
                institution="Mohan Babu University",
                degree="Bachelor of Technology",
                field_of_study="Computer Science and Engineering",
                start_date="July 2022",
                end_date="May 2026",
                grade="8.98/10",
            )
        ],
        experience=[
            ResumeExperience(
                company="Projxty",
                role="Web Development Intern",
                start_date="Aug 2025",
                end_date="Oct 2025",
                bullets=[
                    "Developed responsive web interfaces using React.js.",
                    "Built REST APIs using Node.js and Express.js.",
                ],
            )
        ],
        projects=[
            ResumeProject(
                name="SmartHire ATS",
                technologies=[
                    "Python",
                    "FastAPI",
                    "spaCy",
                    "Sentence Transformers",
                ],
                description="AI-powered resume analysis platform.",
            )
        ],
        skills=[
            "Python",
            "JavaScript",
            "React.js",
            "FastAPI",
            "Node.js",
            "MongoDB",
        ],
        certifications=[
            ResumeCertification(
                name="Python Essentials",
                issuer="Cisco",
                date="2025",
            )
        ],
        achievements=[
            ResumeAchievement(
                title="200+ LeetCode Problems",
                description="Solved more than 200 DSA problems.",
            )
        ],
    )

    print("ResumeProfile created successfully.")
    print()
    print(profile.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
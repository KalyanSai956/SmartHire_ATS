import logging
from typing import Any, Dict, List

from pydantic import BaseModel, Field, ValidationError

from backend.services.llm import LLMGateway


logger = logging.getLogger("smarthire.interview_question_generator")


# ============================================================
# PYDANTIC MODELS
# ============================================================

class GeneratedInterviewQuestion(BaseModel):
    question: str = Field(
        ...,
        min_length=10,
        max_length=2000,
    )

    category: str = Field(
        ...,
        min_length=3,
        max_length=50,
    )

    difficulty: str = Field(
        ...,
        min_length=3,
        max_length=20,
    )

    skill: str = Field(
        default="",
        max_length=200,
    )

    expected_topics: List[str] = Field(
        default_factory=list,
    )


class GeneratedQuestionSet(BaseModel):
    questions: List[GeneratedInterviewQuestion] = Field(
        ...,
        min_length=1,
    )


# ============================================================
# CONSTANTS
# ============================================================

VALID_CATEGORIES = {
    "technical",
    "behavioral",
    "project",
    "problem_solving",
    "system_design",
    "coding",
}

VALID_DIFFICULTIES = {
    "easy",
    "medium",
    "hard",
}


# ============================================================
# HELPERS
# ============================================================

def _safe_text(value: Any, maximum: int = 6000) -> str:
    """
    Convert arbitrary input into safe bounded prompt text.
    """
    if value is None:
        return ""

    text = str(value).strip()

    if len(text) > maximum:
        return text[:maximum] + "\n[truncated]"

    return text


def _dedupe(values: List[str]) -> List[str]:
    """
    Preserve order while removing duplicate strings.
    """
    result = []
    seen = set()

    for value in values or []:
        cleaned = str(value).strip()

        if not cleaned:
            continue

        key = cleaned.lower()

        if key in seen:
            continue

        seen.add(key)
        result.append(cleaned)

    return result


def _normalize_category(value: str) -> str:
    """
    Normalize LLM category output.
    """
    value = str(value or "").strip().lower()

    aliases = {
        "behavior": "behavioral",
        "behavioral interview": "behavioral",
        "technical interview": "technical",
        "project based": "project",
        "project-based": "project",
        "problem solving": "problem_solving",
        "problem-solving": "problem_solving",
        "system design interview": "system_design",
        "coding interview": "coding",
    }

    value = aliases.get(value, value)

    if value not in VALID_CATEGORIES:
        return "technical"

    return value


def _normalize_difficulty(value: str, fallback: str) -> str:
    """
    Normalize LLM difficulty output.
    """
    value = str(value or "").strip().lower()

    if value not in VALID_DIFFICULTIES:
        return fallback

    return value


def _resume_context(profile: Dict[str, Any]) -> str:
    """
    Extract useful resume/profile information without sending
    unnecessary personal contact information to the LLM.
    """
    parts = []

    skills = profile.get("skills") or []

    if skills:
        parts.append(
            "Profile skills: "
            + ", ".join(str(skill) for skill in skills[:30])
        )

    target_roles = profile.get("target_roles") or []

    if target_roles:
        parts.append(
            "Target roles: "
            + ", ".join(str(role) for role in target_roles[:10])
        )

    experience = profile.get("experience")

    if experience:
        parts.append(
            "Experience level/context: "
            + _safe_text(experience, 1000)
        )

    resume_text = profile.get("resume_text")

    if resume_text:
        parts.append(
            "Resume content:\n"
            + _safe_text(resume_text, 8000)
        )

    return "\n\n".join(parts)


# ============================================================
# PROMPT
# ============================================================

def _build_generation_prompt(
    *,
    role: str,
    job_description: str,
    interview_type: str,
    difficulty: str,
    question_count: int,
    focus_areas: List[str],
    include_coding: bool,
    include_system_design: bool,
    profile: Dict[str, Any],
) -> str:
    """
    Build the complete interviewer-generation prompt.
    """

    profile_context = _resume_context(profile)

    focus_text = (
        ", ".join(focus_areas)
        if focus_areas
        else "No specific focus areas were provided."
    )

    coding_text = (
        "Coding questions ARE allowed."
        if include_coding
        else "Do NOT generate coding questions."
    )

    system_design_text = (
        "System design questions ARE allowed."
        if include_system_design
        else "Do NOT generate system design questions."
    )

    if interview_type == "technical":
        category_guidance = """
Focus primarily on:
- technical knowledge
- practical engineering decisions
- problem solving
- project experience
"""
    elif interview_type == "behavioral":
        category_guidance = """
Focus primarily on:
- behavioral questions
- communication
- ownership
- teamwork
- decision making
- project experiences
"""
    else:
        category_guidance = """
Create a balanced mixed interview containing:
- technical questions
- behavioral questions
- project questions
- problem-solving questions
"""

    return f"""
You are the question-generation engine for SmartHire, an AI
career interview platform.

Your task is to generate a personalized interview question set.

INTERVIEW TARGET
Role: {role}
Interview type: {interview_type}
Difficulty: {difficulty}
Question count: {question_count}

FOCUS AREAS
{focus_text}

QUESTION RULES
{category_guidance}

{coding_text}
{system_design_text}

PERSONALIZATION RULES
1. Questions must be relevant to the target role.
2. Use the candidate's actual skills and resume context.
3. Prefer questions that test real understanding rather than
   memorized definitions.
4. Project questions should reference technologies or projects
   actually present in the supplied profile/resume.
5. Do not invent projects, companies, employment history, skills,
   certifications, or achievements.
6. If the candidate is a fresher, emphasize projects, fundamentals,
   problem solving, and practical understanding rather than assuming
   professional experience.
7. Avoid duplicate or nearly identical questions.
8. Questions should progressively test understanding where possible.
9. Do not ask for private information.
10. Do not include answers.

CATEGORY VALUES
Use ONLY one of:
technical
behavioral
project
problem_solving
system_design
coding

DIFFICULTY VALUES
Use ONLY one of:
easy
medium
hard

OUTPUT REQUIREMENT

Return ONLY valid JSON.

The JSON must have exactly this top-level structure:

{{
  "questions": [
    {{
      "question": "string",
      "category": "technical",
      "difficulty": "medium",
      "skill": "Python",
      "expected_topics": [
        "topic 1",
        "topic 2"
      ]
    }}
  ]
}}

The questions array must contain exactly {question_count} items.

CANDIDATE CONTEXT
{profile_context}

JOB DESCRIPTION
{_safe_text(job_description, 10000)}
""".strip()


# ============================================================
# VALIDATION
# ============================================================

def _validate_question_set(
    raw: Dict[str, Any],
    *,
    requested_count: int,
    fallback_difficulty: str,
) -> GeneratedQuestionSet:
    """
    Validate and normalize LLM-generated questions.
    """

    try:
        parsed = GeneratedQuestionSet.model_validate(raw)
    except ValidationError as exc:
        logger.error(
            "Generated interview questions failed validation: %s",
            exc,
        )
        raise ValueError(
            "LLM generated an invalid interview question set."
        ) from exc

    if len(parsed.questions) != requested_count:
        raise ValueError(
            (
                "LLM returned "
                f"{len(parsed.questions)} questions, "
                f"but {requested_count} were requested."
            )
        )

    normalized = []

    seen_questions = set()

    for item in parsed.questions:
        question_text = item.question.strip()
        question_key = question_text.lower()

        if question_key in seen_questions:
            raise ValueError(
                "LLM generated duplicate interview questions."
            )

        seen_questions.add(question_key)

        category = _normalize_category(item.category)

        difficulty = _normalize_difficulty(
            item.difficulty,
            fallback_difficulty,
        )

        expected_topics = _dedupe(
            item.expected_topics[:10]
        )

        normalized.append(
            GeneratedInterviewQuestion(
                question=question_text,
                category=category,
                difficulty=difficulty,
                skill=item.skill.strip(),
                expected_topics=expected_topics,
            )
        )

    return GeneratedQuestionSet(
        questions=normalized,
    )


# ============================================================
# GENERATOR
# ============================================================

async def generate_interview_questions(
    *,
    role: str,
    job_description: str,
    interview_type: str,
    difficulty: str,
    question_count: int,
    focus_areas: List[str],
    include_coding: bool,
    include_system_design: bool,
    profile: Dict[str, Any],
) -> GeneratedQuestionSet:
    """
    Generate a complete personalized interview question set.

    The LLM is responsible for generation.
    Pydantic is responsible for validation.
    """

    prompt = _build_generation_prompt(
        role=role,
        job_description=job_description,
        interview_type=interview_type,
        difficulty=difficulty,
        question_count=question_count,
        focus_areas=focus_areas,
        include_coding=include_coding,
        include_system_design=include_system_design,
        profile=profile,
    )

    gateway = LLMGateway(provider="groq")

    if not gateway.is_configured():
        raise RuntimeError(
            "Groq LLM provider is not configured."
        )

    messages = [
        {
            "role": "system",
            "content": (
                "You are a reliable interview question "
                "generation engine. Return valid JSON only."
            ),
        },
        {
            "role": "user",
            "content": prompt,
        },
    ]

    try:
        raw_response = await gateway.generate_json(
            messages,
            temperature=0.3,
            max_tokens=5000,
        )
    except Exception as exc:
        logger.exception(
            "Interview question generation failed."
        )
        raise RuntimeError(
            "Could not generate interview questions."
        ) from exc

    if not isinstance(raw_response, dict):
        raise ValueError(
            "LLM returned an unexpected JSON structure."
        )

    return _validate_question_set(
        raw_response,
        requested_count=question_count,
        fallback_difficulty=difficulty,
    )
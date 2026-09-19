import re
from typing import List, Tuple

from backend.models.schemas import (
    ResumeProfile,
    ResumeQualityFinding,
    ResumeQualityResult,
)


# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------

ACTION_VERBS = {
    "built",
    "developed",
    "implemented",
    "designed",
    "created",
    "engineered",
    "architected",
    "integrated",
    "optimized",
    "improved",
    "automated",
    "deployed",
    "configured",
    "managed",
    "maintained",
    "analyzed",
    "developed",
    "led",
    "delivered",
    "created",
    "tested",
    "debugged",
    "refactored",
    "migrated",
    "launched",
    "established",
    "streamlined",
    "reduced",
    "increased",
    "enhanced",
}


WEAK_STARTERS = {
    "worked on",
    "helped with",
    "responsible for",
    "was responsible for",
    "participated in",
    "involved in",
    "did",
    "made",
    "used",
}


# Numbers, percentages, currency, measurements, etc.
METRIC_PATTERN = re.compile(
    r"""
    (
        \b\d+(?:\.\d+)?\s*%
        |
        \b\d+(?:\.\d+)?\s*(?:k|m|b)\b
        |
        \$\s*\d+(?:\.\d+)?
        |
        ₹\s*\d+(?:\.\d+)?
        |
        \b\d+(?:\.\d+)?\s*
        (?:users?|requests?|records?|files?|projects?|problems?|
        tests?|apis?|endpoints?|models?|datasets?|
        seconds?|minutes?|hours?|days?|months?|years?)\b
        |
        \b\d+(?:\.\d+)?\b
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)


def _clamp_score(value: float) -> int:
    return max(0, min(100, round(value)))


def _add_finding(
    findings: List[ResumeQualityFinding],
    category: str,
    severity: str,
    message: str,
) -> None:
    findings.append(
        ResumeQualityFinding(
            category=category,
            severity=severity,
            message=message,
        )
    )


# -------------------------------------------------------------------
# Contact analysis
# -------------------------------------------------------------------

def _score_contact(
    profile: ResumeProfile,
    findings: List[ResumeQualityFinding],
) -> Tuple[int, List[str], List[str], List[str]]:
    strengths = []
    weaknesses = []
    recommendations = []

    contact = profile.contact

    fields = {
        "Name": contact.name,
        "Email": contact.email,
        "Phone": contact.phone,
        "LinkedIn": contact.linkedin,
        "GitHub": contact.github,
        "Portfolio": contact.portfolio,
    }

    present = [
        name
        for name, value in fields.items()
        if value and str(value).strip()
    ]

    missing = [
        name
        for name, value in fields.items()
        if not value or not str(value).strip()
    ]

    score = (len(present) / len(fields)) * 100

    if len(present) >= 5:
        strengths.append("Contact information is well populated.")
    elif len(present) >= 4:
        strengths.append("Most important contact information is present.")
    else:
        weaknesses.append("Some important contact information is missing.")

    for field in missing:
        if field == "Portfolio":
            recommendations.append(
                "Consider adding a portfolio URL if you have one."
            )
        elif field in {"LinkedIn", "GitHub"}:
            recommendations.append(
                f"Add your {field} profile to improve professional discoverability."
            )
        else:
            _add_finding(
                findings,
                "contact",
                "warning",
                f"{field} is missing from the resume.",
            )

    return _clamp_score(score), strengths, weaknesses, recommendations


# -------------------------------------------------------------------
# Structure analysis
# -------------------------------------------------------------------

def _score_structure(
    profile: ResumeProfile,
    findings: List[ResumeQualityFinding],
) -> Tuple[int, List[str], List[str], List[str]]:
    strengths = []
    weaknesses = []
    recommendations = []

    sections = {
        "Summary": bool(profile.summary and profile.summary.strip()),
        "Education": bool(profile.education),
        "Experience": bool(profile.experience),
        "Projects": bool(profile.projects),
        "Skills": bool(profile.skills),
        "Certifications": bool(profile.certifications),
        "Achievements": bool(profile.achievements),
    }

    present_count = sum(sections.values())
    score = (present_count / len(sections)) * 100

    core_sections = [
        "Summary",
        "Education",
        "Skills",
    ]

    for section in core_sections:
        if not sections[section]:
            weaknesses.append(f"{section} section is missing.")
            recommendations.append(
                f"Add a clear {section.lower()} section."
            )
            _add_finding(
                findings,
                "structure",
                "warning",
                f"{section} section is missing.",
            )

    if sections["Experience"] or sections["Projects"]:
        strengths.append(
            "The resume contains practical experience or project evidence."
        )

    if sections["Skills"]:
        strengths.append("A dedicated skills section is present.")

    if present_count >= 5:
        strengths.append("Resume structure is reasonably complete.")

    return _clamp_score(score), strengths, weaknesses, recommendations


# -------------------------------------------------------------------
# Bullet analysis
# -------------------------------------------------------------------

def _analyze_bullet(
    bullet: str,
) -> Tuple[bool, bool, bool]:
    """
    Returns:
        has_metric
        starts_with_action_verb
        starts_with_weak_phrase
    """

    cleaned = bullet.strip()

    if not cleaned:
        return False, False, False

    has_metric = bool(METRIC_PATTERN.search(cleaned))

    words = cleaned.lower().split()

    first_words = " ".join(words[:4])

    starts_with_action = False

    if words:
        first_word = re.sub(r"[^a-z]", "", words[0])
        if first_word in ACTION_VERBS:
            starts_with_action = True

    starts_with_weak = any(
        first_words.startswith(weak)
        for weak in WEAK_STARTERS
    )

    return has_metric, starts_with_action, starts_with_weak


def _collect_bullets(profile: ResumeProfile) -> List[str]:
    bullets = []

    for experience in profile.experience:
        bullets.extend(experience.bullets)

    for project in profile.projects:
        bullets.extend(project.bullets)

    return [
        bullet.strip()
        for bullet in bullets
        if bullet and bullet.strip()
    ]


# -------------------------------------------------------------------
# Experience analysis
# -------------------------------------------------------------------

def _score_experience(
    profile: ResumeProfile,
    findings: List[ResumeQualityFinding],
) -> Tuple[int, List[str], List[str], List[str], int, int, int]:
    strengths = []
    weaknesses = []
    recommendations = []

    experiences = profile.experience

    if not experiences:
        _add_finding(
            findings,
            "experience",
            "warning",
            "No professional experience was detected.",
        )

        return (
            50,
            strengths,
            ["No professional experience was detected."],
            ["Add relevant internship, work, freelance, or practical experience if available."],
            0,
            0,
            0,
        )

    total_bullets = sum(
        len(experience.bullets)
        for experience in experiences
    )

    bullets_with_metrics = 0
    action_bullets = 0
    weak_bullets = 0

    for experience in experiences:
        if not experience.bullets:
            weaknesses.append(
                f"{experience.role or 'Experience'} has no bullet points."
            )

            recommendations.append(
                "Add concise accomplishment-focused bullets to each experience entry."
            )

            _add_finding(
                findings,
                "experience",
                "warning",
                f"{experience.role or 'Experience'} has no bullet points.",
            )

        for bullet in experience.bullets:
            has_metric, has_action, has_weak = _analyze_bullet(bullet)

            if has_metric:
                bullets_with_metrics += 1

            if has_action:
                action_bullets += 1

            if has_weak:
                weak_bullets += 1

    if total_bullets >= 3:
        strengths.append(
            "Professional experience contains multiple descriptive bullets."
        )

    if bullets_with_metrics > 0:
        strengths.append(
            "Experience includes measurable results."
        )
    else:
        weaknesses.append(
            "Experience bullets do not contain obvious measurable results."
        )

        recommendations.append(
            "Add metrics such as percentages, scale, users, performance improvements, or time saved where truthful."
        )

        _add_finding(
            findings,
            "experience",
            "suggestion",
            "Experience bullets lack obvious measurable results.",
        )

    if action_bullets > 0:
        strengths.append(
            "Experience uses action-oriented language."
        )

    if weak_bullets > 0:
        weaknesses.append(
            "Some experience bullets begin with weak or passive phrasing."
        )

        recommendations.append(
            "Rewrite weak bullet openings with stronger action verbs."
        )

        _add_finding(
            findings,
            "experience",
            "suggestion",
            "Some experience bullets use weak opening phrases.",
        )

    bullet_score = 0

    if total_bullets > 0:
        bullet_score += min(40, total_bullets * 10)

        metric_ratio = bullets_with_metrics / total_bullets
        action_ratio = action_bullets / total_bullets

        bullet_score += metric_ratio * 35
        bullet_score += action_ratio * 25

    return (
        _clamp_score(bullet_score),
        strengths,
        weaknesses,
        recommendations,
        total_bullets,
        bullets_with_metrics,
        action_bullets,
    )


# -------------------------------------------------------------------
# Project analysis
# -------------------------------------------------------------------

def _score_projects(
    profile: ResumeProfile,
    findings: List[ResumeQualityFinding],
) -> Tuple[int, List[str], List[str], List[str]]:
    strengths = []
    weaknesses = []
    recommendations = []

    projects = profile.projects

    if not projects:
        weaknesses.append("No projects were detected.")
        recommendations.append(
            "Add relevant technical projects that demonstrate practical skills."
        )

        _add_finding(
            findings,
            "projects",
            "warning",
            "No projects were detected.",
        )

        return 40, strengths, weaknesses, recommendations

    project_scores = []

    for project in projects:
        score = 0

        if project.name:
            score += 20

        if project.technologies:
            score += 25

        if project.description:
            score += 20

        if project.bullets:
            score += 25

        if project.url:
            score += 10

        project_scores.append(score)

    score = sum(project_scores) / len(project_scores)

    if len(projects) >= 2:
        strengths.append(
            "Multiple technical projects are present."
        )

    if any(project.technologies for project in projects):
        strengths.append(
            "Projects include technology information."
        )

    projects_without_bullets = [
        project.name or "Unnamed project"
        for project in projects
        if not project.bullets
    ]

    if projects_without_bullets:
        weaknesses.append(
            "Some projects do not contain detailed bullet points."
        )

        recommendations.append(
            "Add 2–4 accomplishment-focused bullets to major projects."
        )

        _add_finding(
            findings,
            "projects",
            "suggestion",
            "Some projects lack detailed bullet points.",
        )

    return (
        _clamp_score(score),
        strengths,
        weaknesses,
        recommendations,
    )


# -------------------------------------------------------------------
# Skills analysis
# -------------------------------------------------------------------

def _score_skills(
    profile: ResumeProfile,
    findings: List[ResumeQualityFinding],
) -> Tuple[int, List[str], List[str], List[str]]:
    strengths = []
    weaknesses = []
    recommendations = []

    skills = profile.skills

    if not skills:
        _add_finding(
            findings,
            "skills",
            "warning",
            "No skills were detected.",
        )

        return (
            30,
            strengths,
            ["No skills were detected."],
            ["Add a focused technical skills section."],
        )

    unique_skills = {
        skill.strip().lower()
        for skill in skills
        if skill.strip()
    }

    score = 100

    if len(unique_skills) >= 8:
        strengths.append(
            "Resume contains a broad technical skills set."
        )
    elif len(unique_skills) >= 5:
        strengths.append(
            "Resume contains a reasonable number of technical skills."
        )
    else:
        weaknesses.append(
            "The skills section contains relatively few skills."
        )

        recommendations.append(
            "Include relevant technical skills that are actually demonstrated elsewhere in the resume."
        )

    if len(unique_skills) != len(skills):
        score -= 10

        _add_finding(
            findings,
            "skills",
            "suggestion",
            "Duplicate skills were detected.",
        )

    return (
        _clamp_score(score),
        strengths,
        weaknesses,
        recommendations,
    )


# -------------------------------------------------------------------
# Overall content analysis
# -------------------------------------------------------------------

def _score_content(
    profile: ResumeProfile,
    findings: List[ResumeQualityFinding],
    bullet_count: int,
    quantified_bullet_count: int,
) -> Tuple[int, List[str], List[str], List[str]]:
    strengths = []
    weaknesses = []
    recommendations = []

    score = 0

    # Summary
    if profile.summary:
        summary_length = len(profile.summary.split())

        if 20 <= summary_length <= 120:
            score += 20
            strengths.append(
                "Professional summary has a reasonable length."
            )
        elif summary_length < 20:
            score += 10
            weaknesses.append(
                "Professional summary is very short."
            )
            recommendations.append(
                "Expand the summary to clearly communicate your role, strengths, and target direction."
            )
        else:
            score += 15
            weaknesses.append(
                "Professional summary may be longer than necessary."
            )
            recommendations.append(
                "Keep the summary concise and focused on relevant value."
            )
    else:
        weaknesses.append("Professional summary is missing.")
        recommendations.append(
            "Add a concise professional summary."
        )

    # Bullet depth
    if bullet_count >= 6:
        score += 25
    elif bullet_count >= 3:
        score += 18
    elif bullet_count > 0:
        score += 10
        weaknesses.append(
            "Resume contains relatively few accomplishment bullets."
        )
        recommendations.append(
            "Expand important experience and project entries with specific contributions."
        )
    else:
        _add_finding(
            findings,
            "content",
            "warning",
            "No experience or project bullets were detected.",
        )

    # Metrics
    if quantified_bullet_count > 0:
        score += 25
        strengths.append(
            "Resume contains quantified information."
        )
    else:
        weaknesses.append(
            "Resume has limited quantified evidence of impact."
        )
        recommendations.append(
            "Where truthful, quantify outcomes using measurable results."
        )

    # Technical evidence
    if profile.skills and (
        profile.experience or profile.projects
    ):
        score += 30
        strengths.append(
            "Technical skills are supported by practical experience or projects."
        )

    return (
        _clamp_score(score),
        strengths,
        weaknesses,
        recommendations,
    )


# -------------------------------------------------------------------
# Main engine
# -------------------------------------------------------------------

def analyze_resume_quality(
    profile: ResumeProfile,
) -> ResumeQualityResult:
    findings: List[ResumeQualityFinding] = []

    strengths: List[str] = []
    weaknesses: List[str] = []
    recommendations: List[str] = []

    contact_score, s, w, r = _score_contact(
        profile,
        findings,
    )

    strengths.extend(s)
    weaknesses.extend(w)
    recommendations.extend(r)

    structure_score, s, w, r = _score_structure(
        profile,
        findings,
    )

    strengths.extend(s)
    weaknesses.extend(w)
    recommendations.extend(r)

    (
        experience_score,
        s,
        w,
        r,
        bullet_count,
        quantified_bullet_count,
        action_bullet_count,
    ) = _score_experience(
        profile,
        findings,
    )

    strengths.extend(s)
    weaknesses.extend(w)
    recommendations.extend(r)

    projects_score, s, w, r = _score_projects(
        profile,
        findings,
    )

    strengths.extend(s)
    weaknesses.extend(w)
    recommendations.extend(r)

    skills_score, s, w, r = _score_skills(
        profile,
        findings,
    )

    strengths.extend(s)
    weaknesses.extend(w)
    recommendations.extend(r)

    content_score, s, w, r = _score_content(
        profile,
        findings,
        bullet_count,
        quantified_bullet_count,
    )

    strengths.extend(s)
    weaknesses.extend(w)
    recommendations.extend(r)

    # Weighted overall score.
    #
    # Content and practical evidence receive higher weight because
    # resume quality should not be determined only by section presence.
    overall_score = (
        contact_score * 0.10
        + structure_score * 0.15
        + experience_score * 0.25
        + projects_score * 0.15
        + skills_score * 0.15
        + content_score * 0.20
    )

    # Remove duplicates while preserving order.
    strengths = list(dict.fromkeys(strengths))
    weaknesses = list(dict.fromkeys(weaknesses))
    recommendations = list(dict.fromkeys(recommendations))

    # If the resume has strong evidence, surface it explicitly.
    if quantified_bullet_count > 0:
        strengths.append(
            f"{quantified_bullet_count} bullet(s) contain measurable information."
        )

    if action_bullet_count > 0:
        strengths.append(
            f"{action_bullet_count} bullet(s) use action-oriented language."
        )

    strengths = list(dict.fromkeys(strengths))

    return ResumeQualityResult(
        overall_score=_clamp_score(overall_score),

        contact_score=contact_score,
        structure_score=structure_score,
        experience_score=experience_score,
        projects_score=projects_score,
        skills_score=skills_score,
        content_score=content_score,

        strengths=strengths,
        weaknesses=weaknesses,
        recommendations=recommendations,

        findings=findings,

        metrics_count=quantified_bullet_count,
        bullet_count=bullet_count,
        quantified_bullet_count=quantified_bullet_count,
    )
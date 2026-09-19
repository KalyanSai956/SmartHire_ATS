

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

class Priority(Enum):
    CRITICAL='critical'
    HIGH='high'
    MEDIUM='medium'
    LOW='low'

# Priority.CRITICAL

@dataclass
class Recommendation:
    title:        str
    description:  str
    priority:     Priority
    impact_score: float
    category:     str
    action_items: List[str]

#generator01
def generate_skill_recommendations(skill_validation_results: Dict) -> List[Recommendation]:
    recommendations   = []
    unvalidated       = skill_validation_results.get('unvalidated_skills', [])
    validation_pct    = skill_validation_results.get('validation_percentage', 0.0)

    if not unvalidated:
        return recommendations

    if validation_pct < 0.4:
        priority, impact = Priority.CRITICAL, 8.0
    elif validation_pct < 0.6:
        priority, impact = Priority.HIGH, 6.0
    elif validation_pct < 0.8:
        priority, impact = Priority.MEDIUM, 4.0
    else:
        priority, impact = Priority.LOW, 2.0

    action_items = [
        f"Add a project or experience demonstrating '{skill}', or remove it from skills"
        for skill in unvalidated[:5]
    ]
    if len(unvalidated) > 5:
        action_items.append(f'... and {len(unvalidated) - 5} more unvalidated skill(s)')

    recommendations.append(Recommendation(
        title        = 'Validate Your Listed Skills',
        description  = (
            f'{len(unvalidated)} skill(s) are not demonstrated in your projects or experience. '
            'ATS systems and recruiters look for evidence that you\'ve actually used the skills you claim.'
        ),
        priority     = priority,
        impact_score = impact,
        category     = 'skill_validation',
        action_items = action_items,
    ))
    return recommendations

#generator02: grammtical suggestions
def generate_grammar_recommendations(grammar_results: Dict) -> List[Recommendation]:
    recommendations = []

    critical_errors = grammar_results.get('critical_errors', [])
    moderate_errors = grammar_results.get('moderate_errors', [])
    minor_errors    = grammar_results.get('minor_errors', [])

    total = len(critical_errors) + len(moderate_errors) + len(minor_errors)

    if total == 0:
        return recommendations

    if critical_errors:
        items = []
        for error in critical_errors[:5]:
            word    = error.get('error_text', 'unknown')
            suggest = error.get('suggestions', [])
            suffix  = f" → '{suggest[0]}'" if suggest else ''
            items.append(f"Fix '{word}'{suffix}: {error.get('message', '')}")
        if len(critical_errors) > 5:
            items.append(f'... and {len(critical_errors) - 5} more critical error(s)')

        recommendations.append(Recommendation(
            title        = 'Fix Critical Spelling/Grammar Errors',
            description  = (
                f'{len(critical_errors)} critical error(s) found. These spelling mistakes or '
                'major grammar issues will make your resume look unprofessional.'
            ),
            priority     = Priority.CRITICAL,
            impact_score = min(10.0, len(critical_errors) * 2.0),
            category     = 'grammar',
            action_items = items,
        ))

    if moderate_errors:
        items = []
        for error in moderate_errors[:3]:
            word    = error.get('error_text', 'unknown')
            suggest = error.get('suggestions', [])
            suffix  = f" → '{suggest[0]}'" if suggest else ''
            items.append(f"Fix '{word}'{suffix}: {error.get('message', '')}")
        if len(moderate_errors) > 3:
            items.append(f'... and {len(moderate_errors) - 3} more moderate error(s)')

        recommendations.append(Recommendation(
            title        = 'Address Punctuation and Capitalization Issues',
            description  = (
                f'{len(moderate_errors)} moderate error(s) found. '
                'These punctuation or capitalization issues should be corrected.'
            ),
            priority     = Priority.HIGH,
            impact_score = min(6.0, len(moderate_errors) * 1.0),
            category     = 'grammar',
            action_items = items,
        ))

    if minor_errors and len(minor_errors) >= 3:
        recommendations.append(Recommendation(
            title        = 'Consider Style Improvements',
            description  = (
                f'{len(minor_errors)} minor style suggestion(s) found. '
                'These are optional improvements for better readability.'
            ),
            priority     = Priority.LOW,
            impact_score = 1.0,
            category     = 'grammar',
            action_items = [
                f'Review {len(minor_errors)} style suggestion(s) for improved readability',
                'Use consistent formatting throughout',
            ],
        ))

    return recommendations

#generator03: location recommendations
def generate_location_recommendations(location_results: Dict) -> List[Recommendation]:
    recommendations    = []
    detected_locations = location_results.get('detected_locations', [])
    privacy_risk       = location_results.get('privacy_risk', 'none')

    if privacy_risk == 'none' or not detected_locations:
        return recommendations

    addresses = [loc for loc in detected_locations if loc.get('type') == 'address']
    zip_codes = [loc for loc in detected_locations if loc.get('type') == 'zip']

    action_items = []
    for addr in addresses[:2]:
        action_items.append(f"Remove full address: '{addr.get('text', '')}'")

    for z in zip_codes[:2]:
        action_items.append(f"Remove zip code: '{z.get('text', '')}'")
    action_items.append("Keep only 'City, State' in your contact header")

    if privacy_risk == 'high':
        priority    = Priority.CRITICAL
        impact      = 5.0
        description = (
            'Your resume contains detailed location information that poses a privacy risk. '
            'Full addresses and zip codes are unnecessary and can be used to identify your location.'
        )
    elif privacy_risk == 'medium':
        priority    = Priority.HIGH
        impact      = 3.0
        description = (
            "Your resume contains multiple location mentions. Consider simplifying to just "
            "'City, State' in your contact header."
        )
    else:
        priority    = Priority.MEDIUM
        impact      = 2.0
        description = (
            'Minor location information detected. Consider reviewing for unnecessary location details.'
        )

    recommendations.append(Recommendation(
        title        = 'Protect Your Location Privacy',
        description  = description,
        priority     = priority,
        impact_score = impact,
        category     = 'location',
        action_items = action_items,
    ))
    return recommendations

#generator04: keyword recommendations
def generate_keyword_recommendations(
    keyword_analysis: Optional[Dict] = None,
    resume_keywords: Optional[List[str]] = None,
) -> List[Recommendation]:
    recommendations = []

    if keyword_analysis:
        missing   = keyword_analysis.get('missing_keywords', [])
        gap       = keyword_analysis.get('skills_gap', [])
        match_pct = keyword_analysis.get('match_percentage', 0.0)

        if missing:
            if match_pct < 40:
                priority, impact = Priority.CRITICAL, 8.0
            elif match_pct < 60:
                priority, impact = Priority.HIGH, 6.0
            else:
                priority, impact = Priority.MEDIUM, 4.0

            items = [f"Add '{kw}' to your resume in a relevant section" for kw in missing[:7]]
            if len(missing) > 7:
                items.append(f'... and {len(missing) - 7} more missing keyword(s)')

            recommendations.append(Recommendation(
                title        = 'Add Missing Job Description Keywords',
                description  = (
                    f'{len(missing)} keyword(s) from the job description are missing from '
                    f'your resume. Your current match is {match_pct:.0f}%.'
                ),
                priority     = priority,
                impact_score = impact,
                category     = 'keywords',
                action_items = items,
            ))

        if gap:
            items = [f"Consider adding '{skill}' if you have this skill" for skill in gap[:5]]
            if len(gap) > 5:
                items.append(f'... and {len(gap) - 5} more skill(s) mentioned in the job')

            recommendations.append(Recommendation(
                title        = 'Address Skills Gap',
                description  = (
                    f'The job description mentions {len(gap)} skill(s) not found in your resume. '
                    'Add these skills if you have them, or consider gaining them.'
                ),
                priority     = Priority.HIGH,
                impact_score = 5.0,
                category     = 'keywords',
                action_items = items,
            ))

    elif resume_keywords is not None:
        if len(resume_keywords) < 10:
            recommendations.append(Recommendation(
                title        = 'Increase Keyword Density',
                description  = (
                    f'Your resume contains only {len(resume_keywords)} keywords. '
                    'Adding more relevant keywords will improve ATS matching.'
                ),
                priority     = Priority.MEDIUM,
                impact_score = 4.0,
                category     = 'keywords',
                action_items = [
                    "Add more technical skills and tools you've used",
                    'Include industry-specific terminology',
                    'Mention relevant certifications and methodologies',
                ],
            ))

    return recommendations

#generator05: formatting and structure recommendations
def generate_formatting_recommendations(
    score_results: Dict,
    sections: Dict[str, str],
) -> List[Recommendation]:
    recommendations  = []
    formatting_score = score_results.get('formatting_score', 0.0)

    section_recommendations = {
        'experience': "Add a clear 'Experience' or 'Work History' section",
        'education':  "Add an 'Education' section with your qualifications",
        'skills':     "Add a 'Skills' section listing your technical and soft skills",
        'summary':    "Consider adding a 'Summary' or 'Objective' section at the top",
        'projects':   "Consider adding a 'Projects' section to showcase your work",
    }

    missing_sections = []
    for section_name, suggestion in section_recommendations.items():
        content = sections.get(section_name, '')
        if not content or len(content) < 20:
            missing_sections.append((section_name, suggestion))

    core_missing     = [(n, s) for n, s in missing_sections if n in ['experience', 'education', 'skills']]
    optional_missing = [(n, s) for n, s in missing_sections if n in ['summary', 'projects']]

    if core_missing:
        recommendations.append(Recommendation(
            title        = 'Add Missing Core Sections',
            description  = (
                f'Your resume is missing {len(core_missing)} essential section(s). '
                'ATS systems expect standard resume sections.'
            ),
            priority     = Priority.CRITICAL,
            impact_score = 7.0,
            category     = 'formatting',
            action_items = [suggestion for _, suggestion in core_missing],
        ))

    if optional_missing and formatting_score < 15:
        recommendations.append(Recommendation(
            title        = 'Consider Adding Optional Sections',
            description  = 'Adding a summary and projects section can strengthen your resume.',
            priority     = Priority.LOW,
            impact_score = 2.0,
            category     = 'formatting',
            action_items = [suggestion for _, suggestion in optional_missing],
        ))

    if formatting_score < 12:   # Below 60% of 20 pts
        recommendations.append(Recommendation(
            title        = 'Improve Resume Structure',
            description  = (
                f'Your formatting score is {formatting_score:.1f}/20. '
                'Better structure will improve ATS parsing and readability.'
            ),
            priority     = Priority.HIGH,
            impact_score = 5.0,
            category     = 'formatting',
            action_items = [
                'Use bullet points to list achievements and responsibilities',
                'Add clear section headers (Experience, Education, Skills)',
                'Ensure consistent formatting throughout',
                'Use a clean, single-column layout',
            ],
        ))

    return recommendations



def _prioritize_recommendations(recommendations: List[Recommendation]) -> List[Recommendation]:
    priority_order = {
        Priority.CRITICAL: 0,
        Priority.HIGH:     1,
        Priority.MEDIUM:   2,
        Priority.LOW:      3,
    }
    return sorted(
        recommendations,
        key=lambda r: (priority_order[r.priority], -r.impact_score)
    )

# ============================================================
# Phase 3F — AI / Career Recommendations
# ============================================================
# These recommendations are evidence-aware. They consume the
# structured outputs from Phase 3C, 3D and 3E instead of asking
# an LLM to invent missing skills or resume problems.


def _phase3_get(obj, name, default=None):
    """Read a Pydantic model or dictionary safely."""
    if obj is None:
        return default

    if isinstance(obj, dict):
        return obj.get(name, default)

    return getattr(obj, name, default)


def _phase3_dedupe(items):
    """Preserve order while removing duplicate text values."""
    seen = set()
    result = []

    for item in items or []:
        value = str(item).strip()
        if not value:
            continue

        key = value.lower()
        if key not in seen:
            seen.add(key)
            result.append(value)

    return result


def _phase3_has_experience(resume_profile) -> bool:
    experience = _phase3_get(
        resume_profile,
        'experience',
        [],
    ) or []

    for item in experience:
        if (
            _phase3_get(item, 'role')
            or _phase3_get(item, 'company')
            or _phase3_get(item, 'bullets', [])
        ):
            return True

    return False


def _phase3_has_projects(resume_profile) -> bool:
    projects = _phase3_get(
        resume_profile,
        'projects',
        [],
    ) or []

    for item in projects:
        if (
            _phase3_get(item, 'name')
            or _phase3_get(item, 'technologies', [])
            or _phase3_get(item, 'description')
            or _phase3_get(item, 'bullets', [])
        ):
            return True

    return False


def _phase3_score(value, default=0.0) -> float:
    try:
        return max(0.0, min(100.0, float(value)))
    except (TypeError, ValueError):
        return default


def _phase3_skill_gap_recommendations(
    advanced_ats,
    jd_intelligence,
):
    recommendations = []

    missing_skills = _phase3_dedupe(
        _phase3_get(
            advanced_ats,
            'missing_skills',
            [],
        )
    )

    required_skills = _phase3_dedupe(
        _phase3_get(
            jd_intelligence,
            'required_skills',
            [],
        )
    )

    required_set = {
        skill.lower()
        for skill in required_skills
    }

    missing_required = [
        skill
        for skill in missing_skills
        if skill.lower() in required_set
    ]

    if not missing_required:
        return recommendations

    selected = missing_required[:5]

    action_items = [
        (
            f"Gain and demonstrate '{skill}' through a relevant "
            "project, internship, coursework, or other genuine "
            "experience before claiming it on the resume."
        )
        for skill in selected
    ]

    recommendations.append(
        Recommendation(
            title='Address Required Skill Gaps',
            description=(
                f'{len(missing_required)} required skill(s) from the '
                'target job are not currently supported by the resume. '
                'Focus on the most relevant gaps first.'
            ),
            priority=Priority.HIGH,
            impact_score=7.0,
            category='skill_gap',
            action_items=action_items,
        )
    )

    return recommendations


def _phase3_keyword_recommendations(advanced_ats):
    recommendations = []

    keyword_analysis = _phase3_get(
        advanced_ats,
        'keyword_analysis',
    )

    if keyword_analysis is None:
        return recommendations

    missing = _phase3_dedupe(
        _phase3_get(
            keyword_analysis,
            'missing_keywords',
            [],
        )
    )

    if not missing:
        return recommendations

    selected = missing[:7]

    action_items = [
        (
            f"Use '{keyword}' in a relevant resume section only if "
            "it accurately describes your existing skills or work."
        )
        for keyword in selected
    ]

    recommendations.append(
        Recommendation(
            title='Improve Relevant Keyword Coverage',
            description=(
                f'{len(missing)} relevant job-description term(s) were '
                'not detected in the resume. Add them only when they are '
                'truthful and supported by your background.'
            ),
            priority=Priority.MEDIUM,
            impact_score=4.0,
            category='keywords',
            action_items=action_items,
        )
    )

    return recommendations


def _phase3_quality_recommendations(resume_quality):
    recommendations = []

    if resume_quality is None:
        return recommendations

    score = _phase3_score(
        _phase3_get(
            resume_quality,
            'overall_score',
            0,
        )
    )

    weaknesses = _phase3_dedupe(
        _phase3_get(
            resume_quality,
            'weaknesses',
            [],
        )
    )

    engine_recommendations = _phase3_dedupe(
        _phase3_get(
            resume_quality,
            'recommendations',
            [],
        )
    )

    evidence = (weaknesses + engine_recommendations)[:5]

    if score < 70:
        priority = Priority.HIGH
        impact = 7.0
    elif score < 85:
        priority = Priority.MEDIUM
        impact = 4.0
    else:
        return recommendations

    recommendations.append(
        Recommendation(
            title='Improve Resume Quality',
            description=(
                f'The structured resume quality score is {score:.0f}/100. '
                'Address the highest-impact content issues before making '
                'minor keyword changes.'
            ),
            priority=priority,
            impact_score=impact,
            category='resume_quality',
            action_items=(
                evidence
                if evidence
                else [
                    'Strengthen achievement-oriented bullets.',
                    'Add measurable results where they are available.',
                    'Keep section structure clear and consistent.',
                ]
            ),
        )
    )

    return recommendations


def _phase3_project_recommendations(
    resume_profile,
    advanced_ats,
):
    recommendations = []

    has_projects = _phase3_has_projects(
        resume_profile
    )

    matched_project_terms = _phase3_dedupe(
        _phase3_get(
            advanced_ats,
            'matched_project_terms',
            [],
        )
    )

    if not has_projects:
        recommendations.append(
            Recommendation(
                title='Add a Relevant Technical Project',
                description=(
                    'No project evidence was detected in the structured '
                    'resume profile. Projects can provide concrete evidence '
                    'for technical skills, especially for early-career roles.'
                ),
                priority=Priority.HIGH,
                impact_score=7.0,
                category='projects',
                action_items=[
                    'Add a relevant technical project.',
                    'List the technologies actually used.',
                    'Describe your implementation and measurable outcome.',
                ],
            )
        )

    elif not matched_project_terms:
        recommendations.append(
            Recommendation(
                title='Strengthen Project Alignment',
                description=(
                    'Projects were detected, but the advanced ATS analysis '
                    'did not find strong project-term matches for the target job.'
                ),
                priority=Priority.MEDIUM,
                impact_score=4.0,
                category='projects',
                action_items=[
                    'Rewrite relevant project bullets around the work you actually performed.',
                    'Explicitly mention applicable technologies you genuinely used.',
                    'Include the outcome or measurable result where available.',
                ],
            )
        )

    return recommendations


def _phase3_experience_recommendations(
    resume_profile,
    advanced_ats,
    jd_intelligence,
):
    recommendations = []

    has_experience = _phase3_has_experience(
        resume_profile
    )

    experience_requirement = _phase3_get(
        jd_intelligence,
        'experience',
    )

    required = bool(
        _phase3_get(
            experience_requirement,
            'required',
            False,
        )
    )

    minimum_years = _phase3_get(
        experience_requirement,
        'minimum_years',
    )

    score_breakdown = _phase3_get(
        advanced_ats,
        'score_breakdown',
    )

    experience_match = _phase3_get(
        score_breakdown,
        'experience_match',
    )

    if (
        required
        and minimum_years is not None
        and not has_experience
    ):
        recommendations.append(
            Recommendation(
                title='Address the Experience Requirement',
                description=(
                    f'The target job specifies at least {minimum_years:g} '
                    'years of experience, while no professional experience '
                    'was detected in the structured resume.'
                ),
                priority=Priority.HIGH,
                impact_score=8.0,
                category='experience',
                action_items=[
                    'Accurately include relevant internships if applicable.',
                    'Include relevant freelance, research, or open-source work when appropriate.',
                    'Do not claim professional experience that you do not have.',
                ],
            )
        )

    elif (
        has_experience
        and experience_match is not None
        and _phase3_score(experience_match) < 60
    ):
        recommendations.append(
            Recommendation(
                title='Strengthen Experience Alignment',
                description=(
                    'The experience component of the advanced ATS analysis '
                    'shows limited alignment with the target job description.'
                ),
                priority=Priority.MEDIUM,
                impact_score=5.0,
                category='experience',
                action_items=[
                    'Emphasize relevant responsibilities you actually performed.',
                    'Mention applicable technologies used in that work.',
                    'Add measurable outcomes where they are available.',
                ],
            )
        )

    return recommendations


def _phase3_build_strengths(
    resume_quality,
    advanced_ats,
    jd_intelligence,
):
    strengths = []

    quality_score = _phase3_score(
        _phase3_get(
            resume_quality,
            'overall_score',
            0,
        )
    )

    ats_score = _phase3_score(
        _phase3_get(
            advanced_ats,
            'ats_score',
            0,
        )
    )

    matched_skills = _phase3_dedupe(
        _phase3_get(
            advanced_ats,
            'matched_skills',
            [],
        )
    )

    role_signals = _phase3_dedupe(
        _phase3_get(
            jd_intelligence,
            'role_signals',
            [],
        )
    )

    if quality_score >= 80:
        strengths.append(
            'Resume quality is strong based on the structured quality analysis.'
        )

    if matched_skills:
        strengths.append(
            f'{len(matched_skills)} target-role skill(s) have been detected in the resume.'
        )

    if ats_score >= 70:
        strengths.append(
            'The advanced ATS analysis shows strong alignment with the supplied job description.'
        )

    if role_signals:
        strengths.append(
            'The job description contains identifiable signals for: '
            + ', '.join(role_signals[:5])
            + '.'
        )

    return _phase3_dedupe(strengths)


def generate_ai_recommendations(
    resume_profile,
    resume_quality,
    advanced_ats,
    jd_intelligence=None,
) -> Dict:
    """
    Generate Phase 3F evidence-aware recommendations.

    Returns the same dictionary shape used by the existing
    recommendation engine, so existing formatting and API code
    remain compatible.
    """

    if advanced_ats is None:
        return {
            'all_recommendations': [],
            'critical_recommendations': [],
            'high_recommendations': [],
            'medium_recommendations': [],
            'low_recommendations': [],
            'total_count': 0,
            'estimated_improvement': 0.0,
            'strengths': [],
            'top_missing_skills': [],
        }

    all_recs = []

    if jd_intelligence is not None:
        all_recs.extend(
            _phase3_skill_gap_recommendations(
                advanced_ats,
                jd_intelligence,
            )
        )

        all_recs.extend(
            _phase3_experience_recommendations(
                resume_profile,
                advanced_ats,
                jd_intelligence,
            )
        )

    all_recs.extend(
        _phase3_keyword_recommendations(
            advanced_ats
        )
    )

    all_recs.extend(
        _phase3_quality_recommendations(
            resume_quality
        )
    )

    all_recs.extend(
        _phase3_project_recommendations(
            resume_profile,
            advanced_ats,
        )
    )

    prioritized = _prioritize_recommendations(
        all_recs
    )

    critical = [
        r for r in prioritized
        if r.priority == Priority.CRITICAL
    ]

    high = [
        r for r in prioritized
        if r.priority == Priority.HIGH
    ]

    medium = [
        r for r in prioritized
        if r.priority == Priority.MEDIUM
    ]

    low = [
        r for r in prioritized
        if r.priority == Priority.LOW
    ]

    missing_skills = _phase3_dedupe(
        _phase3_get(
            advanced_ats,
            'missing_skills',
            [],
        )
    )

    required_skills = {
        skill.lower()
        for skill in _phase3_dedupe(
            _phase3_get(
                jd_intelligence,
                'required_skills',
                [],
            )
        )
    } if jd_intelligence is not None else set()

    top_missing_skills = [
        skill
        for skill in missing_skills
        if skill.lower() in required_skills
    ][:5]

    estimated_improvement = min(
        30.0,
        sum(
            recommendation.impact_score
            for recommendation in prioritized
        ),
    )

    return {
        'all_recommendations': prioritized,
        'critical_recommendations': critical,
        'high_recommendations': high,
        'medium_recommendations': medium,
        'low_recommendations': low,
        'total_count': len(prioritized),
        'estimated_improvement': estimated_improvement,
        'strengths': _phase3_build_strengths(
            resume_quality,
            advanced_ats,
            jd_intelligence,
        ),
        'top_missing_skills': top_missing_skills,
    }


#orchestrator of this file
def generate_all_recommendations(
    skill_validation_results: Dict,
    grammar_results: Dict,
    location_results: Dict,
    score_results: Dict,
    sections: Dict[str, str],
    keyword_analysis: Optional[Dict] = None,
    resume_keywords: Optional[List[str]] = None,
    resume_profile=None,
    resume_quality=None,
    advanced_ats=None,
    jd_intelligence=None,
) -> Dict:

    all_recs = []

    # Collect from all five domain generators
    all_recs.extend(generate_skill_recommendations(skill_validation_results))
    all_recs.extend(generate_grammar_recommendations(grammar_results))
    all_recs.extend(generate_location_recommendations(location_results))
    all_recs.extend(generate_keyword_recommendations(keyword_analysis, resume_keywords))
    all_recs.extend(generate_formatting_recommendations(score_results, sections))

    # Phase 3F: add evidence-aware recommendations when the newer
    # structured analysis results are available. Existing callers that
    # do not pass these values continue to work unchanged.
    if (
        resume_profile is not None
        and advanced_ats is not None
    ):
        phase3f_result = generate_ai_recommendations(
            resume_profile=resume_profile,
            resume_quality=resume_quality,
            advanced_ats=advanced_ats,
            jd_intelligence=jd_intelligence,
        )
        all_recs.extend(
            phase3f_result.get('all_recommendations', [])
        )

    #Sort: critical first, highest impact within each tier
    prioritized = _prioritize_recommendations(all_recs)

    #Group by priority level for convenient access
    critical = [r for r in prioritized if r.priority == Priority.CRITICAL]
    high     = [r for r in prioritized if r.priority == Priority.HIGH]
    medium   = [r for r in prioritized if r.priority == Priority.MEDIUM]
    low      = [r for r in prioritized if r.priority == Priority.LOW]

    # Estimate improvement potential (sum of impact scores, capped at 30)
    estimated_improvement = min(30.0, sum(r.impact_score for r in prioritized))

    return {
        'all_recommendations':      prioritized,
        'critical_recommendations': critical,
        'high_recommendations':     high,
        'medium_recommendations':   medium,
        'low_recommendations':      low,
        'total_count':              len(prioritized),
        'estimated_improvement':    estimated_improvement,
    }

def format_recommendations_for_api(recommendations_result: Dict) -> List[Dict]:
    priority_icons = {
        Priority.CRITICAL: '🔴',
        Priority.HIGH:     '🟠',
        Priority.MEDIUM:   '🟡',
        Priority.LOW:      '🟢',
    }
    priority_labels = {
        Priority.CRITICAL: 'Critical',
        Priority.HIGH:     'High Priority',
        Priority.MEDIUM:   'Medium Priority',
        Priority.LOW:      'Low Priority',
    }

    return [
        {
            'title':          rec.title,
            'description':    rec.description,
            'priority_icon':  priority_icons[rec.priority],
            'priority_label': priority_labels[rec.priority],
            'priority_value': rec.priority.value,
            'impact_score':   rec.impact_score,
            'category':       rec.category,
            'action_items':   rec.action_items,
        }
        for rec in recommendations_result.get('all_recommendations', [])
    ]

def get_recommendation_summary(recommendations_result: Dict) -> str:
    total       = recommendations_result.get('total_count', 0)
    critical    = len(recommendations_result.get('critical_recommendations', []))
    high        = len(recommendations_result.get('high_recommendations', []))
    improvement = recommendations_result.get('estimated_improvement', 0.0)

    if total == 0:
        return 'Excellent! No major recommendations. Your resume is well-optimized.'

    if critical > 0:
        return (
            f'Found {total} recommendation(s) including {critical} critical issue(s). '
            f'Addressing these could improve your score by up to {improvement:.0f} points.'
        )
    elif high > 0:
        return (
            f'Found {total} recommendation(s) including {high} high-priority item(s). '
            f'Addressing these could improve your score by up to {improvement:.0f} points.'
        )
    else:
        return (
            f'Found {total} recommendation(s) for improvement. '
            f'Addressing these could improve your score by up to {improvement:.0f} points.'
        )

import re
from typing import Dict, List, Optional, Tuple

from backend.models.schemas import (
    JDExperienceRequirement,
    JDIntelligenceResult,
    JDRequirement,
)


# ============================================================================
# TECHNOLOGY VOCABULARY
# ============================================================================

TECH_SYNONYMS = {
    "python": ["python"],
    "java": ["java"],
    "javascript": ["javascript", "java script"],
    "typescript": ["typescript", "type script"],
    "c++": ["c++", "cpp"],
    "c#": ["c#", "csharp"],
    "react": ["react", "react.js", "reactjs"],
    "angular": ["angular"],
    "vue": ["vue", "vue.js", "vuejs"],
    "node.js": ["node", "node.js", "nodejs"],
    "express.js": ["express", "express.js", "expressjs"],
    "fastapi": ["fastapi"],
    "django": ["django"],
    "flask": ["flask"],
    "spring": ["spring", "spring boot"],
    "sql": ["sql"],
    "mysql": ["mysql"],
    "postgresql": ["postgresql", "postgres"],
    "mongodb": ["mongodb", "mongo db", "mongo"],
    "redis": ["redis"],
    "docker": ["docker"],
    "kubernetes": ["kubernetes", "k8s"],
    "aws": ["aws", "amazon web services"],
    "azure": ["azure"],
    "gcp": ["gcp", "google cloud"],
    "git": ["git"],
    "github": ["github"],
    "gitlab": ["gitlab"],
    "rest api": ["rest api", "restful api", "rest apis", "restful apis"],
    "graphql": ["graphql"],
    "microservices": ["microservices", "microservice"],
    "machine learning": ["machine learning"],
    "deep learning": ["deep learning"],
    "artificial intelligence": ["artificial intelligence"],
    "nlp": ["nlp", "natural language processing"],
    "computer vision": ["computer vision"],
    "tensorflow": ["tensorflow"],
    "pytorch": ["pytorch"],
    "scikit-learn": ["scikit-learn", "scikit learn", "sklearn"],
    "pandas": ["pandas"],
    "numpy": ["numpy"],
    "langchain": ["langchain"],
    "langgraph": ["langgraph"],
    "llm": ["llm", "large language model", "large language models"],
    "rag": ["rag", "retrieval augmented generation"],
    "generative ai": ["generative ai", "gen ai", "genai"],
}


SOFT_SKILLS = {
    "communication",
    "leadership",
    "teamwork",
    "collaboration",
    "problem solving",
    "problem-solving",
    "time management",
    "adaptability",
    "critical thinking",
    "analytical thinking",
    "presentation",
    "interpersonal skills",
    "organization",
    "ownership",
    "initiative",
}


GENERIC_TERMS = {
    "experience",
    "knowledge",
    "skills",
    "skill",
    "ability",
    "work",
    "working",
    "strong",
    "good",
    "excellent",
    "understanding",
    "development",
    "developer",
    "engineering",
    "engineer",
    "role",
    "candidate",
    "team",
    "company",
    "position",
    "responsibilities",
    "responsibility",
    "requirements",
    "requirement",
    "preferred",
    "required",
    "qualification",
    "qualifications",
    "using",
    "use",
    "build",
    "building",
    "develop",
    "developing",
    "maintain",
    "maintaining",
    "write",
    "writing",
    "clean",
    "maintainable",
}


# ============================================================================
# ROLE / DOMAIN VOCABULARY
# ============================================================================

DOMAIN_PATTERNS = [
    (
        "backend development",
        [
            "backend",
            "back-end",
            "server-side",
            "rest api",
            "restful api",
            "microservices",
            "backend applications",
            "backend services",
        ],
    ),
    (
        "frontend development",
        [
            "frontend",
            "front-end",
            "ui development",
            "user interface",
            "frontend applications",
        ],
    ),
    (
        "full-stack development",
        [
            "full stack",
            "full-stack",
            "fullstack",
        ],
    ),
    (
        "data science",
        [
            "data science",
            "data scientist",
            "data analysis",
            "data analytics",
        ],
    ),
    (
        "artificial intelligence",
        [
            "artificial intelligence",
            "machine learning",
            "deep learning",
            "generative ai",
            "large language model",
            "natural language processing",
        ],
    ),
    (
        "devops / cloud",
        [
            "devops",
            "cloud infrastructure",
            "cloud engineering",
            "infrastructure",
            "site reliability",
            "aws",
            "azure",
            "kubernetes",
        ],
    ),
    (
        "cybersecurity",
        [
            "cybersecurity",
            "cyber security",
            "information security",
            "application security",
        ],
    ),
    (
        "mobile development",
        [
            "android development",
            "ios development",
            "mobile development",
            "mobile application",
        ],
    ),
]


ROLE_KEYWORDS = {
    "backend": "backend development",
    "back-end": "backend development",
    "frontend": "frontend development",
    "front-end": "frontend development",
    "full stack": "full-stack development",
    "full-stack": "full-stack development",
    "fullstack": "full-stack development",
    "machine learning": "artificial intelligence",
    "artificial intelligence": "artificial intelligence",
    "data scientist": "data science",
    "data science": "data science",
    "devops": "devops / cloud",
    "cloud": "devops / cloud",
    "cybersecurity": "cybersecurity",
    "cyber security": "cybersecurity",
    "android": "mobile development",
    "ios": "mobile development",
}


# ============================================================================
# NORMALIZATION
# ============================================================================

def _normalize(text: str) -> str:
    text = text.lower()

    text = (
        text.replace("–", "-")
        .replace("—", "-")
        .replace("’", "'")
    )

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def _clean_line(line: str) -> str:
    line = line.strip()

    line = re.sub(
        r"^[\-\*\•\▪\◦\u2022\d\.\)\(]+\s*",
        "",
        line,
    )

    return line.strip()


def _contains_term(text: str, term: str) -> bool:
    """
    Exact phrase-aware matching.

    Important:
    We do NOT use simple `term in text` for short terms such as
    'git', 'ts', etc. because that can create false positives.
    """

    normalized_text = _normalize(text)
    normalized_term = _normalize(term)

    if not normalized_text or not normalized_term:
        return False

    escaped = re.escape(normalized_term)

    # Word boundaries prevent:
    # git -> legitimate
    # git -> not matched inside "digital"
    pattern = rf"(?<![a-z0-9+#]){escaped}(?![a-z0-9+#])"

    return re.search(pattern, normalized_text) is not None


# ============================================================================
# SECTION DETECTION
# ============================================================================

def _detect_section(line: str) -> Optional[str]:
    normalized = _normalize(line)
    normalized = normalized.rstrip(":").strip()

    section_aliases = {
        "responsibilities": {
            "responsibilities",
            "key responsibilities",
            "roles and responsibilities",
            "what you will do",
            "what you'll do",
            "your responsibilities",
            "job responsibilities",
            "duties",
            "what you bring",
        },
        "requirements": {
            "requirements",
            "required qualifications",
            "required skills",
            "must have",
            "minimum qualifications",
            "basic qualifications",
            "required experience",
        },
        "preferred": {
            "preferred qualifications",
            "preferred skills",
            "nice to have",
            "nice-to-have",
            "good to have",
            "preferred",
            "bonus",
            "plus",
            "preferred experience",
        },
        "education": {
            "education",
            "educational qualifications",
            "academic qualifications",
            "education requirements",
        },
    }

    for section, aliases in section_aliases.items():
        if normalized in aliases:
            return section

    return None


def _split_sections(text: str) -> Dict[str, List[str]]:
    sections = {
        "general": [],
        "responsibilities": [],
        "requirements": [],
        "preferred": [],
        "education": [],
    }

    current_section = "general"

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        detected = _detect_section(line)

        if detected:
            current_section = detected
            continue

        cleaned = _clean_line(line)

        if cleaned:
            sections[current_section].append(cleaned)

    return sections


# ============================================================================
# JOB TITLE
# ============================================================================

def _looks_like_section_or_metadata(line: str) -> bool:
    normalized = _normalize(line)

    blocked = {
        "requirements",
        "responsibilities",
        "preferred qualifications",
        "preferred skills",
        "education",
        "qualifications",
        "job description",
        "about the role",
        "about us",
    }

    return normalized.rstrip(":") in blocked


def _extract_job_title(
    text: str,
    sections: Dict[str, List[str]],
) -> Optional[str]:

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    # ------------------------------------------------------------
    # Explicit metadata
    # ------------------------------------------------------------

    title_patterns = [
        r"^\s*job\s*title\s*:\s*(.+)$",
        r"^\s*position\s*:\s*(.+)$",
        r"^\s*role\s*:\s*(.+)$",
        r"^\s*title\s*:\s*(.+)$",
    ]

    for line in lines[:20]:
        for pattern in title_patterns:
            match = re.match(
                pattern,
                line,
                flags=re.IGNORECASE,
            )

            if match:
                return match.group(1).strip()

    # ------------------------------------------------------------
    # First meaningful line
    #
    # Most JDs begin with the actual role.
    # Prefer this over searching for a shorter role phrase.
    # ------------------------------------------------------------

    for line in lines[:10]:

        cleaned = _clean_line(line)

        if not cleaned:
            continue

        if _looks_like_section_or_metadata(cleaned):
            continue

        if len(cleaned.split()) <= 10 and len(cleaned) <= 120:

            normalized = _normalize(cleaned)

            # Skip obvious sentence-style descriptions.
            sentence_markers = [
                "we are looking",
                "we're looking",
                "the candidate",
                "you will",
                "we seek",
                "about the",
            ]

            if any(
                marker in normalized
                for marker in sentence_markers
            ):
                continue

            # A title usually contains a role word.
            role_words = [
                "developer",
                "engineer",
                "scientist",
                "analyst",
                "architect",
                "designer",
                "manager",
                "intern",
                "specialist",
                "administrator",
            ]

            if any(
                word in normalized
                for word in role_words
            ):
                return cleaned

    return None


# ============================================================================
# SENIORITY
# ============================================================================

def _extract_seniority(text: str) -> Optional[str]:
    normalized = _normalize(text)

    seniority_patterns = [
        ("intern", r"\bintern(ship)?\b"),
        (
            "entry-level",
            r"\bentry[- ]level\b|\bfresher\b|\bgraduate\b",
        ),
        ("junior", r"\bjunior\b"),
        (
            "mid-level",
            r"\bmid[- ]level\b|\bintermediate\b",
        ),
        ("senior", r"\bsenior\b"),
        ("lead", r"\blead\b"),
        ("principal", r"\bprincipal\b"),
        ("staff", r"\bstaff\b"),
        ("manager", r"\bmanager\b"),
        ("director", r"\bdirector\b"),
    ]

    for label, pattern in seniority_patterns:
        if re.search(pattern, normalized):
            return label

    return None


# ============================================================================
# DOMAIN
# ============================================================================

def _extract_domain(
    text: str,
    job_title: Optional[str],
    responsibilities: List[str],
) -> Optional[str]:

    normalized_text = _normalize(text)
    normalized_title = _normalize(job_title or "")
    normalized_responsibilities = _normalize(
        " ".join(responsibilities)
    )

    # ------------------------------------------------------------
    # 1. Role title gets strongest priority.
    # ------------------------------------------------------------

    for role_keyword, domain in ROLE_KEYWORDS.items():
        if _contains_term(normalized_title, role_keyword):
            return domain

    # ------------------------------------------------------------
    # 2. Responsibilities are stronger evidence than preferred
    #    technologies.
    # ------------------------------------------------------------

    responsibility_scores = {}

    for domain, terms in DOMAIN_PATTERNS:

        score = 0

        for term in terms:
            if _contains_term(
                normalized_responsibilities,
                term,
            ):
                score += 2

        responsibility_scores[domain] = score

    best_domain = None
    best_score = 0

    for domain, score in responsibility_scores.items():
        if score > best_score:
            best_domain = domain
            best_score = score

    if best_domain:
        return best_domain

    # ------------------------------------------------------------
    # 3. Whole JD fallback.
    # ------------------------------------------------------------

    text_scores = {}

    for domain, terms in DOMAIN_PATTERNS:

        score = 0

        for term in terms:
            if _contains_term(
                normalized_text,
                term,
            ):
                score += 1

        text_scores[domain] = score

    best_domain = None
    best_score = 0

    for domain, score in text_scores.items():
        if score > best_score:
            best_domain = domain
            best_score = score

    return best_domain


# ============================================================================
# EXPERIENCE
# ============================================================================

def _extract_experience_requirement(
    text: str,
) -> JDExperienceRequirement:

    normalized = _normalize(text)

    values = []

    patterns = [
        r"(\d+(?:\.\d+)?)\s*\+\s*(?:years?|yrs?)",
        r"minimum\s+of\s+(\d+(?:\.\d+)?)\s*(?:years?|yrs?)",
        r"at\s+least\s+(\d+(?:\.\d+)?)\s*(?:years?|yrs?)",
        r"(\d+(?:\.\d+)?)\s*(?:to|-)\s*(\d+(?:\.\d+)?)\s*(?:years?|yrs?)",
    ]

    for pattern in patterns:

        for match in re.finditer(
            pattern,
            normalized,
        ):

            try:

                first = float(match.group(1))
                values.append(first)

                if match.lastindex and match.lastindex >= 2:
                    second = float(match.group(2))

                    values.append(second)

            except ValueError:
                continue

    minimum_years = min(values) if values else None

    raw_text = None

    if minimum_years is not None:

        matches = re.findall(
            r".{0,80}"
            r"\d+(?:\.\d+)?"
            r"\s*\+?"
            r"\s*(?:years?|yrs?)"
            r".{0,80}",
            text,
            flags=re.IGNORECASE,
        )

        if matches:
            raw_text = matches[0].strip()

    return JDExperienceRequirement(
        minimum_years=minimum_years,
        maximum_years=None,
        raw_text=raw_text,
    )


# ============================================================================
# TECHNOLOGY EXTRACTION
# ============================================================================

def _extract_technical_skills(
    text: str,
) -> List[str]:

    found = []

    for canonical, aliases in TECH_SYNONYMS.items():

        for alias in aliases:

            if _contains_term(text, alias):
                found.append(canonical)
                break

    return sorted(set(found))


# ============================================================================
# SOFT SKILLS
# ============================================================================

def _extract_soft_skills(
    text: str,
) -> List[str]:

    found = []

    for skill in SOFT_SKILLS:

        if _contains_term(text, skill):
            found.append(skill)

    return sorted(set(found))


# ============================================================================
# PRIORITY
# ============================================================================

def _skill_priority(
    skill: str,
    required_text: str,
    preferred_text: str,
    full_text: str,
) -> str:

    # Explicit section has highest priority.

    if _contains_term(preferred_text, skill):
        return "preferred"

    if _contains_term(required_text, skill):
        return "required"

    normalized = _normalize(full_text)

    aliases = TECH_SYNONYMS.get(
        skill,
        [skill],
    )

    for alias in aliases:

        escaped = re.escape(
            _normalize(alias)
        )

        required_patterns = [
            rf"\b(required|must have|mandatory|essential)\b"
            rf".{{0,100}}{escaped}",

            rf"{escaped}.{{0,100}}"
            rf"\b(required|must have|mandatory|essential)\b",
        ]

        preferred_patterns = [
            rf"\b(preferred|nice to have|bonus|plus)\b"
            rf".{{0,100}}{escaped}",

            rf"{escaped}.{{0,100}}"
            rf"\b(preferred|nice to have|bonus|plus)\b",
        ]

        for pattern in preferred_patterns:

            if re.search(
                pattern,
                normalized,
            ):
                return "preferred"

        for pattern in required_patterns:

            if re.search(
                pattern,
                normalized,
            ):
                return "required"

    # If the skill appears in the JD but isn't explicitly
    # marked preferred, treat it as required.
    return "required"


# ============================================================================
# RESPONSIBILITIES
# ============================================================================

def _extract_responsibilities(
    lines: List[str],
) -> List[str]:

    responsibilities = []

    for line in lines:

        cleaned = _clean_line(line)

        if len(cleaned) < 10:
            continue

        responsibilities.append(cleaned)

    return responsibilities[:20]


# ============================================================================
# EDUCATION
# ============================================================================

def _extract_education(
    text: str,
    education_lines: List[str],
) -> List[str]:

    result = []

    education_patterns = [
        r"\bbachelor(?:'s)?\b",
        r"\bmaster(?:'s)?\b",
        r"\bph\.?d\.?\b",
        r"\bdegree\b",
        r"\bdiploma\b",
        r"\bcomputer science\b",
        r"\binformation technology\b",
        r"\bengineering\b",
    ]

    for line in education_lines:

        normalized = _normalize(line)

        if any(
            re.search(
                pattern,
                normalized,
            )
            for pattern in education_patterns
        ):
            result.append(line)

    # Fallback when there is no explicit Education section.

    if not result:

        for pattern in education_patterns:

            match = re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            if match:
                result.append(
                    match.group(0)
                )
                break

    return list(
        dict.fromkeys(result)
    )[:10]


# ============================================================================
# REQUIREMENT OBJECTS
# ============================================================================

def _build_requirements(
    skills: List[str],
    category: str,
    priority: str,
) -> List[JDRequirement]:

    return [
        JDRequirement(
            requirement=skill,
            category=category,
            priority=priority,
            evidence=None,
        )
        for skill in skills
    ]


# ============================================================================
# KEYWORD EXTRACTION
# ============================================================================

def _is_meaningful_phrase(
    phrase: str,
) -> bool:

    normalized = _normalize(phrase)
    words = normalized.split()

    if not words:
        return False

    # Remove phrases containing obvious filler words.

    bad_words = {
        "and",
        "or",
        "the",
        "a",
        "an",
        "with",
        "for",
        "to",
        "of",
        "in",
        "on",
        "as",
        "by",
        "from",
        "be",
        "is",
        "are",
        "will",
        "can",
        "should",
    }

    # Reject if the phrase begins or ends with filler.

    if words[0] in bad_words:
        return False

    if words[-1] in bad_words:
        return False

    # Reject very generic phrases.

    meaningful_words = [
        word
        for word in words
        if word not in GENERIC_TERMS
        and word not in bad_words
    ]

    if len(meaningful_words) < 2:
        return False

    return True


def _extract_keywords(
    text: str,
    technical_skills: List[str],
    soft_skills: List[str],
    responsibilities: List[str],
) -> List[str]:

    keywords = []

    # ------------------------------------------------------------
    # Technical skills are the strongest keywords.
    # ------------------------------------------------------------

    keywords.extend(
        technical_skills
    )

    # ------------------------------------------------------------
    # Soft skills.
    # ------------------------------------------------------------

    keywords.extend(
        soft_skills
    )

    # ------------------------------------------------------------
    # Extract meaningful phrases from responsibilities.
    #
    # Instead of blindly generating every 2/3-word phrase,
    # identify phrases around useful technical/action concepts.
    # ------------------------------------------------------------

    responsibility_patterns = [
        r"\bbuild and maintain ([a-z0-9 .+/&-]+)",
        r"\bdesign and develop ([a-z0-9 .+/&-]+)",
        r"\bwork with ([a-z0-9 .+/&-]+)",
        r"\bdevelop ([a-z0-9 .+/&-]+)",
        r"\bbuild ([a-z0-9 .+/&-]+)",
        r"\bdesign ([a-z0-9 .+/&-]+)",
    ]

    for responsibility in responsibilities:

        normalized = _normalize(
            responsibility
        )

        for pattern in responsibility_patterns:

            match = re.search(
                pattern,
                normalized,
            )

            if not match:
                continue

            phrase = match.group(1)

            # Stop at common sentence boundaries.

            phrase = re.split(
                r"\b(?:and|while|with|to|that)\b",
                phrase,
                maxsplit=1,
            )[0]

            phrase = phrase.strip(
                " .,;:"
            )

            if (
                2 <= len(phrase.split()) <= 5
                and _is_meaningful_phrase(phrase)
            ):
                keywords.append(
                    phrase
                )

    # ------------------------------------------------------------
    # Role-specific phrases.
    # ------------------------------------------------------------

    role_phrases = [
        "backend applications",
        "backend services",
        "frontend applications",
        "rest api development",
        "api development",
        "database development",
        "scalable applications",
        "scalable backend applications",
        "microservice architecture",
        "cloud infrastructure",
        "machine learning models",
        "natural language processing",
        "data analysis",
    ]

    for phrase in role_phrases:

        if _contains_term(
            text,
            phrase,
        ):
            keywords.append(
                phrase
            )

    # ------------------------------------------------------------
    # Deduplicate while preserving order.
    # ------------------------------------------------------------

    unique = []

    for keyword in keywords:

        keyword = _normalize(
            keyword
        ).strip()

        if not keyword:
            continue

        if keyword not in unique:
            unique.append(
                keyword
            )

    return unique[:50]


# ============================================================================
# JD QUALITY
# ============================================================================

def _calculate_jd_quality(
    title: Optional[str],
    required_skills: List[str],
    preferred_skills: List[str],
    responsibilities: List[str],
    experience: JDExperienceRequirement,
    education: List[str],
) -> Tuple[int, List[str], List[str]]:

    score = 0

    strengths = []
    weaknesses = []

    if title:

        score += 15

        strengths.append(
            "The job description clearly identifies a target role."
        )

    else:

        weaknesses.append(
            "The job description does not clearly identify a job title."
        )

    if required_skills:

        score += 25

        strengths.append(
            "The job description contains identifiable technical requirements."
        )

    else:

        weaknesses.append(
            "Few or no explicit technical requirements were detected."
        )

    if responsibilities:

        score += 25

        if len(responsibilities) >= 3:

            strengths.append(
                "The job description provides multiple responsibilities."
            )

    else:

        weaknesses.append(
            "No clear responsibilities section was detected."
        )

    if experience.minimum_years is not None:

        score += 15

        strengths.append(
            "An experience requirement was identified."
        )

    else:

        weaknesses.append(
            "No explicit minimum years of experience were detected."
        )

    if education:

        score += 10

        strengths.append(
            "Education requirements were identified."
        )

    else:

        weaknesses.append(
            "No explicit education requirement was detected."
        )

    if preferred_skills:

        score += 10

        strengths.append(
            "Preferred or nice-to-have skills were identified."
        )

    return (
        min(score, 100),
        strengths,
        weaknesses,
    )


# ============================================================================
# MAIN ENGINE
# ============================================================================

def analyze_job_description(
    jd_text: str,
) -> JDIntelligenceResult:

    if not jd_text or not jd_text.strip():

        raise ValueError(
            "Job description cannot be empty."
        )

    jd_text = jd_text.strip()

    sections = _split_sections(
        jd_text
    )

    # ------------------------------------------------------------
    # Core job information
    # ------------------------------------------------------------

    job_title = _extract_job_title(
        jd_text,
        sections,
    )

    seniority = _extract_seniority(
        jd_text
    )

    responsibilities = _extract_responsibilities(
        sections["responsibilities"]
    )

    domain = _extract_domain(
        text=jd_text,
        job_title=job_title,
        responsibilities=responsibilities,
    )

    experience = _extract_experience_requirement(
        jd_text
    )

    # ------------------------------------------------------------
    # Skill extraction
    # ------------------------------------------------------------

    required_section_text = "\n".join(
        sections["requirements"]
    )

    preferred_section_text = "\n".join(
        sections["preferred"]
    )

    all_skills = _extract_technical_skills(
        jd_text
    )

    required_skills_all = _extract_technical_skills(
        required_section_text
    )

    preferred_skills_all = _extract_technical_skills(
        preferred_section_text
    )

    required_skills = []
    preferred_skills = []

    for skill in all_skills:

        priority = _skill_priority(
            skill=skill,
            required_text=required_section_text,
            preferred_text=preferred_section_text,
            full_text=jd_text,
        )

        if priority == "preferred":

            preferred_skills.append(
                skill
            )

        else:

            required_skills.append(
                skill
            )

    # Explicit requirements always win.

    for skill in required_skills_all:

        if skill not in required_skills:

            required_skills.append(
                skill
            )

        if skill in preferred_skills:

            preferred_skills.remove(
                skill
            )

    # Explicit preferred skills.

    for skill in preferred_skills_all:

        if skill not in required_skills:

            if skill not in preferred_skills:

                preferred_skills.append(
                    skill
                )

    required_skills = sorted(
        set(required_skills)
    )

    preferred_skills = sorted(
        set(preferred_skills)
    )

    # ------------------------------------------------------------
    # Other requirement categories
    # ------------------------------------------------------------

    soft_skills = _extract_soft_skills(
        jd_text
    )

    education = _extract_education(
        jd_text,
        sections["education"],
    )

    technical_requirements = (
        _build_requirements(
            required_skills,
            category="technical",
            priority="required",
        )
        +
        _build_requirements(
            preferred_skills,
            category="technical",
            priority="preferred",
        )
    )

    soft_requirements = _build_requirements(
        soft_skills,
        category="soft-skill",
        priority="required",
    )

    keywords = _extract_keywords(
        text=jd_text,
        technical_skills=all_skills,
        soft_skills=soft_skills,
        responsibilities=responsibilities,
    )

    # ------------------------------------------------------------
    # Quality
    # ------------------------------------------------------------

    (
        quality_score,
        strengths,
        weaknesses,
    ) = _calculate_jd_quality(
        title=job_title,
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        responsibilities=responsibilities,
        experience=experience,
        education=education,
    )

    # ------------------------------------------------------------
    # Final structured result
    # ------------------------------------------------------------

    return JDIntelligenceResult(
        job_title=job_title,
        seniority=seniority,
        domain=domain,
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        responsibilities=responsibilities,
        experience_requirement=experience,
        education_requirements=education,
        technical_requirements=technical_requirements,
        soft_skill_requirements=soft_requirements,
        keywords=keywords,
        must_have_count=len(
            required_skills
        ),
        preferred_count=len(
            preferred_skills
        ),
        jd_quality_score=quality_score,
        strengths=strengths,
        weaknesses=weaknesses,
    )
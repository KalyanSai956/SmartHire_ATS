"""
Interview evaluation rubrics.

The rubric is intentionally deterministic and explicit.
The LLM is used to assess the candidate's answer against
these rules, not to invent its own scoring system.
"""

from typing import Dict


# ============================================================
# SCORE BANDS
# ============================================================

SCORE_BANDS: Dict[str, str] = {
    "excellent": "90-100",
    "strong": "75-89",
    "good": "60-74",
    "needs_improvement": "40-59",
    "weak": "0-39",
}


# ============================================================
# GENERAL RUBRIC
# ============================================================

GENERAL_RUBRIC = """
Use a 0-100 scale for every evaluation dimension.

90-100:
Excellent. The answer is accurate, directly addresses the
question, communicates clearly, and demonstrates strong depth,
reasoning, examples, trade-offs, or practical understanding
where appropriate.

75-89:
Strong. The answer is mostly accurate and relevant, with good
understanding and communication. Minor omissions may exist.

60-74:
Good. The answer demonstrates a reasonable understanding but
has noticeable omissions, limited depth, or minor inaccuracies.

40-59:
Needs improvement. The answer contains partial understanding,
significant omissions, weak reasoning, unclear communication,
or important inaccuracies.

0-39:
Weak. The answer is largely incorrect, irrelevant, extremely
incomplete, or demonstrates very limited understanding.

Do not award points merely because the candidate uses technical
buzzwords.

Do not penalize a candidate for not mentioning information that
is irrelevant to the question.

Do not invent facts about the candidate.

Evaluate only the answer that was actually provided.
"""


# ============================================================
# DIMENSION RUBRICS
# ============================================================

TECHNICAL_RUBRIC = """
TECHNICAL SCORE:

Evaluate:
- correctness of technical statements
- understanding of the underlying concept
- appropriate terminology
- correct use of technical mechanisms
- ability to explain why something works
- ability to distinguish related concepts when relevant

For coding or technical questions, incorrect core concepts
should materially reduce the technical score.
"""

RELEVANCE_RUBRIC = """
RELEVANCE SCORE:

Evaluate:
- whether the answer directly addresses the question
- whether the candidate covers the requested subject
- whether examples actually support the answer
- whether unnecessary tangents dominate the response

A technically correct answer that does not answer the question
should receive a lower relevance score.
"""

CLARITY_RUBRIC = """
CLARITY SCORE:

Evaluate:
- organization
- understandable language
- logical progression
- ability to communicate technical ideas
- avoidance of excessive ambiguity
- whether the listener could reasonably follow the explanation

Do not confuse simple language with weak technical ability.
A concise but clear answer can receive a strong clarity score.
"""

DEPTH_RUBRIC = """
DEPTH SCORE:

Evaluate:
- reasoning
- explanation beyond surface-level definitions
- examples
- trade-offs
- edge cases
- practical considerations
- cause-and-effect understanding

Not every question requires all of these.
Only evaluate depth using factors relevant to the question.
"""


# ============================================================
# CATEGORY-SPECIFIC GUIDANCE
# ============================================================

CATEGORY_RUBRICS: Dict[str, str] = {
    "technical": """
For a technical question, prioritize conceptual correctness,
implementation understanding, and technical reasoning.
""",

    "behavioral": """
For a behavioral question, evaluate whether the candidate
actually answers the behavioral situation and demonstrates
clear reasoning, actions, ownership, and outcome.

Do not require a specific framework such as STAR unless the
question explicitly asks for structured storytelling.
""",

    "project": """
For a project question, evaluate whether the candidate can
explain the project they claim to have worked on.

Look for:
- architecture understanding
- personal contribution
- technology choices
- implementation details
- challenges
- decisions
- results

Do not assume project details that are not present in the
candidate's answer.
""",

    "problem_solving": """
For a problem-solving question, evaluate:
- problem decomposition
- reasoning
- assumptions
- proposed approach
- trade-offs
- handling of edge cases
- practical execution
""",

    "system_design": """
For system-design questions, evaluate:
- requirement understanding
- component decomposition
- data flow
- scalability
- reliability
- consistency considerations
- bottlenecks
- trade-offs
- practical architecture decisions

Do not require every category when the question itself is
narrow.
""",

    "coding": """
For coding questions, evaluate:
- correctness of the proposed solution
- algorithmic reasoning
- complexity awareness
- edge cases
- implementation details

If actual code is not provided, do not claim that code is
correct or incorrect. Evaluate the explanation that was given.
""",
}


# ============================================================
# PROMPT BUILDER
# ============================================================

def build_evaluation_rubric(category: str) -> str:
    """
    Return the complete rubric for a question category.
    """

    normalized_category = (
        category or "technical"
    ).strip().lower()

    category_guidance = CATEGORY_RUBRICS.get(
        normalized_category,
        CATEGORY_RUBRICS["technical"],
    )

    return f"""
{GENERAL_RUBRIC}

{TECHNICAL_RUBRIC}

{RELEVANCE_RUBRIC}

{CLARITY_RUBRIC}

{DEPTH_RUBRIC}

CATEGORY-SPECIFIC GUIDANCE:
{category_guidance}
"""
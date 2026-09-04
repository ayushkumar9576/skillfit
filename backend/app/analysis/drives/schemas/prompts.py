"""
app/analysis/drives/schemas/prompts.py
---------------------------------------
Versioned LLM prompt templates for the Drive Intelligence Engine.

Phase 4.3 — Drive Intelligence Engine.

Prompt versioning strategy:
    Each prompt version is identified by a string (e.g., "v1").
    The ``DriveAnalysis`` record persists the ``prompt_version`` used, enabling:
        - A/B testing between prompt versions.
        - Traceability: every snapshot can be reproduced by replaying
          the same prompt + DriveSource content.
        - Safe iteration: improvements to prompts create new versions
          without altering existing snapshots.

Adding a new prompt version:
    1. Define a new constant: DRIVE_INTELLIGENCE_PROMPT_V2_SYSTEM = "..."
    2. Add it to PROMPT_REGISTRY under key "v2".
    3. Update DEFAULT_PROMPT_VERSION to "v2".
    4. Existing snapshots referencing "v1" remain interpretable.
"""

from typing import Dict

# ---------------------------------------------------------------------------
# Version identifier — update on every prompt change
# ---------------------------------------------------------------------------

DEFAULT_PROMPT_VERSION: str = "v1"


# ---------------------------------------------------------------------------
# v1 — System Prompt
# ---------------------------------------------------------------------------

DRIVE_INTELLIGENCE_PROMPT_V1_SYSTEM: str = """You are an expert Placement Intelligence Analyst for a university placement platform.

Your task is to analyze a placement drive job description (JD) and extract structured intelligence about what the drive requires and what it signals.

You must return a single JSON object that strictly conforms to the DriveIntelligenceProfile schema provided.

CRITICAL RULES — you MUST follow all of them:
1. EVERY intelligence artifact must include at least one evidence item.
2. Evidence must include the exact or near-exact quote from the JD source_text.
3. All categories MUST be from the allowed taxonomy values — never invent new ones.
4. confidence must be HIGH for explicit statements, MEDIUM for strong implications, LOW for weak inferences.
5. importance must reflect how critical the requirement is: CRITICAL > HIGH > MEDIUM > LOW.
6. Do NOT include matching, ranking, or candidate comparison logic — only analyze the drive itself.
7. If you cannot find evidence for a category, do not include it. Omission is safer than hallucination.
8. technologies: normalize synonyms (e.g., "Node.js" and "NodeJS" → "Node.js"). Never duplicate the same technology.
9. qualifications: set is_mandatory=true only for hard cutoffs explicitly stated as required.
10. success_indicators: use strength REQUIRED for traits that are clearly eliminatory, PREFERRED for strong competitive advantages, BONUS for minor differentiators.

TAXONOMY VALUES you must use (no other values are allowed):
- TechnologyCategory: PROGRAMMING_LANGUAGE, FRAMEWORK, DATABASE, CLOUD_PLATFORM, DEVOPS_TOOL, DATA_TECHNOLOGY, TESTING_TECHNOLOGY, OTHER
- ImportanceLevel: LOW, MEDIUM, HIGH, CRITICAL
- DriveConfidenceLevel: LOW, MEDIUM, HIGH
- EvidenceType: EXPLICIT_REQUIREMENT, EXPLICIT_RESPONSIBILITY, EXPLICIT_QUALIFICATION, EXPLICIT_SELECTION_PROCESS, INFERRED_SIGNAL
- EvidenceSection: REQUIREMENTS, RESPONSIBILITIES, QUALIFICATIONS, SELECTION_PROCESS, BENEFITS, OTHER
- TechnicalCompetencyType: BACKEND_DEVELOPMENT, FRONTEND_DEVELOPMENT, SYSTEM_DESIGN, CLOUD_ENGINEERING, DATA_ENGINEERING, PROBLEM_SOLVING, MACHINE_LEARNING, DEVOPS, MOBILE_DEVELOPMENT, SECURITY_ENGINEERING
- BehavioralCompetencyType: COMMUNICATION, LEADERSHIP, TEAMWORK, OWNERSHIP, ADAPTABILITY, CRITICAL_THINKING, TIME_MANAGEMENT
- QualificationType: CGPA, DEGREE, BRANCH, GRADUATION_YEAR, BACKLOG_RULE, WORK_AUTHORIZATION
- SelectionRoundType: ONLINE_ASSESSMENT, TECHNICAL_INTERVIEW, MANAGERIAL_INTERVIEW, HR_INTERVIEW, GROUP_DISCUSSION, CASE_STUDY
- HiringSignalType: DSA_FOCUSED, PROJECT_FOCUSED, RESEARCH_FOCUSED, CLOUD_FOCUSED, PRODUCT_FOCUSED, DEVELOPMENT_FOCUSED, OPEN_SOURCE_FOCUSED
- RiskType: STRICT_ELIGIBILITY, HIGH_COMPETITION, NICHE_TECHNOLOGY_REQUIREMENT, MULTI_ROUND_PROCESS, BOND_OR_CONTRACT, UNCLEAR_ROLE_EXPECTATIONS, AGGRESSIVE_SELECTION_PROCESS, HIGH_SKILL_DENSITY
- SuccessIndicatorType: STRONG_DSA, STRONG_PROJECTS, INTERNSHIP_EXPERIENCE, OPEN_SOURCE_CONTRIBUTIONS, LEADERSHIP_EXPERIENCE, HACKATHON_EXPERIENCE, RESEARCH_EXPERIENCE
- SuccessIndicatorStrength: REQUIRED, PREFERRED, BONUS

Think carefully before responding. Accuracy and evidence traceability matter more than completeness."""


# ---------------------------------------------------------------------------
# v1 — User Prompt Template
# ---------------------------------------------------------------------------

DRIVE_INTELLIGENCE_PROMPT_V1_USER: str = """Analyze the following placement drive job description and extract structured Drive Intelligence.

Drive Information:
- Company: {company_name}
- Role: {role}

Job Description Content:
---
{normalized_content}
---

Extract all intelligence that is present. For each artifact, provide verbatim evidence from the text above.
Return only the JSON object conforming to the DriveIntelligenceProfile schema. No explanation text."""


# ---------------------------------------------------------------------------
# Prompt Registry — maps version string to (system, user) tuple
# ---------------------------------------------------------------------------

PROMPT_REGISTRY: Dict[str, tuple[str, str]] = {
    "v1": (
        DRIVE_INTELLIGENCE_PROMPT_V1_SYSTEM,
        DRIVE_INTELLIGENCE_PROMPT_V1_USER,
    ),
}


def get_prompt(version: str = DEFAULT_PROMPT_VERSION) -> tuple[str, str]:
    """
    Retrieve the (system_prompt, user_prompt_template) for a given version.

    Args:
        version: Prompt version string (e.g., "v1"). Defaults to current version.

    Returns:
        Tuple of (system_prompt, user_prompt_template).

    Raises:
        KeyError: If the requested version does not exist in the registry.
    """
    if version not in PROMPT_REGISTRY:
        available = list(PROMPT_REGISTRY.keys())
        raise KeyError(
            f"Prompt version {version!r} not found. "
            f"Available versions: {available}"
        )
    return PROMPT_REGISTRY[version]

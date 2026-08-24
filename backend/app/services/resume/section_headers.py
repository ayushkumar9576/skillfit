"""
app/services/resume/section_headers.py
--------------------------------------
Configurable section header alias mapping and robust text normalization
for SkillFit Phase 3.4 – Resume Section Detection.

Responsibilities:
    - Normalize header candidate strings across case, decorators, punctuation, bullets.
    - Provide an extensible, centralized dictionary mapping alias phrases to ResumeSection enums.
    - Match candidate header lines against canonical sections while rejecting false positives.
"""

import re
from typing import Dict, Optional

from app.services.resume.section_types import ResumeSection

# Maximum allowed length and word count for a valid section header line
MAX_HEADER_CHARS: int = 60
MAX_HEADER_WORDS: int = 6

# ---------------------------------------------------------------------------
# Section Header Alias Mapping
# ---------------------------------------------------------------------------

SECTION_HEADER_MAP: Dict[str, ResumeSection] = {
    # -----------------------------------------------------------------------
    # Education
    # -----------------------------------------------------------------------
    "education": ResumeSection.EDUCATION,
    "academic background": ResumeSection.EDUCATION,
    "academic qualifications": ResumeSection.EDUCATION,
    "academic qualification": ResumeSection.EDUCATION,
    "educational details": ResumeSection.EDUCATION,
    "educational background": ResumeSection.EDUCATION,
    "educational qualifications": ResumeSection.EDUCATION,
    "educational qualification": ResumeSection.EDUCATION,
    "academics": ResumeSection.EDUCATION,
    "academic record": ResumeSection.EDUCATION,
    "academic records": ResumeSection.EDUCATION,
    "academic profile": ResumeSection.EDUCATION,
    "academic history": ResumeSection.EDUCATION,
    "qualifications": ResumeSection.EDUCATION,
    "education and training": ResumeSection.EDUCATION,
    "education & training": ResumeSection.EDUCATION,
    "education & qualifications": ResumeSection.EDUCATION,
    "formal education": ResumeSection.EDUCATION,
    "scholastic achievements": ResumeSection.EDUCATION,
    "scholastic background": ResumeSection.EDUCATION,
    "studies": ResumeSection.EDUCATION,

    # -----------------------------------------------------------------------
    # Skills
    # -----------------------------------------------------------------------
    "skills": ResumeSection.SKILLS,
    "technical skills": ResumeSection.SKILLS,
    "core competencies": ResumeSection.SKILLS,
    "technologies": ResumeSection.SKILLS,
    "technical expertise": ResumeSection.SKILLS,
    "key skills": ResumeSection.SKILLS,
    "professional skills": ResumeSection.SKILLS,
    "areas of expertise": ResumeSection.SKILLS,
    "skill set": ResumeSection.SKILLS,
    "skills & abilities": ResumeSection.SKILLS,
    "skills and abilities": ResumeSection.SKILLS,
    "skills & competencies": ResumeSection.SKILLS,
    "skills and competencies": ResumeSection.SKILLS,
    "technical proficiency": ResumeSection.SKILLS,
    "technical proficiencies": ResumeSection.SKILLS,
    "technical competencies": ResumeSection.SKILLS,
    "programming languages": ResumeSection.SKILLS,
    "tech stack": ResumeSection.SKILLS,
    "tools & technologies": ResumeSection.SKILLS,
    "tools and technologies": ResumeSection.SKILLS,
    "tools & tech": ResumeSection.SKILLS,
    "technical strengths": ResumeSection.SKILLS,
    "frameworks & libraries": ResumeSection.SKILLS,
    "frameworks and libraries": ResumeSection.SKILLS,
    "frameworks & tools": ResumeSection.SKILLS,
    "frameworks and tools": ResumeSection.SKILLS,
    "languages & frameworks": ResumeSection.SKILLS,
    "languages and frameworks": ResumeSection.SKILLS,
    "languages & technologies": ResumeSection.SKILLS,
    "languages and technologies": ResumeSection.SKILLS,
    "hard skills": ResumeSection.SKILLS,
    "computer skills": ResumeSection.SKILLS,
    "it skills": ResumeSection.SKILLS,
    "competencies": ResumeSection.SKILLS,
    "core skills": ResumeSection.SKILLS,
    "relevant skills": ResumeSection.SKILLS,
    "technologies used": ResumeSection.SKILLS,
    "software skills": ResumeSection.SKILLS,
    "development tools": ResumeSection.SKILLS,

    # -----------------------------------------------------------------------
    # Projects
    # -----------------------------------------------------------------------
    "projects": ResumeSection.PROJECTS,
    "academic projects": ResumeSection.PROJECTS,
    "personal projects": ResumeSection.PROJECTS,
    "key projects": ResumeSection.PROJECTS,
    "major projects": ResumeSection.PROJECTS,
    "minor projects": ResumeSection.PROJECTS,
    "mini projects": ResumeSection.PROJECTS,
    "relevant projects": ResumeSection.PROJECTS,
    "selected projects": ResumeSection.PROJECTS,
    "notable projects": ResumeSection.PROJECTS,
    "capstone project": ResumeSection.PROJECTS,
    "capstone projects": ResumeSection.PROJECTS,
    "project work": ResumeSection.PROJECTS,
    "project experience": ResumeSection.PROJECTS,
    "technical projects": ResumeSection.PROJECTS,
    "engineering projects": ResumeSection.PROJECTS,
    "software projects": ResumeSection.PROJECTS,
    "coursework projects": ResumeSection.PROJECTS,
    "course projects": ResumeSection.PROJECTS,
    "side projects": ResumeSection.PROJECTS,
    "independent projects": ResumeSection.PROJECTS,
    "client projects": ResumeSection.PROJECTS,

    # -----------------------------------------------------------------------
    # Internships
    # -----------------------------------------------------------------------
    "internships": ResumeSection.INTERNSHIPS,
    "internship": ResumeSection.INTERNSHIPS,
    "internship experience": ResumeSection.INTERNSHIPS,
    "internship experiences": ResumeSection.INTERNSHIPS,
    "industrial training": ResumeSection.INTERNSHIPS,
    "summer internship": ResumeSection.INTERNSHIPS,
    "summer internships": ResumeSection.INTERNSHIPS,
    "winter internship": ResumeSection.INTERNSHIPS,
    "apprenticeships": ResumeSection.INTERNSHIPS,
    "apprenticeship": ResumeSection.INTERNSHIPS,
    "practical training": ResumeSection.INTERNSHIPS,
    "internship history": ResumeSection.INTERNSHIPS,
    "trainee experience": ResumeSection.INTERNSHIPS,
    "internship & training": ResumeSection.INTERNSHIPS,
    "internship and training": ResumeSection.INTERNSHIPS,
    "virtual internship": ResumeSection.INTERNSHIPS,
    "virtual internships": ResumeSection.INTERNSHIPS,

    # -----------------------------------------------------------------------
    # Experience
    # -----------------------------------------------------------------------
    "experience": ResumeSection.EXPERIENCE,
    "work experience": ResumeSection.EXPERIENCE,
    "professional experience": ResumeSection.EXPERIENCE,
    "employment history": ResumeSection.EXPERIENCE,
    "career history": ResumeSection.EXPERIENCE,
    "work history": ResumeSection.EXPERIENCE,
    "professional background": ResumeSection.EXPERIENCE,
    "employment": ResumeSection.EXPERIENCE,
    "job experience": ResumeSection.EXPERIENCE,
    "relevant experience": ResumeSection.EXPERIENCE,
    "industry experience": ResumeSection.EXPERIENCE,
    "professional work experience": ResumeSection.EXPERIENCE,
    "past experience": ResumeSection.EXPERIENCE,
    "past employment": ResumeSection.EXPERIENCE,
    "career summary": ResumeSection.EXPERIENCE,

    # -----------------------------------------------------------------------
    # Certifications
    # -----------------------------------------------------------------------
    "certifications": ResumeSection.CERTIFICATIONS,
    "certification": ResumeSection.CERTIFICATIONS,
    "certificates": ResumeSection.CERTIFICATIONS,
    "certificate": ResumeSection.CERTIFICATIONS,
    "licenses": ResumeSection.CERTIFICATIONS,
    "licensures": ResumeSection.CERTIFICATIONS,
    "courses": ResumeSection.CERTIFICATIONS,
    "accreditations": ResumeSection.CERTIFICATIONS,
    "credentials": ResumeSection.CERTIFICATIONS,
    "training & certifications": ResumeSection.CERTIFICATIONS,
    "training and certifications": ResumeSection.CERTIFICATIONS,
    "certifications & licenses": ResumeSection.CERTIFICATIONS,
    "certifications and licenses": ResumeSection.CERTIFICATIONS,
    "certifications & courses": ResumeSection.CERTIFICATIONS,
    "certifications and courses": ResumeSection.CERTIFICATIONS,
    "courses & certifications": ResumeSection.CERTIFICATIONS,
    "courses and certifications": ResumeSection.CERTIFICATIONS,
    "online courses": ResumeSection.CERTIFICATIONS,
    "online certifications": ResumeSection.CERTIFICATIONS,
    "professional certifications": ResumeSection.CERTIFICATIONS,
    "professional courses": ResumeSection.CERTIFICATIONS,
    "certifications & training": ResumeSection.CERTIFICATIONS,
    "certified courses": ResumeSection.CERTIFICATIONS,

    # -----------------------------------------------------------------------
    # Achievements
    # -----------------------------------------------------------------------
    "achievements": ResumeSection.ACHIEVEMENTS,
    "achievement": ResumeSection.ACHIEVEMENTS,
    "awards": ResumeSection.ACHIEVEMENTS,
    "award": ResumeSection.ACHIEVEMENTS,
    "honors": ResumeSection.ACHIEVEMENTS,
    "honor": ResumeSection.ACHIEVEMENTS,
    "accomplishments": ResumeSection.ACHIEVEMENTS,
    "accomplishment": ResumeSection.ACHIEVEMENTS,
    "accolades": ResumeSection.ACHIEVEMENTS,
    "key achievements": ResumeSection.ACHIEVEMENTS,
    "awards & achievements": ResumeSection.ACHIEVEMENTS,
    "awards and achievements": ResumeSection.ACHIEVEMENTS,
    "honors & awards": ResumeSection.ACHIEVEMENTS,
    "honors and awards": ResumeSection.ACHIEVEMENTS,
    "awards & honors": ResumeSection.ACHIEVEMENTS,
    "awards and honors": ResumeSection.ACHIEVEMENTS,
    "recognition": ResumeSection.ACHIEVEMENTS,
    "recognitions": ResumeSection.ACHIEVEMENTS,
    "distinctions": ResumeSection.ACHIEVEMENTS,
    "merits & awards": ResumeSection.ACHIEVEMENTS,
    "academic achievements": ResumeSection.ACHIEVEMENTS,
    "academic honors": ResumeSection.ACHIEVEMENTS,
    "co-curricular achievements": ResumeSection.ACHIEVEMENTS,
    "co curricular achievements": ResumeSection.ACHIEVEMENTS,

    # -----------------------------------------------------------------------
    # Positions of Responsibility
    # -----------------------------------------------------------------------
    "positions of responsibility": ResumeSection.POSITIONS_OF_RESPONSIBILITY,
    "position of responsibility": ResumeSection.POSITIONS_OF_RESPONSIBILITY,
    "leadership": ResumeSection.POSITIONS_OF_RESPONSIBILITY,
    "leadership experience": ResumeSection.POSITIONS_OF_RESPONSIBILITY,
    "extracurricular leadership": ResumeSection.POSITIONS_OF_RESPONSIBILITY,
    "leadership roles": ResumeSection.POSITIONS_OF_RESPONSIBILITY,
    "leadership role": ResumeSection.POSITIONS_OF_RESPONSIBILITY,
    "campus leadership": ResumeSection.POSITIONS_OF_RESPONSIBILITY,
    "responsibilities": ResumeSection.POSITIONS_OF_RESPONSIBILITY,
    "positions held": ResumeSection.POSITIONS_OF_RESPONSIBILITY,
    "responsibilities held": ResumeSection.POSITIONS_OF_RESPONSIBILITY,
    "student leadership": ResumeSection.POSITIONS_OF_RESPONSIBILITY,
    "extra-curricular activities": ResumeSection.POSITIONS_OF_RESPONSIBILITY,
    "extracurricular activities": ResumeSection.POSITIONS_OF_RESPONSIBILITY,
    "extra curricular activities": ResumeSection.POSITIONS_OF_RESPONSIBILITY,
    "extracurriculars": ResumeSection.POSITIONS_OF_RESPONSIBILITY,
    "extracurricular": ResumeSection.POSITIONS_OF_RESPONSIBILITY,
    "volunteering": ResumeSection.POSITIONS_OF_RESPONSIBILITY,
    "volunteer experience": ResumeSection.POSITIONS_OF_RESPONSIBILITY,
    "volunteer work": ResumeSection.POSITIONS_OF_RESPONSIBILITY,
    "activities & leadership": ResumeSection.POSITIONS_OF_RESPONSIBILITY,
    "college activities": ResumeSection.POSITIONS_OF_RESPONSIBILITY,
    "community involvement": ResumeSection.POSITIONS_OF_RESPONSIBILITY,
    "community service": ResumeSection.POSITIONS_OF_RESPONSIBILITY,
    "roles and responsibilities": ResumeSection.POSITIONS_OF_RESPONSIBILITY,
    "roles & responsibilities": ResumeSection.POSITIONS_OF_RESPONSIBILITY,
    "co-curricular activities": ResumeSection.POSITIONS_OF_RESPONSIBILITY,
    "co curricular activities": ResumeSection.POSITIONS_OF_RESPONSIBILITY,
    "clubs & committees": ResumeSection.POSITIONS_OF_RESPONSIBILITY,
    "clubs and committees": ResumeSection.POSITIONS_OF_RESPONSIBILITY,
    "clubs & societies": ResumeSection.POSITIONS_OF_RESPONSIBILITY,
    "clubs and societies": ResumeSection.POSITIONS_OF_RESPONSIBILITY,
    "social initiatives": ResumeSection.POSITIONS_OF_RESPONSIBILITY,

    # -----------------------------------------------------------------------
    # Publications
    # -----------------------------------------------------------------------
    "publications": ResumeSection.PUBLICATIONS,
    "publication": ResumeSection.PUBLICATIONS,
    "research": ResumeSection.PUBLICATIONS,
    "research publications": ResumeSection.PUBLICATIONS,
    "papers": ResumeSection.PUBLICATIONS,
    "research papers": ResumeSection.PUBLICATIONS,
    "selected publications": ResumeSection.PUBLICATIONS,
    "conference proceedings": ResumeSection.PUBLICATIONS,
    "conference publications": ResumeSection.PUBLICATIONS,
    "journals": ResumeSection.PUBLICATIONS,
    "journal publications": ResumeSection.PUBLICATIONS,
    "journal articles": ResumeSection.PUBLICATIONS,
    "patents": ResumeSection.PUBLICATIONS,
    "patents & publications": ResumeSection.PUBLICATIONS,
    "published work": ResumeSection.PUBLICATIONS,
    "published papers": ResumeSection.PUBLICATIONS,
    "academic research": ResumeSection.PUBLICATIONS,
    "research work": ResumeSection.PUBLICATIONS,

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------
    "summary": ResumeSection.SUMMARY,
    "professional summary": ResumeSection.SUMMARY,
    "profile": ResumeSection.SUMMARY,
    "career objective": ResumeSection.SUMMARY,
    "objective": ResumeSection.SUMMARY,
    "executive summary": ResumeSection.SUMMARY,
    "about me": ResumeSection.SUMMARY,
    "personal profile": ResumeSection.SUMMARY,
    "summary statement": ResumeSection.SUMMARY,
    "overview": ResumeSection.SUMMARY,
    "professional profile": ResumeSection.SUMMARY,
    "biography": ResumeSection.SUMMARY,
    "brief profile": ResumeSection.SUMMARY,
    "statement of purpose": ResumeSection.SUMMARY,
    "personal statement": ResumeSection.SUMMARY,
    "profile summary": ResumeSection.SUMMARY,

    # -----------------------------------------------------------------------
    # Contact
    # -----------------------------------------------------------------------
    "contact": ResumeSection.CONTACT,
    "contact information": ResumeSection.CONTACT,
    "contact info": ResumeSection.CONTACT,
    "contact details": ResumeSection.CONTACT,
    "personal info": ResumeSection.CONTACT,
    "personal information": ResumeSection.CONTACT,
    "personal details": ResumeSection.CONTACT,

    # -----------------------------------------------------------------------
    # Other / Miscellaneous
    # -----------------------------------------------------------------------
    "other": ResumeSection.OTHER,
    "additional information": ResumeSection.OTHER,
    "miscellaneous": ResumeSection.OTHER,
    "interests": ResumeSection.OTHER,
    "hobbies": ResumeSection.OTHER,
    "languages": ResumeSection.OTHER,
    "languages known": ResumeSection.OTHER,
    "hobbies & interests": ResumeSection.OTHER,
    "hobbies and interests": ResumeSection.OTHER,
    "personal interests": ResumeSection.OTHER,
    "affiliations": ResumeSection.OTHER,
    "references": ResumeSection.OTHER,
}


# ---------------------------------------------------------------------------
# Header Normalization & Matching Engine
# ---------------------------------------------------------------------------

def normalize_header_text(line: str) -> str:
    """
    Clean and normalize a potential resume header line before dictionary matching.

    Transformation Pipeline:
        1. Strip outer whitespace.
        2. Strip markdown headers (#, ##, ###) and emphasis (*, _, ~, `).
        3. Strip leading bullets, numbered list markers (e.g. '1.', '1)', 'I.', 'A.').
        4. Strip surrounding decorator lines and brackets (===, ---, ___, ***, <<<, >>>, [...]).
        5. Strip trailing punctuation (: - – — | / .).
        6. Collapse multiple inline whitespace and convert to lowercase.

    Args:
        line: Raw line string from document.

    Returns:
        Cleaned, normalized lowercase string.
    """
    if not line:
        return ""

    text = line.strip()

    # 1. Remove Markdown headers (e.g. '### Header')
    text = re.sub(r"^#+\s*", "", text)

    # 2. Remove markdown bold/italics wrappers (e.g. '**Header**' or '__Header__')
    text = re.sub(r"^[\*_~`]+", "", text)
    text = re.sub(r"[\*_~`]+$", "", text)

    # 3. Remove leading bullet symbols (e.g. '•', '●', '▪', '■', '-', '*', '–', '—')
    text = re.sub(r"^[\u2022\u2023\u25cf\u25aa\u25fe\u25b6\u27a4\u2714\*\-\–\—\>\+\·]+\s*", "", text)

    # 4. Remove leading numbering/alphabetic index (e.g. '1.', '1)', '(1)', 'I.', 'A.')
    text = re.sub(r"^\(?([0-9]{1,2}|[ivxIVX]{1,4}|[a-zA-Z])[\.\)\:\-]\s*", "", text)

    # 5. Remove surrounding decorators (e.g. '=== Header ===', '--- Header ---', '___ Header ___', '*** Header ***')
    text = re.sub(r"^[\=\-\_\*\~\|\<\>\[\{]{2,}\s*", "", text)
    text = re.sub(r"\s*[\=\-\_\*\~\|\<\>\]\}]{2,}$", "", text)

    # 6. Remove remaining outer bracket/brace pairs if wrapping entire text
    if (text.startswith("[") and text.endswith("]")) or (text.startswith("(") and text.endswith(")")):
        text = text[1:-1].strip()

    # 7. Remove trailing separator characters (':', '-', '–', '—', '|', '/', '.')
    text = re.sub(r"[\:\-\–\—\|\/\.\,\;]+$", "", text).strip()

    # 8. Collapse whitespace and lowercase
    text = re.sub(r"\s+", " ", text).strip().lower()

    return text


def match_section_header(line: str) -> Optional[ResumeSection]:
    """
    Evaluate whether a candidate line represents a section header.

    Heuristics:
        - Must satisfy character length constraint (<= MAX_HEADER_CHARS).
        - Must satisfy word count constraint (<= MAX_HEADER_WORDS).
        - Must not be a narrative sentence (e.g. containing action verbs or conversational text).
        - Normalized text must match a recognized entry in SECTION_HEADER_MAP.

    Args:
        line: Raw line string from document.

    Returns:
        Mapped ResumeSection enum if recognized, otherwise None.
    """
    if not line:
        return None

    raw_stripped = line.strip()

    # Fast rejection for empty lines, overlong lines, or high word counts
    if not raw_stripped or len(raw_stripped) > MAX_HEADER_CHARS:
        return None

    words = raw_stripped.split()
    if len(words) > MAX_HEADER_WORDS:
        return None

    # Sentence heuristic: headers do not start with conversational pronouns or narrative phrases
    lower_raw = raw_stripped.lower()
    if any(lower_raw.startswith(prefix) for prefix in (
        "i have", "i am", "worked as", "responsible for", "developed", "implemented", "managed",
        "experienced in", "looking for", "my goal", "proficient in"
    )):
        return None

    normalized = normalize_header_text(raw_stripped)
    if not normalized:
        return None

    return SECTION_HEADER_MAP.get(normalized)

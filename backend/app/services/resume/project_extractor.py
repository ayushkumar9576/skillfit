"""
app/services/resume/project_extractor.py
-----------------------------------------
Rule-based project extraction for SkillFit Phase 3.7 (Project Analysis Engine).

This turns raw resume text into a list of discrete :class:`ProjectEvidence`
artifacts — the *extraction* half of Phase 3.7, which then feeds one LLM
analysis call per project inside :class:`ProjectAnalysisEngine`.

Why it runs on RAW text (not the section-detector output):
    :class:`~app.services.resume.section_detector.RuleBasedSectionDetector`
    deliberately drops blank lines (``if not stripped: continue``). Blank lines
    are exactly the boundaries that separate one project from the next, so this
    extractor must operate on the ORIGINAL ``extracted_text`` to keep them.

Strategy + Factory (mirrors ``section_detector``):
    BaseProjectExtractor (ABC)
        └── RuleBasedProjectExtractor   (deterministic, pure stdlib)
        └── LLMProjectExtractor         (stub — future work)
    get_project_extractor(type="rule_based") -> BaseProjectExtractor
    extract_projects_from_text(raw_text, extractor_type="rule_based")

Design principles:
    - Pure standard library. Imports the pure-dataclass domain models but no
      framework code and no LLM code (extraction never makes a network call).
    - Best-effort structuring: the structured fields (title / technologies /
      highlights / role / url) are *hints*. Every meaningful line is also kept
      verbatim in ``evidences`` (with line numbers), so the downstream LLM
      always receives the full, traceable raw context even when a heuristic
      mis-parses a field.
"""

import logging
import re
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from app.analysis.models.base import AnalysisEvidence
from app.analysis.models.project_models import ProjectAnalysisResult, ProjectEvidence
from app.services.resume.section_detector import DIVIDER_LINE_PATTERN
from app.services.resume.section_headers import match_section_header
from app.services.resume.section_types import ResumeSection

logger = logging.getLogger(__name__)

#: Canonical section label stamped on every extracted evidence snippet.
SECTION_SOURCE: str = "projects"

# Leading bullet markers (ASCII + common unicode). Requires trailing whitespace
# so mid-word hyphens ("AI-Powered", "E-Commerce") are never treated as bullets.
_BULLET_CHARS = r"•‣◦▪◾▸▶➤✔∙·⁃\*\-–—\+>"
_BULLET_PATTERN = re.compile(rf"^[{_BULLET_CHARS}]+\s+")

# Leading list numbering: "1. ", "1) ", "(1) ".
_NUMBERING_PATTERN = re.compile(r"^\(?\d{1,2}[\.\)\:]\s+")

# "Technologies: a, b, c" / "Tech Stack - a | b" style label lines.
_TECH_LABEL_PATTERN = re.compile(
    r"^\s*(technologies used|technologies|tech stack|tech used|tech|stack|"
    r"tools used|tools & technologies|tools and technologies|tools|"
    r"built with|built using|frameworks|libraries|languages)\s*[:\-–—]\s*(.+)$",
    re.IGNORECASE,
)

# "Role: Backend Lead" style label lines.
_ROLE_LABEL_PATTERN = re.compile(
    r"^\s*(my role|role|responsibility|responsibilities|position|contribution)\s*"
    r"[:\-–—]\s*(.+)$",
    re.IGNORECASE,
)

# URLs / repository links.
_URL_PATTERN = re.compile(
    r"(https?://[^\s)>\]]+|(?:www\.|github\.com/|gitlab\.com/|bitbucket\.org/)[^\s)>\]]+)",
    re.IGNORECASE,
)

# Technology-list separators.
_TECH_SPLIT_PATTERN = re.compile(r"[,\|/;•]+")

# Month tokens used to recognize (and discard) date ranges masquerading as tech.
_MONTH_TOKENS = (
    "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec",
    "january", "february", "march", "april", "june", "july", "august", "september",
    "october", "november", "december", "present", "current", "ongoing", "till date",
)

# A candidate title starting with one of these verbs is an accomplishment line,
# not a project title (titles are noun phrases). Prevents false title-splits.
_ACTION_VERB_PREFIXES = frozenset({
    "built", "developed", "designed", "created", "implemented", "achieved", "led",
    "managed", "integrated", "deployed", "used", "worked", "engineered", "architected",
    "optimized", "improved", "reduced", "increased", "wrote", "added", "collaborated",
    "responsible", "spearheaded", "handled", "delivered", "maintained", "trained",
    "analyzed", "researched", "conducted", "performed", "utilized", "leveraged",
})


class BaseProjectExtractor(ABC):
    """Abstract interface for turning raw resume text into project evidence."""

    @abstractmethod
    def extract(self, raw_text: str) -> ProjectAnalysisResult:
        """
        Parse raw resume text into discrete project evidence.

        Args:
            raw_text: The ORIGINAL extracted resume text (blanks preserved).

        Returns:
            A :class:`ProjectAnalysisResult` whose ``projects`` holds the
            extracted evidence and ``reports`` is left empty (the engine fills
            it later). Empty result when no projects section is present.
        """
        raise NotImplementedError


class RuleBasedProjectExtractor(BaseProjectExtractor):
    """
    Deterministic, dependency-free project extractor.

    Pipeline:
        1. Locate the projects block in raw text via ``match_section_header``
           (keeping blank lines), ending at the next *different* section header.
        2. Segment the block into entries: primary boundary = blank line /
           visual divider; secondary refinement = a conservative "title-line"
           heuristic that splits back-to-back projects lacking blank separators.
        3. Parse each segment into a :class:`ProjectEvidence`.
    """

    def extract(self, raw_text: str) -> ProjectAnalysisResult:
        if not raw_text or not isinstance(raw_text, str) or not raw_text.strip():
            logger.debug("Project extraction invoked with empty or invalid text.")
            return ProjectAnalysisResult()

        lines = raw_text.split("\n")
        block = self._locate_projects_block(lines)
        if not block:
            logger.debug("No projects section located in resume text.")
            return ProjectAnalysisResult()

        segments = self._segment(block)
        projects: List[ProjectEvidence] = []
        for segment in segments:
            project = self._build_project(segment)
            if project is not None:
                projects.append(project)

        logger.info("Project extraction completed: %d project(s) identified.", len(projects))
        return ProjectAnalysisResult(projects=projects, total_projects_count=len(projects))

    # -- block location -----------------------------------------------------

    def _locate_projects_block(self, lines: List[str]) -> List[Tuple[int, str]]:
        """
        Return the projects block as ``[(line_number, raw_line), ...]`` with
        interior blank lines preserved and header lines dropped. Line numbers
        are 1-based (for evidence traceability).
        """
        start: Optional[int] = None
        for idx, line in enumerate(lines):
            if match_section_header(line) == ResumeSection.PROJECTS:
                start = idx + 1
                break
        if start is None:
            return []

        block: List[Tuple[int, str]] = []
        for idx in range(start, len(lines)):
            line = lines[idx]
            matched = match_section_header(line)
            if matched is not None:
                if matched == ResumeSection.PROJECTS:
                    # A second projects sub-header ("Personal Projects" etc.):
                    # merge its content, but drop the header line itself.
                    continue
                # Any other recognized section header ends the projects block.
                break
            block.append((idx + 1, line))

        return self._trim_blank_edges(block)

    @staticmethod
    def _trim_blank_edges(block: List[Tuple[int, str]]) -> List[Tuple[int, str]]:
        """Drop leading/trailing blank or divider lines; keep interior blanks."""
        def is_edge_noise(text: str) -> bool:
            s = text.strip()
            return (not s) or bool(DIVIDER_LINE_PATTERN.match(s))

        lo, hi = 0, len(block)
        while lo < hi and is_edge_noise(block[lo][1]):
            lo += 1
        while hi > lo and is_edge_noise(block[hi - 1][1]):
            hi -= 1
        return block[lo:hi]

    # -- segmentation -------------------------------------------------------

    def _segment(self, block: List[Tuple[int, str]]) -> List[List[Tuple[int, str]]]:
        """Split the block into per-project segments."""
        groups: List[List[Tuple[int, str]]] = []
        current: List[Tuple[int, str]] = []
        for lineno, text in block:
            stripped = text.strip()
            is_separator = (not stripped) or bool(DIVIDER_LINE_PATTERN.match(stripped))
            if is_separator:
                if current:
                    groups.append(current)
                    current = []
                continue
            current.append((lineno, text))
        if current:
            groups.append(current)

        refined: List[List[Tuple[int, str]]] = []
        for group in groups:
            refined.extend(self._split_by_titles(group))
        return refined

    def _split_by_titles(
        self, group: List[Tuple[int, str]]
    ) -> List[List[Tuple[int, str]]]:
        """
        Within one blank-delimited group, split back-to-back projects that lack
        a blank separator by detecting subsequent "title" lines. Conservative:
        only splits once real content (a bullet / label / description line) has
        been seen since the previous title.
        """
        if not group:
            return []

        subs: List[List[Tuple[int, str]]] = []
        current: List[Tuple[int, str]] = [group[0]]
        seen_content = False

        for lineno, text in group[1:]:
            if self._is_bullet(text) or self._is_label(text):
                seen_content = True
                current.append((lineno, text))
                continue
            if seen_content and self._looks_like_title(text):
                subs.append(current)
                current = [(lineno, text)]
                seen_content = False
                continue
            if text.strip():
                seen_content = True
            current.append((lineno, text))

        subs.append(current)
        return subs

    # -- line classification helpers ---------------------------------------

    @staticmethod
    def _is_bullet(text: str) -> bool:
        return bool(_BULLET_PATTERN.match(text.lstrip()))

    @staticmethod
    def _strip_bullet(text: str) -> str:
        return _BULLET_PATTERN.sub("", text.lstrip()).strip()

    @staticmethod
    def _is_label(text: str) -> bool:
        s = text.strip()
        return bool(_TECH_LABEL_PATTERN.match(s) or _ROLE_LABEL_PATTERN.match(s))

    def _looks_like_title(self, text: str) -> bool:
        """Conservative title-line detector for secondary segmentation."""
        s = text.strip()
        if not s or len(s) > 90:
            return False
        if self._is_bullet(text) or self._is_label(text):
            return False

        core = self._strip_decorations(s)
        if not core:
            return False

        # Strong structural signals.
        if (s.startswith("**") and s.endswith("**")) or (s.startswith("__") and s.endswith("__")):
            return True
        if " | " in s:
            return True
        if re.search(r"\s[–—\-]\s", s) and re.search(r"(19|20)\d{2}", s):
            return True

        # Title-case / caps heuristic on a short noun phrase.
        first_word = re.sub(r"[^a-zA-Z]", "", core.split()[0]).lower() if core.split() else ""
        if first_word in _ACTION_VERB_PREFIXES:
            return False
        if core.endswith((".", "!", "?")):
            return False
        words = re.findall(r"[A-Za-z][A-Za-z0-9+#.&/]*", core)
        if not words or len(words) > 8:
            return False
        capitalized = sum(1 for w in words if w[0].isupper())
        return (capitalized / len(words)) >= 0.6

    @staticmethod
    def _strip_decorations(line: str) -> str:
        """Strip markdown / bullets / numbering / wrappers, KEEPING case."""
        text = line.strip()
        text = re.sub(r"^#+\s*", "", text)
        text = re.sub(r"^[\*_~`]+", "", text)
        text = re.sub(r"[\*_~`]+$", "", text)
        text = _BULLET_PATTERN.sub("", text)
        text = _NUMBERING_PATTERN.sub("", text)
        return text.strip()

    # -- per-project parsing ------------------------------------------------

    def _build_project(self, segment: List[Tuple[int, str]]) -> Optional[ProjectEvidence]:
        """Turn one segment into a :class:`ProjectEvidence` (or ``None``)."""
        if not segment:
            return None

        # Title = first non-bullet, non-label line; else the first line.
        title_idx = 0
        for i, (_lineno, text) in enumerate(segment):
            if text.strip() and not self._is_bullet(text) and not self._is_label(text):
                title_idx = i
                break

        title_lineno, title_raw = segment[title_idx]
        title_text, inline_tech = self._parse_title(title_raw)
        if not title_text:
            return None

        technologies: List[str] = list(inline_tech)
        highlights: List[str] = []
        description_parts: List[str] = []
        role: Optional[str] = None
        project_url: Optional[str] = None
        evidences: List[AnalysisEvidence] = [
            AnalysisEvidence(
                evidence_text=title_text,
                source_section=SECTION_SOURCE,
                confidence=1.0,
                context_snippet=title_raw.strip(),
                line_number=title_lineno,
            )
        ]

        for i, (lineno, text) in enumerate(segment):
            if i == title_idx:
                continue
            stripped = text.strip()
            if not stripped:
                continue

            # URL (from any line).
            url_match = _URL_PATTERN.search(stripped)
            if url_match and project_url is None:
                project_url = self._clean_url(url_match.group(0))
                remainder = stripped.replace(url_match.group(0), "").strip(" :|-–—")
                if len(remainder) <= 6:  # URL-only-ish line (maybe a "GitHub:" label)
                    evidences.append(self._evidence(stripped, lineno))
                    continue

            # "Technologies: ..." label line.
            tech_match = _TECH_LABEL_PATTERN.match(stripped)
            if tech_match:
                technologies.extend(self._split_tech(tech_match.group(2)))
                evidences.append(self._evidence(stripped, lineno))
                continue

            # "Role: ..." label line.
            role_match = _ROLE_LABEL_PATTERN.match(stripped)
            if role_match:
                role = role_match.group(2).strip()
                evidences.append(self._evidence(stripped, lineno))
                continue

            # Bullet -> highlight.
            if self._is_bullet(text):
                highlight = self._strip_bullet(text)
                if highlight:
                    highlights.append(highlight)
                    evidences.append(self._evidence(highlight, lineno, context=stripped))
                continue

            # "| a, b, c" inline tech line.
            if stripped.startswith("|"):
                techs = self._split_tech(stripped.lstrip("|"))
                if techs:
                    technologies.extend(techs)
                    evidences.append(self._evidence(stripped, lineno))
                    continue

            # Otherwise prose description.
            description_parts.append(stripped)
            evidences.append(self._evidence(stripped, lineno))

        technologies = self._dedupe(technologies)
        description = " ".join(description_parts).strip()
        confidence = self._confidence(highlights, technologies, description, role, project_url)

        return ProjectEvidence(
            title=title_text,
            description=description,
            role=role,
            technologies=technologies,
            project_url=project_url,
            highlights=highlights,
            confidence=confidence,
            evidences=evidences,
        )

    @staticmethod
    def _evidence(text: str, lineno: int, context: Optional[str] = None) -> AnalysisEvidence:
        return AnalysisEvidence(
            evidence_text=text,
            source_section=SECTION_SOURCE,
            confidence=1.0,
            context_snippet=context if context is not None else text,
            line_number=lineno,
        )

    def _parse_title(self, title_raw: str) -> Tuple[str, List[str]]:
        """
        Return ``(title, inline_tech)``. Handles the common
        ``Project Name | React, Node | Jan 2024`` one-line format by taking the
        first pipe segment as the title and mining the rest for technologies.
        """
        core = self._strip_decorations(title_raw)
        inline_tech: List[str] = []
        if " | " in core:
            parts = [p.strip() for p in core.split(" | ") if p.strip()]
            if parts:
                title = parts[0]
                for part in parts[1:]:
                    if self._is_date_range(part):
                        continue
                    inline_tech.extend(self._split_tech(part))
                return title, inline_tech
        return core, inline_tech

    def _split_tech(self, value: str) -> List[str]:
        techs: List[str] = []
        for part in _TECH_SPLIT_PATTERN.split(value):
            token = part.strip().strip(".").strip()
            if not token:
                continue
            if self._is_date_range(token) or re.fullmatch(r"(19|20)\d{2}", token):
                continue
            if len(token) > 40:  # too long to be a tech token; likely prose
                continue
            techs.append(token)
        return techs

    @staticmethod
    def _is_date_range(value: str) -> bool:
        low = value.lower().strip()
        if not low:
            return False
        if any(low == m or low.startswith(m + " ") for m in _MONTH_TOKENS):
            return True
        # Contains a year and little other alphabetic content (e.g. "2021-2022").
        if re.search(r"(19|20)\d{2}", low):
            residue = re.sub(r"[0-9\s\-–—/.]", "", low)
            if len(residue) <= 2:
                return True
        return False

    @staticmethod
    def _clean_url(url: str) -> str:
        return url.rstrip(").,;]>'\"")

    @staticmethod
    def _dedupe(items: List[str]) -> List[str]:
        seen = set()
        result: List[str] = []
        for item in items:
            key = item.lower()
            if key not in seen:
                seen.add(key)
                result.append(item)
        return result

    @staticmethod
    def _confidence(
        highlights: List[str],
        technologies: List[str],
        description: str,
        role: Optional[str],
        project_url: Optional[str],
    ) -> float:
        score = 0.4
        if highlights or description:
            score += 0.3
        if technologies:
            score += 0.2
        if project_url or role:
            score += 0.1
        return round(min(score, 1.0), 2)


class LLMProjectExtractor(BaseProjectExtractor):
    """Extensibility stub — an LLM-assisted extractor is not part of Phase 3.7."""

    def extract(self, raw_text: str) -> ProjectAnalysisResult:
        raise NotImplementedError(
            "LLM-based project extraction is not implemented; Phase 3.7 uses "
            "rule-based extraction plus one LLM *analysis* call per project."
        )


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def get_project_extractor(extractor_type: str = "rule_based") -> BaseProjectExtractor:
    """
    Factory returning a project extractor instance.

    Args:
        extractor_type: 'rule_based' (default) or 'llm'.

    Raises:
        ValueError: on an unknown extractor type.
    """
    normalized = (extractor_type or "rule_based").lower().strip()
    if normalized in ("rule_based", "rule", "deterministic"):
        return RuleBasedProjectExtractor()
    if normalized == "llm":
        return LLMProjectExtractor()
    raise ValueError(
        f"Unsupported project extractor type '{extractor_type}'. "
        f"Available types: 'rule_based', 'llm'."
    )


def extract_projects_from_text(
    raw_text: str, extractor_type: str = "rule_based"
) -> ProjectAnalysisResult:
    """Convenience wrapper: extract projects from raw text in one call."""
    return get_project_extractor(extractor_type).extract(raw_text)

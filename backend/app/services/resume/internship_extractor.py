"""
app/services/resume/internship_extractor.py
-------------------------------------------
Rule-based internship extraction for SkillFit Phase 3.8.

This turns raw resume text into a list of discrete :class:`InternshipEvidence`
artifacts, which then feeds one LLM analysis call per internship inside 
:class:`InternshipAnalysisEngine`.

Design principles:
    - Pure standard library.
    - Operates directly on the RAW extracted text to preserve blank lines.
    - Dumb extraction: absolutely NO intelligence or competency inference here.
    - Mandatory evidence tracking: every parsed text snippet is preserved verbatim
      with line numbers.
"""

import logging
import re
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from app.analysis.models.base import AnalysisEvidence
from app.analysis.models.internship_models import InternshipAnalysisResult, InternshipEvidence
from app.services.resume.section_detector import DIVIDER_LINE_PATTERN
from app.services.resume.section_headers import match_section_header
from app.services.resume.section_types import ResumeSection

logger = logging.getLogger(__name__)

SECTION_SOURCE: str = "internships"

_BULLET_CHARS = r"•‣◦▪◾▸▶➤✔∙·⁃\*\-–—\+>"
_BULLET_PATTERN = re.compile(rf"^[{_BULLET_CHARS}]+\s+")
_NUMBERING_PATTERN = re.compile(r"^\(?\d{1,2}[\.\)\:]\s+")

_TECH_LABEL_PATTERN = re.compile(
    r"^\s*(technologies used|technologies|tech stack|tech used|tech|stack|"
    r"tools used|tools & technologies|tools and technologies|tools|"
    r"built with|built using|frameworks|libraries|languages)\s*[:\-–—]\s*(.+)$",
    re.IGNORECASE,
)

_ROLE_LABEL_PATTERN = re.compile(
    r"^\s*(my role|role|responsibility|responsibilities|position|contribution|title)\s*"
    r"[:\-–—]\s*(.+)$",
    re.IGNORECASE,
)

_TECH_SPLIT_PATTERN = re.compile(r"[,\|/;•]+")

_MONTH_TOKENS = (
    "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec",
    "january", "february", "march", "april", "june", "july", "august", "september",
    "october", "november", "december", "present", "current", "ongoing", "till date",
)


class BaseInternshipExtractor(ABC):
    """Abstract interface for turning raw resume text into internship evidence."""

    @abstractmethod
    def extract(self, raw_text: str) -> InternshipAnalysisResult:
        raise NotImplementedError


class RuleBasedInternshipExtractor(BaseInternshipExtractor):
    """
    Deterministic internship extractor mirroring the project extractor.
    """

    def extract(self, raw_text: str) -> InternshipAnalysisResult:
        if not raw_text or not isinstance(raw_text, str) or not raw_text.strip():
            logger.debug("Internship extraction invoked with empty or invalid text.")
            return InternshipAnalysisResult()

        lines = raw_text.split("\n")
        block = self._locate_internships_block(lines)
        if not block:
            logger.debug("No internships or experience section located in resume text.")
            return InternshipAnalysisResult()

        segments = self._segment(block)
        internships: List[InternshipEvidence] = []
        for segment in segments:
            internship = self._build_internship(segment)
            if internship is not None:
                internships.append(internship)

        logger.info("Internship extraction completed: %d internship(s) identified.", len(internships))
        return InternshipAnalysisResult(internships=internships, total_internships_count=len(internships))

    def _locate_internships_block(self, lines: List[str]) -> List[Tuple[int, str]]:
        """
        Locate the internships/experience block. Uses EXPERIENCE as a fallback if INTERNSHIPS isn't found.
        """
        start: Optional[int] = None
        target_section = None
        for idx, line in enumerate(lines):
            matched = match_section_header(line)
            if matched in (ResumeSection.INTERNSHIPS, ResumeSection.EXPERIENCE):
                start = idx + 1
                target_section = matched
                break
                
        if start is None:
            return []

        block: List[Tuple[int, str]] = []
        for idx in range(start, len(lines)):
            line = lines[idx]
            matched = match_section_header(line)
            if matched is not None:
                if matched == target_section or matched in (ResumeSection.INTERNSHIPS, ResumeSection.EXPERIENCE):
                    continue
                break
            block.append((idx + 1, line))

        return self._trim_blank_edges(block)

    @staticmethod
    def _trim_blank_edges(block: List[Tuple[int, str]]) -> List[Tuple[int, str]]:
        def is_edge_noise(text: str) -> bool:
            s = text.strip()
            return (not s) or bool(DIVIDER_LINE_PATTERN.match(s))

        lo, hi = 0, len(block)
        while lo < hi and is_edge_noise(block[lo][1]):
            lo += 1
        while hi > lo and is_edge_noise(block[hi - 1][1]):
            hi -= 1
        return block[lo:hi]

    def _segment(self, block: List[Tuple[int, str]]) -> List[List[Tuple[int, str]]]:
        """Split block into per-internship segments by blank lines."""
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

        # We skip the complex title-splitting secondary segmentation for internships to keep it simple,
        # unless it becomes strictly necessary. Blank lines should separate distinct experiences.
        return groups

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

    @staticmethod
    def _strip_decorations(line: str) -> str:
        text = line.strip()
        text = re.sub(r"^#+\s*", "", text)
        text = re.sub(r"^[\*_~`]+", "", text)
        text = re.sub(r"[\*_~`]+$", "", text)
        text = _BULLET_PATTERN.sub("", text)
        text = _NUMBERING_PATTERN.sub("", text)
        return text.strip()

    def _build_internship(self, segment: List[Tuple[int, str]]) -> Optional[InternshipEvidence]:
        """Parse segment into an InternshipEvidence."""
        if not segment:
            return None

        # Title line contains company & potentially role
        title_lineno, title_raw = segment[0]
        organization, inline_role, duration, location = self._parse_title(title_raw)
        
        if not organization:
            return None

        role: str = inline_role or ""
        technologies: List[str] = []
        achievements: List[str] = []
        description_parts: List[str] = []
        evidences: List[AnalysisEvidence] = [
            AnalysisEvidence(
                evidence_text=organization,
                source_section=SECTION_SOURCE,
                confidence=1.0,
                context_snippet=title_raw.strip(),
                line_number=title_lineno,
            )
        ]

        # Scan remaining lines
        for lineno, text in segment[1:]:
            stripped = text.strip()
            if not stripped:
                continue

            tech_match = _TECH_LABEL_PATTERN.match(stripped)
            if tech_match:
                technologies.extend(self._split_tech(tech_match.group(2)))
                evidences.append(self._evidence(stripped, lineno))
                continue

            role_match = _ROLE_LABEL_PATTERN.match(stripped)
            if role_match:
                role = role_match.group(2).strip()
                evidences.append(self._evidence(stripped, lineno))
                continue

            if self._is_bullet(text):
                achievement = self._strip_bullet(text)
                if achievement:
                    achievements.append(achievement)
                    evidences.append(self._evidence(achievement, lineno, context=stripped))
                continue

            # Check if this line is purely a date/location line (often the second line)
            if not duration and self._is_date_range(stripped):
                duration = stripped
                evidences.append(self._evidence(stripped, lineno))
                continue
                
            if stripped.startswith("|"):
                techs = self._split_tech(stripped.lstrip("|"))
                if techs:
                    technologies.extend(techs)
                    evidences.append(self._evidence(stripped, lineno))
                    continue

            description_parts.append(stripped)
            evidences.append(self._evidence(stripped, lineno))

        technologies = self._dedupe(technologies)
        description = " ".join(description_parts).strip()
        
        # If role is still empty, maybe use organization or fallback
        if not role:
            role = "Intern"

        return InternshipEvidence(
            organization=organization,
            role=role,
            duration=duration,
            location=location,
            description=description,
            technologies_used=technologies,
            achievements=achievements,
            confidence=1.0,  # Constant confidence for rule-based matching
            evidences=evidences,
        )

    def _parse_title(self, title_raw: str) -> Tuple[str, Optional[str], Optional[str], Optional[str]]:
        """
        Parses common internship header lines:
        "Company Name | Role | Date | Location"
        Returns (organization, role, duration, location).
        """
        core = self._strip_decorations(title_raw)
        if " | " in core or " - " in core:
            sep = " | " if " | " in core else " - "
            parts = [p.strip() for p in core.split(sep) if p.strip()]
            organization = parts[0]
            role, duration, location = None, None, None
            for part in parts[1:]:
                if self._is_date_range(part):
                    duration = part
                elif len(part) < 30 and ("," in part or part.lower() in ("remote", "wfh")):
                    location = part
                elif not role:
                    role = part
            return organization, role, duration, location
        
        return core, None, None, None

    def _split_tech(self, value: str) -> List[str]:
        techs: List[str] = []
        for part in _TECH_SPLIT_PATTERN.split(value):
            token = part.strip().strip(".").strip()
            if not token:
                continue
            if self._is_date_range(token) or re.fullmatch(r"(19|20)\d{2}", token):
                continue
            if len(token) > 40:
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
        if re.search(r"(19|20)\d{2}", low):
            residue = re.sub(r"[0-9\s\-–—/.]", "", low)
            if len(residue) <= 2 or "present" in low or "current" in low:
                return True
        return False

    @staticmethod
    def _evidence(text: str, lineno: int, context: Optional[str] = None) -> AnalysisEvidence:
        return AnalysisEvidence(
            evidence_text=text,
            source_section=SECTION_SOURCE,
            confidence=1.0,
            context_snippet=context if context is not None else text,
            line_number=lineno,
        )

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


class LLMInternshipExtractor(BaseInternshipExtractor):
    def extract(self, raw_text: str) -> InternshipAnalysisResult:
        raise NotImplementedError("LLM-based internship extraction is not implemented in Phase 3.8.")


def get_internship_extractor(extractor_type: str = "rule_based") -> BaseInternshipExtractor:
    normalized = (extractor_type or "rule_based").lower().strip()
    if normalized in ("rule_based", "rule", "deterministic"):
        return RuleBasedInternshipExtractor()
    if normalized == "llm":
        return LLMInternshipExtractor()
    raise ValueError(
        f"Unsupported internship extractor type '{extractor_type}'. "
        f"Available types: 'rule_based', 'llm'."
    )

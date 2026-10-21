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
from app.services.resume.section_headers import match_section_header, normalize_header_text
from app.services.resume.section_types import ResumeSection

logger = logging.getLogger(__name__)

SECTION_SOURCE: str = "internships"

_BULLET_CHARS = r"•‣◦▪◾▸▶➤✔∙·⁃\*\-–—\+>\ufffd"
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

MONTHS_REGEX_PART = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
DATE_PART_REGEX = rf"(?:{MONTHS_REGEX_PART}[\s\'’\`\ufffd]*(?:\d{{2,4}})?|(?:\d{{1,2}}[/-])?(?:19|20)\d{{2}})"
DATE_SEP_REGEX = r"[\s\-–—to\ufffd/]+"
END_PART_REGEX = rf"(?:{MONTHS_REGEX_PART}[\s\'’\`\ufffd]*(?:\d{{2,4}})?|(?:\d{{1,2}}[/-])?(?:19|20)\d{{2}}|Present|Current|Ongoing|Till\s*Date)"

_DATE_RANGE_REGEX = re.compile(
    rf"(?:(?:Since|From)\s+)?\b{DATE_PART_REGEX}\s*{DATE_SEP_REGEX}\s*{END_PART_REGEX}",
    re.IGNORECASE,
)
_SINGLE_DATE_REGEX = re.compile(
    rf"\b(?:(?:Since|From)\s+)?(?:{MONTHS_REGEX_PART}[\s\'’\`\ufffd]*(?:19|20)?\d{{2}}|(?:19|20)\d{{2}})\b",
    re.IGNORECASE,
)

_ROLE_INDICATORS = frozenset({
    "intern", "internship", "developer", "engineer", "analyst", "trainee",
    "associate", "consultant", "lead", "specialist", "assistant", "researcher",
    "fellow", "programmer", "administrator", "officer", "coordinator", "manager",
    "architect", "designer", "apprentice", "apprenticeship",
})

_ACTION_VERBS = frozenset({
    "built", "developed", "designed", "created", "implemented", "achieved", "led",
    "managed", "integrated", "deployed", "used", "worked", "engineered", "architected",
    "optimized", "improved", "reduced", "increased", "wrote", "added", "collaborated",
    "responsible", "spearheaded", "handled", "delivered", "maintained", "trained",
    "analyzed", "researched", "conducted", "performed", "utilized", "leveraged",
    "automated", "contributed", "promoted", "engaged", "coordinated",
})


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
        blocks = self._locate_internships_blocks(lines)
        if not blocks:
            logger.debug("No internships or experience section located in resume text.")
            return InternshipAnalysisResult()

        internships: List[InternshipEvidence] = []
        for block in blocks:
            segments = self._segment(block)
            for segment in segments:
                internship = self._build_internship(segment)
                if internship is not None:
                    internships.append(internship)

        logger.info("Internship extraction completed: %d internship(s) identified.", len(internships))
        return InternshipAnalysisResult(internships=internships, total_internships_count=len(internships))

    def _locate_internships_blocks(self, lines: List[str]) -> List[List[Tuple[int, str]]]:
        """
        Locate all blocks under INTERNSHIPS, EXPERIENCE, or TRAINING sections.
        Supports multiple distinct sections throughout the document.
        """
        blocks: List[List[Tuple[int, str]]] = []
        current_block: List[Tuple[int, str]] = []
        in_target_section = False

        for idx, line in enumerate(lines):
            matched = match_section_header(line)
            norm = normalize_header_text(line)
            is_target_section = (
                matched in (ResumeSection.INTERNSHIPS, ResumeSection.EXPERIENCE)
                or norm in ("training", "trainings", "training program", "training programs")
            )
            if is_target_section:
                if current_block:
                    trimmed = self._trim_blank_edges(current_block)
                    if trimmed:
                        blocks.append(trimmed)
                    current_block = []
                in_target_section = True
                continue
            elif matched is not None:
                if current_block:
                    trimmed = self._trim_blank_edges(current_block)
                    if trimmed:
                        blocks.append(trimmed)
                    current_block = []
                in_target_section = False
                continue

            if in_target_section:
                current_block.append((idx + 1, line))

        if current_block:
            trimmed = self._trim_blank_edges(current_block)
            if trimmed:
                blocks.append(trimmed)

        return blocks

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

        refined: List[List[Tuple[int, str]]] = []
        for group in groups:
            refined.extend(self._split_by_titles(group))
        return refined

    def _split_by_titles(self, group: List[Tuple[int, str]]) -> List[List[Tuple[int, str]]]:
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

            # Check if this line is an unbulleted continuation of a previous bullet
            if current and self._is_bullet_continuation(current[-1][1], text):
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

    def _is_bullet_continuation(self, prev_text: str, curr_text: str) -> bool:
        if self._is_bullet(curr_text) or self._is_label(curr_text):
            return False
        prev_s = prev_text.strip()
        curr_s = curr_text.strip()
        if not prev_s or not curr_s:
            return False
        if "|" in curr_s or match_section_header(curr_s) is not None:
            return False
        if not prev_s.endswith((".", "!", "?", ":", ";")):
            first_token = re.sub(r"[^a-zA-Z]", "", curr_s.split()[0]).lower() if curr_s.split() else ""
            if not curr_s[0].isupper() or first_token in {"and", "or", "with", "for", "by", "to", "in", "on", "of", "as", "enabling", "handling", "delivering"}:
                return True
            if any(part in curr_s.lower() for part in ("handling", "delivering", "providing", "enabling")):
                return True
            if curr_s.count(",") >= 2:
                return True
        return False

    def _looks_like_title(self, text: str) -> bool:
        s = text.strip()
        if not s or len(s) > 150:
            return False
        if self._is_bullet(text) or self._is_label(text):
            return False

        if match_section_header(s) is not None:
            return False

        core = self._strip_decorations(s)
        if not core:
            return False

        # Strong structural signals: bold, pipe, date range
        if (s.startswith("**") and s.endswith("**")) or (s.startswith("__") and s.endswith("__")):
            return True
        if "|" in s:
            return True
        if bool(_DATE_RANGE_REGEX.search(s) or _SINGLE_DATE_REGEX.search(s)):
            return True
        if re.search(r"\s[–—\-]\s", s) and re.search(r"(19|20)\d{2}", s):
            return True

        # Action verbs at start mean this is an unbulleted accomplishment line
        first_word = re.sub(r"[^a-zA-Z]", "", core.split()[0]).lower() if core.split() else ""
        if first_word in _ACTION_VERBS:
            return False

        words = re.findall(r"[A-Za-z][A-Za-z0-9+#.&/]*", core)
        if not words or len(words) > 8:
            return False
        capitalized = sum(1 for w in words if w[0].isupper())
        return (capitalized / len(words)) >= 0.6

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

    @staticmethod
    def _extract_and_strip_date(text: str) -> Tuple[str, Optional[str]]:
        m = _DATE_RANGE_REGEX.search(text) or _SINGLE_DATE_REGEX.search(text)
        if not m:
            return text.strip(), None
        date_str = m.group(0).strip()
        cleaned = text[:m.start()] + " " + text[m.end():]
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" \t\r\n|,–—-\ufffd")
        cleaned = re.sub(r"\(\s*\)|\[\s*\]", "", cleaned).strip(" \t\r\n|,–—-\ufffd")
        return cleaned, date_str

    def _parse_header(self, segment: List[Tuple[int, str]]) -> Tuple[dict, set]:
        """
        Extract organization, role, duration, location, technologies from header lines.
        Supports 1-line and 2-line header layouts with arbitrary ordering of Role vs Organization.
        """
        first_lineno, first_raw = segment[0]
        core = self._strip_decorations(first_raw)
        core = re.sub(r"[\ufffd\u2013\u2014]", " - ", core)
        core, duration = self._extract_and_strip_date(core)

        organization: Optional[str] = None
        role: Optional[str] = None
        location: Optional[str] = None
        technologies: List[str] = []

        # Multi-level splitting on pipes and hyphens
        raw_parts = [p.strip() for p in re.split(r"\s*\|\s*", core) if p.strip()]
        parts: List[str] = []
        for rp in raw_parts:
            if re.search(r"\s+[–—\-]\s+", rp):
                parts.extend([sp.strip() for sp in re.split(r"\s+[–—\-]\s+", rp) if sp.strip()])
            else:
                parts.append(rp)

        cleaned_parts: List[str] = []
        for idx_p, p in enumerate(parts):
            p_clean, p_date = self._extract_and_strip_date(p)
            if p_date and not duration:
                duration = p_date
            if not p_clean:
                continue
            is_loc_or_entity = any(loc in p_clean.lower() for loc in (
                "india", "usa", "delhi", "punjab", "bangalore", "bengaluru", "hyderabad",
                "mumbai", "pune", "noida", "gurgaon", "remote", "wfh", "hybrid",
                "pvt", "ltd", "inc", "corp", "llc", "limited", "technologies", "solutions"
            ))
            # Check if this part contains comma-separated technologies (e.g. React.js, Next.js, TailwindCSS)
            if idx_p > 0 and p_clean.count(",") >= 2 and not is_loc_or_entity:
                technologies.extend(self._split_tech(p_clean))
            else:
                cleaned_parts.append(p_clean)

        for p in cleaned_parts:
            p_low = p.lower()
            if p_low in ("remote", "wfh", "hybrid"):
                location = p
            elif any(r in p_low for r in _ROLE_INDICATORS) and "," not in p:
                if not role:
                    role = p
                elif not organization:
                    organization = p
            elif "," in p:
                chunks = [c.strip() for c in p.split(",") if c.strip()]
                first_chunk = chunks[0]
                words = first_chunk.split()
                if any(loc in p_low for loc in ("india", "usa", "delhi", "punjab", "bangalore", "bengaluru", "hyderabad", "mumbai", "pune", "noida", "gurgaon")):
                    if len(words) > 1 and not organization:
                        organization = " ".join(words[:-1])
                        location = words[-1] + p[len(first_chunk):]
                    else:
                        if not organization:
                            organization = first_chunk
                        if not location:
                            location = p[len(first_chunk):].lstrip(" ,")
                elif len(chunks) == 2:
                    sub0, sub1 = chunks[0], chunks[1]
                    sub0_low, sub1_low = sub0.lower(), sub1.lower()
                    if any(r in sub0_low for r in _ROLE_INDICATORS):
                        if not role:
                            role = sub0
                        if not organization:
                            organization = sub1
                    elif any(r in sub1_low for r in _ROLE_INDICATORS):
                        if not organization:
                            organization = sub0
                        if not role:
                            role = sub1
                    else:
                        if not organization:
                            organization = sub0
                        if not location:
                            location = sub1
                else:
                    if not organization:
                        organization = p
            else:
                if not organization:
                    organization = p
                elif not role:
                    role = p

        consumed_indices = {0}
        # If role or organization missing, inspect subsequent line(s) before bullets
        for idx in range(1, len(segment)):
            lineno, text = segment[idx]
            stripped = text.strip()
            if not stripped:
                continue
            if self._is_bullet(text) or self._is_label(text):
                break
            first_word = re.sub(r"[^a-zA-Z]", "", stripped.split()[0]).lower() if stripped.split() else ""
            if first_word in _ACTION_VERBS:
                break

            line_clean, line_date = self._extract_and_strip_date(stripped)
            if line_date and not duration:
                duration = line_date

            if not line_clean:
                consumed_indices.add(idx)
                continue

            line_low = line_clean.lower()
            if not role and any(r in line_low for r in _ROLE_INDICATORS):
                role = line_clean
                consumed_indices.add(idx)
            elif not organization and not any(r in line_low for r in _ROLE_INDICATORS):
                organization = line_clean
                consumed_indices.add(idx)
            elif not location and (line_low in ("remote", "wfh", "hybrid") or "," in line_clean):
                location = line_clean
                consumed_indices.add(idx)

        has_explicit_role = False
        if role and any(r in role.lower() for r in _ROLE_INDICATORS):
            has_explicit_role = True

        if not organization and role:
            organization = role
            role = "Intern"
        elif not role:
            role = "Intern"

        # Clean trailing location from organization if present (e.g. 'LearnDevs Remote')
        if organization:
            for loc_word in ("remote", "wfh", "hybrid"):
                if organization.lower().endswith(" " + loc_word):
                    if not location:
                        location = organization[-len(loc_word):]
                    organization = organization[:-len(loc_word)].strip(" -–—,")
                    break

        return {
            "organization": organization,
            "role": role,
            "duration": duration,
            "location": location,
            "technologies": technologies,
            "has_explicit_role": has_explicit_role,
        }, consumed_indices

    def _build_internship(self, segment: List[Tuple[int, str]]) -> Optional[InternshipEvidence]:
        """Parse segment into an InternshipEvidence."""
        if not segment:
            return None

        title_lineno, title_raw = segment[0]
        parsed_header, consumed_indices = self._parse_header(segment)
        organization = parsed_header["organization"]
        role = parsed_header["role"]
        duration = parsed_header["duration"]
        location = parsed_header["location"]
        technologies: List[str] = list(parsed_header["technologies"])
        achievements: List[str] = []
        description_parts: List[str] = []

        if not organization:
            return None

        # Filter out section headers
        if match_section_header(organization) is not None:
            return None

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
        for idx in range(len(segment)):
            if idx in consumed_indices:
                continue
            lineno, text = segment[idx]
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

            # Bullet -> achievement
            if self._is_bullet(text):
                achievement = self._strip_bullet(text)
                if achievement:
                    achievements.append(achievement)
                    evidences.append(self._evidence(achievement, lineno, context=stripped))
                continue

            # Check if this non-bullet line is an unbulleted continuation of the previous achievement
            if achievements and self._is_bullet_continuation(achievements[-1], stripped):
                achievements[-1] = f"{achievements[-1]} {stripped}"
                evidences.append(self._evidence(stripped, lineno, context=stripped))
                continue

            # Check if this line is purely a date/location line
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

        has_explicit_role = parsed_header.get("has_explicit_role", False)
        has_work_bullets = any(
            re.sub(r"[^a-zA-Z]", "", b.split()[0]).lower() in _ACTION_VERBS
            for b in achievements if b.split()
        )
        if not has_explicit_role and not has_work_bullets:
            return None

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
            confidence=1.0,
            evidences=evidences,
        )

    def _split_tech(self, value: str) -> List[str]:
        techs: List[str] = []
        val_clean, _ = self._extract_and_strip_date(value)
        for part in _TECH_SPLIT_PATTERN.split(val_clean):
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
        if bool(_DATE_RANGE_REGEX.search(value) or _SINGLE_DATE_REGEX.search(value)):
            return True
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

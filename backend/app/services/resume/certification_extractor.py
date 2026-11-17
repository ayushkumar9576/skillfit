"""
app/services/resume/certification_extractor.py
----------------------------------------------
Rule-based certification extraction for SkillFit Phase 3.9.

Extracts certifications, normalizes them to prevent duplicates, applies global 
caps (max 25), and performs deterministic provider tier assignment.

Design principles:
    - Pure standard library.
    - Fast-exit optimization (no LLM tokens burned if empty).
    - Removes duplicate certifications to save tokens.
"""

import logging
import re
from typing import List, Tuple, Optional

from app.analysis.models.base import AnalysisEvidence
from app.analysis.models.certification_models import (
    CertificationAnalysisResult,
    CertificationEvidence,
    PROVIDER_HIGH,
    PROVIDER_MEDIUM,
    PROVIDER_LOW,
    PROVIDER_UNKNOWN,
)
from app.services.resume.section_detector import DIVIDER_LINE_PATTERN
from app.services.resume.section_headers import match_section_header
from app.services.resume.section_types import ResumeSection

logger = logging.getLogger(__name__)

SECTION_SOURCE: str = "certifications"
MAX_CERTIFICATIONS_PER_RESUME = 25

_BULLET_CHARS = r"•‣◦▪◾▸▶➤✔∙·⁃\*\-–—\+>\ufffd"
_BULLET_PATTERN = re.compile(rf"^[{_BULLET_CHARS}]+\s+")
_NUMBERING_PATTERN = re.compile(r"^\(?\d{1,2}[\.\)\:]\s+")

# Provider Alias Normalization Mapping
PROVIDER_ALIASES = {
    "aws": "amazon web services",
    "amazon": "amazon web services",
    "amazon web services": "amazon web services",
    "gcp": "google",
    "google cloud": "google",
    "google": "google",
    "azure": "microsoft",
    "microsoft azure": "microsoft",
    "microsoft": "microsoft",
    "coursera": "coursera",
    "edureka": "edureka",
    "udemy": "udemy",
    "linkedin learning": "linkedin learning",
    "linkedin": "linkedin learning",
    "oracle": "oracle",
    "cisco": "cisco",
    "meta": "meta",
    "facebook": "meta",
    "infosys springboard": "infosys springboard",
    "infosys": "infosys springboard",
}

# Tier Mapping on Normalized Names
PROVIDER_TIERS = {
    "amazon web services": PROVIDER_HIGH,
    "google": PROVIDER_HIGH,
    "microsoft": PROVIDER_HIGH,
    "oracle": PROVIDER_HIGH,
    "cisco": PROVIDER_HIGH,
    "meta": PROVIDER_HIGH,
    "coursera": PROVIDER_MEDIUM,
    "edureka": PROVIDER_MEDIUM,
    "linkedin learning": PROVIDER_MEDIUM,
    "udemy": PROVIDER_LOW,
    "infosys springboard": PROVIDER_MEDIUM,
}

_DESCRIPTION_PREFIXES = frozenset({
    "achieved", "applied", "built", "completed", "created", "developed",
    "enhanced", "gained", "implemented", "improved", "learned", "practiced",
    "solved", "strengthened", "studied", "trained", "used", "worked",
})


class RuleBasedCertificationExtractor:
    """
    Deterministic certification extractor.
    """

    def extract(self, raw_text: str) -> CertificationAnalysisResult:
        """
        Extracts certifications from raw resume text.
        Returns early with 0 count if no certifications are found (fast-exit).
        """
        empty_result = CertificationAnalysisResult(
            certifications=[], reports=[], total_certifications_count=0
        )
        if not raw_text or not isinstance(raw_text, str) or not raw_text.strip():
            logger.debug("Certification extraction invoked with empty or invalid text.")
            return empty_result

        lines = raw_text.split("\n")
        block = self._locate_certifications_block(lines)
        if not block:
            logger.debug("No certifications section located in resume text.")
            return empty_result

        segments = self._segment(block)
        
        certifications: List[CertificationEvidence] = []
        seen_titles = set()

        for segment in segments:
            cert = self._build_certification(segment)
            if not cert or not cert.certification_name:
                continue
                
            # Duplicate Protection
            normalized_title = self._normalize_title(cert.certification_name)
            if not normalized_title or normalized_title in seen_titles:
                continue
                
            seen_titles.add(normalized_title)
            certifications.append(cert)
            
            # Global Token Budget Protection
            if len(certifications) >= MAX_CERTIFICATIONS_PER_RESUME:
                logger.warning(
                    f"Truncating certifications to MAX limit ({MAX_CERTIFICATIONS_PER_RESUME}). "
                    f"Ignored subsequent certifications."
                )
                break

        if not certifications:
            return empty_result

        logger.info("Certification extraction completed: %d certification(s) identified.", len(certifications))
        return CertificationAnalysisResult(
            certifications=certifications,
            reports=[],
            total_certifications_count=len(certifications)
        )

    def _locate_certifications_block(self, lines: List[str]) -> List[Tuple[int, str]]:
        start: Optional[int] = None
        for idx, line in enumerate(lines):
            if match_section_header(line) == ResumeSection.CERTIFICATIONS:
                start = idx + 1
                break
                
        if start is None:
            return []

        block: List[Tuple[int, str]] = []
        for idx in range(start, len(lines)):
            line = lines[idx]
            matched = match_section_header(line)
            if matched is not None:
                if matched == ResumeSection.CERTIFICATIONS:
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
        """
        Certifications are often listed line-by-line or separated by bullets.
        We group them by lines that look like new list items, or split by blanks.
        """
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
                
            # If the line starts with a bullet, we consider it a new certification segment,
            # UNLESS it's indented much further (heuristic: wait, for now just split if we have current).
            if self._is_bullet(text) and current:
                bullet_text = self._strip_decorations(text)
                if (
                    self._looks_like_description(bullet_text)
                    and not self._has_certificate_title_keyword(bullet_text)
                ):
                    current.append((lineno, text))
                else:
                    groups.append(current)
                    current = [(lineno, text)]
            else:
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
        
        for index, (lineno, text) in enumerate(group[1:], start=1):
            if self._is_bullet(text):
                current.append((lineno, text))
                continue
            if self._looks_like_title(text):
                next_text = group[index + 1][1] if index + 1 < len(group) else None
                if self._looks_like_provider_metadata(current, text, next_text):
                    current.append((lineno, text))
                    continue
                subs.append(current)
                current = [(lineno, text)]
                continue
            current.append((lineno, text))
            
        subs.append(current)
        return subs

    def _looks_like_title(self, text: str) -> bool:
        s = text.strip()
        if not s or len(s) > 150:
            return False
        if self._is_bullet(text):
            return False
            
        core = self._strip_decorations(s)
        if not core:
            return False
            
        lower = core.lower()
        
        # 1. Exclude date-only metadata, while allowing certificate titles that
        # include a date on the same line.
        month_pattern = (
            r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|"
            r"jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|"
            r"nov(?:ember)?|dec(?:ember)?)"
        )
        if re.fullmatch(rf"{month_pattern}\s+\d{{4}}", lower):
            return False
        if re.fullmatch(r"(?:19|20)\d{2}(?:\s*[-–—/]\s*(?:19|20)\d{2})?", lower):
            return False

        # 2. Exclude URL lines
        if "http://" in lower or "https://" in lower or "www." in lower:
            return False
            
        # 3. Exclude Verification/link lines and Provider lines
        # E.g. "Certificate Link", "Edureka - Certificate Link", "Credential Verification"
        metadata_keywords = [
            "link", "credential", "verification", "verify", "validation", "id:", "credential id"
        ]
        provider_keywords = tuple(PROVIDER_ALIASES)
        
        # Check if the line is primarily composed of provider or metadata keywords
        # A simple heuristic: if it contains a strong metadata keyword like "certificate link", it's metadata.
        if "certificate link" in lower or "verify certificate" in lower:
            return False
            
        # If it contains a provider keyword AND a metadata keyword (like "Coursera - Certificate Link")
        has_provider = any(p in lower for p in provider_keywords)
        has_metadata = any(m in lower for m in metadata_keywords)
        
        if has_metadata:
            return False
            
        # If the line is EXACTLY a provider name (e.g., "Coursera", "Udemy")
        if lower in provider_keywords:
            return False
            
        # Specific whole-word keywords often indicate a line is a title.
        if self._has_certificate_title_keyword(lower):
            return True

        # Provider/issuer lines belong to the preceding certificate. They are
        # metadata even when written in title case (for example,
        # "DeepLearning.AI, Coursera" or "Infosys Springboard").
        if has_provider and re.search(r"[,|–—]", core):
            return False
            
        # Fallback to capitalization heuristics (short noun phrases)
        words = re.findall(r"[A-Za-z][A-Za-z0-9+#.&/]*", core)
        if not words or len(words) > 8:
            return False
        capitalized = sum(1 for w in words if w[0].isupper())
        return (capitalized / len(words)) >= 0.6

    @staticmethod
    def _looks_like_description(text: str) -> bool:
        words = text.strip().split()
        if not words:
            return False
        first = re.sub(r"[^a-zA-Z]", "", words[0]).lower()
        return first in _DESCRIPTION_PREFIXES

    @staticmethod
    def _has_certificate_title_keyword(text: str) -> bool:
        return bool(re.search(
            r"\b(?:certified|certification|certificate|course|specialization)\b",
            text.lower(),
        ))

    @staticmethod
    def _contains_date(text: str) -> bool:
        return bool(re.search(
            r"\b(?:19|20)\d{2}\b|"
            r"\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|"
            r"jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|"
            r"nov(?:ember)?|dec(?:ember)?)\b",
            text,
            re.IGNORECASE,
        ))

    def _looks_like_provider_metadata(
        self,
        current: List[Tuple[int, str]],
        candidate: str,
        next_text: Optional[str],
    ) -> bool:
        if not current:
            return False
        candidate_core = self._strip_decorations(candidate)
        if (
            self._has_certificate_title_keyword(candidate_core)
            or self._contains_date(candidate_core)
            or len(candidate_core.split()) > 5
        ):
            return False

        current_title = self._strip_decorations(current[0][1])
        if not self._contains_date(current_title):
            return False
        if next_text is None:
            return True
        return self._contains_date(next_text) or self._is_bullet(next_text)

    def _build_certification(self, segment: List[Tuple[int, str]]) -> Optional[CertificationEvidence]:
        if not segment:
            return None

        # Title line is the first non-empty line
        title_lineno, title_raw = segment[0]
        title_text = self._strip_decorations(title_raw)
        
        evidences = []
        for lineno, text in segment:
            stripped = text.strip()
            if stripped:
                evidences.append(AnalysisEvidence(
                    evidence_text=self._strip_decorations(text),
                    source_section=SECTION_SOURCE,
                    confidence=1.0,
                    context_snippet=stripped,
                    line_number=lineno,
                ))

        # Detect provider from the segment texts
        provider = self._detect_provider(" ".join(e.evidence_text for e in evidences))

        return CertificationEvidence(
            certification_name=title_text,
            issuer=provider or "unknown",
            evidences=evidences
        )

    @staticmethod
    def _is_bullet(text: str) -> bool:
        return bool(_BULLET_PATTERN.match(text.lstrip()))

    @staticmethod
    def _strip_decorations(line: str) -> str:
        text = line.strip()
        text = re.sub(r"^#+\s*", "", text)
        text = re.sub(r"^[\*_~`]+", "", text)
        text = re.sub(r"[\*_~`]+$", "", text)
        text = _BULLET_PATTERN.sub("", text)
        text = _NUMBERING_PATTERN.sub("", text)
        return text.strip()

    def _normalize_title(self, title: str) -> str:
        """Lowercases and removes non-alphanumeric chars for exact duplicate detection."""
        low = title.lower()
        return re.sub(r'[^a-z0-9]', '', low)
        
    def _detect_provider(self, text: str) -> Optional[str]:
        """
        Attempts to deterministically extract the provider using PROVIDER_ALIASES.
        Returns the original alias if found, mapped to standard name.
        """
        text_lower = text.lower()
        
        # Sort aliases by length descending so "amazon web services" matches before "amazon"
        for alias in sorted(PROVIDER_ALIASES.keys(), key=len, reverse=True):
            # Check for word boundary match to avoid substring false positives
            if re.search(rf'\b{re.escape(alias)}\b', text_lower):
                return PROVIDER_ALIASES[alias]
                
        return None

def get_provider_tier(provider: Optional[str]) -> str:
    """Helper to convert a normalized provider name to its tier."""
    if not provider:
        return PROVIDER_UNKNOWN
    return PROVIDER_TIERS.get(provider.lower(), PROVIDER_UNKNOWN)

def get_certification_extractor() -> RuleBasedCertificationExtractor:
    return RuleBasedCertificationExtractor()

def extract_certifications_from_text(raw_text: str) -> CertificationAnalysisResult:
    return get_certification_extractor().extract(raw_text)

"""
app/drives/parsers/base.py
----------------------------
Abstract base for all Drive source normalizers.

Phase 4.2 — Drive Ingestion & Parsing.

Design contract:
    - Normalizers are STATELESS.
    - Normalizers are DETERMINISTIC.  The same raw_text always yields the
      same normalized_text — no randomness, no LLM calls, no AI.
    - Normalizers do NOT extract intelligence.  They improve consistency only.
    - Normalizers PRESERVE SEMANTIC MEANING.  They never infer or add content.

What normalizers DO:
    - Remove excess whitespace
    - Collapse repeated blank lines
    - Strip page markers / footer artifacts from PDF extraction
    - Normalize Unicode to NFC (e.g. composed characters)
    - Strip null bytes and non-printable control characters
    - Decode common mojibake patterns

What normalizers DO NOT do:
    - Extract skills, technologies, requirements
    - Infer structure (sections, headings)
    - Score or rank content
    - Use AI or ML
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class NormalizationResult:
    """
    Output produced by a single normalizer invocation.

    Attributes:
        normalized_text:  Cleaned text ready for Phase 4.3 consumption.
        character_count:  Character count of normalized_text.
        word_count:       Word count of normalized_text.
        parser_version:   Version string of the normalizer that produced this.
        transformations:  List of human-readable transformation labels applied
                          (e.g. ["collapsed_blank_lines", "stripped_page_markers"]).
                          Useful for debugging and regression testing.
    """
    normalized_text: str
    character_count: int
    word_count: int
    parser_version: str
    transformations: list[str] = field(default_factory=list)


class BaseNormalizer(ABC):
    """
    Abstract normalizer interface.

    All normalizers must implement normalize() and expose VERSION.
    """

    #: Semver-style version string — bump when normalization logic changes
    VERSION: str = "v1.0"

    @abstractmethod
    def normalize(self, raw_text: str) -> NormalizationResult:
        """
        Normalize raw_text and return a NormalizationResult.

        Args:
            raw_text: The unmodified text from an extractor.

        Returns:
            NormalizationResult with normalized_text, counts, and metadata.
        """

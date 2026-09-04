"""
app/drives/parsers/standard_normalizer.py
-------------------------------------------
Standard deterministic normalizer for Drive source content (Phase 4.2).

This is the default normalizer.  It applies a fixed, ordered sequence of
text transformations to produce consistent, clean output suitable for
Phase 4.3 intelligence consumption.

All transformations are:
    - Deterministic — same input always produces same output
    - Non-inferential — no new information is added
    - Semantic-preserving — meaning is never changed, only formatting cleaned

Version log:
    v1.0 — Initial implementation:
            Unicode NFC normalization, null-byte stripping, control char removal,
            page-marker removal, encoding artifact cleanup, whitespace normalization.
"""

import logging
import re
import unicodedata

from app.drives.parsers.base import BaseNormalizer, NormalizationResult

logger = logging.getLogger(__name__)


class StandardNormalizer(BaseNormalizer):
    """
    Applies a deterministic sequence of text cleaning transformations.

    Transformation order matters — steps are applied in the sequence defined
    in normalize() to avoid interference between steps.
    """

    VERSION: str = "v1.0"

    # ------------------------------------------------------------------
    # Compiled patterns — class-level for efficiency
    # ------------------------------------------------------------------

    # PDF extraction page-marker patterns (e.g. "Page 1 of 5", "- 3 -")
    _PAGE_MARKERS: list[re.Pattern] = [
        re.compile(r'(?im)^\s*[-–—]?\s*page\s+\d+\s*(of\s+\d+)?\s*[-–—]?\s*$'),
        re.compile(r'(?im)^\s*\d+\s*$'),          # standalone page numbers
        re.compile(r'(?im)^\s*-{3,}\s*\d+\s*-{3,}\s*$'),  # "--- 3 ---" style
    ]

    # Repeated separator lines (e.g. "========", "--------", "............")
    _SEPARATOR_LINES: re.Pattern = re.compile(r'(?m)^[=\-_\.]{4,}\s*$')

    # Three or more consecutive blank lines → collapse to two
    _EXCESS_BLANK_LINES: re.Pattern = re.compile(r'\n{3,}')

    # Sequences of whitespace chars (spaces, tabs) on a line → single space
    _INLINE_WHITESPACE: re.Pattern = re.compile(r'[ \t]+')

    # Non-printable control characters (except \n, \r, \t)
    _CONTROL_CHARS: re.Pattern = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')

    # Common encoding artifacts from bad PDF extraction
    _ENCODING_ARTIFACTS: list[tuple[re.Pattern, str]] = [
        (re.compile(r'\ufffd'), ''),          # Unicode replacement char
        (re.compile(r'â€™'),   "'"),          # Mojibake: curly apostrophe
        (re.compile(r'â€œ'),   '"'),          # Mojibake: left curly quote
        (re.compile(r'â€\x9d'), '"'),         # Mojibake: right curly quote
        (re.compile(r'â€"'),   '–'),          # Mojibake: en-dash
        (re.compile(r'â€"'),   '—'),          # Mojibake: em-dash
        (re.compile(r'Â\xa0'), ' '),          # Mojibake: non-breaking space prefix
        (re.compile(r'\xa0'),  ' '),          # Non-breaking space
        (re.compile(r'\xad'),  ''),           # Soft hyphen
    ]

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def normalize(self, raw_text: str) -> NormalizationResult:
        """
        Apply the full normalization pipeline to raw_text.

        Args:
            raw_text: Unmodified text from an extractor.

        Returns:
            NormalizationResult with clean text and processing metadata.
        """
        transformations: list[str] = []
        text = raw_text

        # Step 1: Unicode NFC normalization (composed form)
        text_nfc = unicodedata.normalize("NFC", text)
        if text_nfc != text:
            transformations.append("unicode_nfc")
        text = text_nfc

        # Step 2: Remove null bytes and non-printable control characters
        text_clean = self._CONTROL_CHARS.sub('', text)
        if text_clean != text:
            transformations.append("stripped_control_chars")
        text = text_clean

        # Step 3: Fix common encoding artifacts (mojibake, replacement chars)
        for pattern, replacement in self._ENCODING_ARTIFACTS:
            replaced = pattern.sub(replacement, text)
            if replaced != text:
                transformations.append("fixed_encoding_artifacts")
                text = replaced
                break  # label once even if multiple patterns fire

        # Step 4: Remove PDF page markers
        for marker_pattern in self._PAGE_MARKERS:
            replaced = marker_pattern.sub('', text)
            if replaced != text:
                transformations.append("removed_page_markers")
                text = replaced
                break

        # Step 5: Remove separator lines (==== / ---- / ....)
        replaced = self._SEPARATOR_LINES.sub('', text)
        if replaced != text:
            transformations.append("removed_separator_lines")
        text = replaced

        # Step 6: Normalize inline whitespace (tabs, multiple spaces → one space)
        replaced = self._INLINE_WHITESPACE.sub(' ', text)
        if replaced != text:
            transformations.append("normalized_inline_whitespace")
        text = replaced

        # Step 7: Strip trailing whitespace from each line
        lines = [line.rstrip() for line in text.split('\n')]
        rejoined = '\n'.join(lines)
        if rejoined != text:
            transformations.append("stripped_trailing_whitespace")
        text = rejoined

        # Step 8: Collapse excess blank lines (3+ consecutive → 2)
        replaced = self._EXCESS_BLANK_LINES.sub('\n\n', text)
        if replaced != text:
            transformations.append("collapsed_blank_lines")
        text = replaced

        # Step 9: Strip leading/trailing whitespace from the full document
        text = text.strip()

        # Compute content statistics
        char_count = len(text)
        word_count = len(text.split()) if text else 0

        logger.info(
            "StandardNormalizer v%s: %d chars, %d words, transformations=%s",
            self.VERSION,
            char_count,
            word_count,
            transformations,
        )

        return NormalizationResult(
            normalized_text=text,
            character_count=char_count,
            word_count=word_count,
            parser_version=self.VERSION,
            transformations=transformations,
        )

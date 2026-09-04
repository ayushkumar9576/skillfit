"""
app/drives/extractors/text_extractor.py
-----------------------------------------
Plain-text source extractor for Drive Ingestion (Phase 4.2).

Handles raw text submissions (POST /api/v1/drives/{id}/text).

This extractor is a thin wrapper that accepts a string and returns it as
an ExtractionResult, preserving the same pipeline interface used for PDFs.
The normaliser is still applied downstream for consistent whitespace/encoding
cleanup regardless of input source.

Determinism:
    TextExtractor is trivially deterministic — the same input string always
    produces the same raw_text.
"""

import logging
from typing import Union

from app.drives.extractors.base import BaseExtractor, ExtractionResult

logger = logging.getLogger(__name__)


class TextExtractor(BaseExtractor):
    """
    Wraps a raw text string as an ExtractionResult.

    Used when the caller submits a job description as plain text rather
    than uploading a PDF.  No file parsing occurs; the text is passed
    through unchanged so the standard normaliser can process it.
    """

    VERSION: str = "v1.0"
    METHOD: str = "raw_text"

    def extract(self, source: Union[bytes, str]) -> ExtractionResult:
        """
        Accept a raw text string (or UTF-8 bytes) and return it as-is.

        Args:
            source: Plain text string or UTF-8 encoded bytes.

        Returns:
            ExtractionResult with raw_text = str(source), page_count=None.
        """
        if isinstance(source, bytes):
            try:
                text = source.decode("utf-8")
            except UnicodeDecodeError as exc:
                return ExtractionResult(
                    raw_text="",
                    extraction_method=self.METHOD,
                    extractor_version=self.VERSION,
                    success=False,
                    error_message=f"Text bytes could not be decoded as UTF-8: {exc}",
                )
        elif isinstance(source, str):
            text = source
        else:
            return ExtractionResult(
                raw_text="",
                extraction_method=self.METHOD,
                extractor_version=self.VERSION,
                success=False,
                error_message=(
                    f"TextExtractor requires str or bytes, got {type(source).__name__}."
                ),
            )

        logger.info("TextExtractor: accepted %d chars of raw text.", len(text))

        return ExtractionResult(
            raw_text=text,
            extraction_method=self.METHOD,
            extractor_version=self.VERSION,
            page_count=None,
            warnings=[],
            success=True,
        )

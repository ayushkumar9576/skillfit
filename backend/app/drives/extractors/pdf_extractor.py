"""
app/drives/extractors/pdf_extractor.py
----------------------------------------
PDF-specific content extractor for Drive Ingestion (Phase 4.2).

Uses pdfplumber for text extraction.  pdfplumber is already a project
dependency (used in Phase 3.2.1 resume validation) so no new dependency
is introduced.

Security:
    - Only text is extracted.  No embedded scripts, attachments, or active
      content is executed or exposed.
    - pdfplumber runs in-process on the provided bytes; no subprocess is spawned.
    - Corrupted or malicious PDFs that pdfplumber cannot open are caught and
      returned as ExtractionResult(success=False).

Determinism:
    pdfplumber's text extraction is deterministic for the same input bytes.
    The same PDF always produces the same raw_text.
"""

import io
import logging
from typing import Union

from app.drives.extractors.base import BaseExtractor, ExtractionResult

logger = logging.getLogger(__name__)


class PDFExtractor(BaseExtractor):
    """
    Extracts plain text from a PDF using pdfplumber.

    Per-page text is joined with double newlines to preserve structure
    from multi-page documents.  Blank pages generate a warning but do
    not stop extraction.
    """

    VERSION: str = "v1.0"
    METHOD: str = "pdfplumber"

    def extract(self, source: Union[bytes, str]) -> ExtractionResult:
        """
        Extract text from PDF bytes.

        Args:
            source: Raw PDF bytes.

        Returns:
            ExtractionResult with raw_text containing per-page text joined
            by double newlines, plus page_count and any per-page warnings.
        """
        if not isinstance(source, bytes):
            return ExtractionResult(
                raw_text="",
                extraction_method=self.METHOD,
                extractor_version=self.VERSION,
                success=False,
                error_message=(
                    f"PDFExtractor requires bytes input, got {type(source).__name__}."
                ),
            )

        try:
            import pdfplumber
        except ImportError:
            return ExtractionResult(
                raw_text="",
                extraction_method=self.METHOD,
                extractor_version=self.VERSION,
                success=False,
                error_message="pdfplumber is not installed.",
            )

        warnings: list[str] = []
        page_texts: list[str] = []
        page_count: int = 0

        try:
            with pdfplumber.open(io.BytesIO(source)) as pdf:
                page_count = len(pdf.pages)
                for page_num, page in enumerate(pdf.pages, start=1):
                    try:
                        text = page.extract_text() or ""
                        if not text.strip():
                            warnings.append(f"Page {page_num} yielded no extractable text.")
                        page_texts.append(text)
                    except Exception as page_exc:
                        warnings.append(
                            f"Page {page_num} extraction error: {page_exc}"
                        )
                        logger.warning(
                            "PDFExtractor: page %d extraction error: %s", page_num, page_exc
                        )
        except Exception as exc:
            logger.warning("PDFExtractor: failed to open PDF: %s", exc)
            return ExtractionResult(
                raw_text="",
                extraction_method=self.METHOD,
                extractor_version=self.VERSION,
                page_count=0,
                warnings=[],
                success=False,
                error_message=f"PDF could not be opened: {exc}",
            )

        raw_text = "\n\n".join(page_texts)

        logger.info(
            "PDFExtractor: extracted %d chars from %d pages (warnings=%d).",
            len(raw_text),
            page_count,
            len(warnings),
        )

        return ExtractionResult(
            raw_text=raw_text,
            extraction_method=self.METHOD,
            extractor_version=self.VERSION,
            page_count=page_count,
            warnings=warnings,
            success=True,
        )

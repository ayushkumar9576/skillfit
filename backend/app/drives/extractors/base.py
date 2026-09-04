"""
app/drives/extractors/base.py
-------------------------------
Abstract base for all Drive source extractors.

Phase 4.2 — Drive Ingestion & Parsing.

Design contract:
    - Extractors are STATELESS.  A single instance may be reused across requests.
    - Extractors are DETERMINISTIC.  The same input bytes always yield the same output.
    - Extractors are FORMAT-SPECIFIC.  Each handles exactly one source format.
    - Extractors do NOT normalise, classify, or infer any intelligence.
    - The service layer never contains format-specific logic — it delegates to
      the appropriate extractor via get_extractor().

ExtractionResult:
    The output contract between the extraction layer and the service/normaliser.
    All fields are explicit and typed.  Warnings are logged but do not fail the
    pipeline; they are preserved in DriveSource.processing_metadata.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ExtractionResult:
    """
    Output produced by a single extractor invocation.

    Attributes:
        raw_text:         The extracted text exactly as produced by the extractor.
                          Whitespace and encoding issues are NOT cleaned here —
                          that is the normaliser's responsibility.
        extraction_method: Human-readable label (e.g. "pdfplumber", "raw_text").
        extractor_version: Version string of the extractor component (e.g. "v1.0").
        page_count:        Number of pages for PDF sources; None for text.
        warnings:          Non-fatal extraction warnings (e.g. "page 3 had no text").
                           Preserved in DriveSource.processing_metadata for debugging.
        success:           False if extraction failed entirely; raw_text may be empty.
        error_message:     Populated only when success=False.
    """
    raw_text: str
    extraction_method: str
    extractor_version: str
    page_count: Optional[int] = None
    warnings: list[str] = field(default_factory=list)
    success: bool = True
    error_message: Optional[str] = None


class BaseExtractor(ABC):
    """
    Abstract extractor interface.

    All extractors must implement extract() and expose VERSION and METHOD
    class attributes for pipeline provenance tracking.
    """

    #: Semver-style version string — bump when extraction logic changes
    VERSION: str = "v1.0"

    #: Human-readable label stored in DriveSource.extraction_method
    METHOD: str = "base"

    @abstractmethod
    def extract(self, source: bytes | str) -> ExtractionResult:
        """
        Extract raw text from source bytes or string.

        Args:
            source: Raw bytes (for file-based sources like PDF) or
                    a plain string (for text-based sources).

        Returns:
            ExtractionResult with raw_text and metadata.
            On failure, returns an ExtractionResult with success=False
            rather than raising — the service layer decides how to handle it.
        """

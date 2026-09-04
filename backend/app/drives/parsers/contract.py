"""
app/drives/parsers/contract.py
--------------------------------
Phase 4.2 → Phase 4.3 output contract.

ParsedDriveContent is the stable, versioned data structure that represents
a fully ingested and normalised job description.

CRITICAL DESIGN NOTE:
    This is the contract between Phase 4.2 and Phase 4.3.
    The Drive Intelligence Engine (Phase 4.3) will NEVER read raw PDFs.
    It consumes ParsedDriveContent exclusively.

    All future intelligence, retrieval, matching, ranking, and ML systems
    depend on this contract.  Design changes here must be versioned.

    Phase 4.2 populates this contract.
    Phase 4.3 reads it as input.

    The contract is serializable to/from JSON for:
        - Storage in DriveSource.processing_metadata (optional)
        - Future caching layers
        - Retrieval systems
        - ML feature pipelines

Versioning:
    CONTRACT_VERSION is bumped when the structure changes.
    DriveSource.parser_version tracks which version produced a given record.
    This enables future reprocessing of historical data with a new contract.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Optional

#: Bump this when ParsedDriveContent structure changes.
#: Corresponds to DriveSource.parser_version in the DB.
CONTRACT_VERSION: str = "v1.0"


@dataclass
class SourceMetadata:
    """
    Provenance metadata for the ingested source.

    Attributes:
        source_format:     "pdf" or "text" — matches DriveSourceFormat.
        original_filename: Client-supplied filename (for auditability).
        content_hash:      SHA-256 of the raw source bytes.
        extraction_method: Label of the extractor used (e.g. "pdfplumber").
        extractor_version: Version of the extractor component.
        parser_version:    Version of the normalizer component.
        page_count:        Page count for PDFs; None for text.
        ingested_at:       UTC timestamp of ingestion.
    """
    source_format: str
    original_filename: Optional[str]
    content_hash: str
    extraction_method: str
    extractor_version: str
    parser_version: str
    page_count: Optional[int]
    ingested_at: str  # ISO-8601 UTC string — avoids datetime serialization complexity


@dataclass
class ContentStatistics:
    """
    Quantitative metrics on the normalized content.

    Used for validation, debugging, and anomaly detection.
    (character_count = 25 may indicate extraction failure.)

    Attributes:
        character_count: Char count of normalized_text.
        word_count:      Word count of normalized_text.
        line_count:      Line count of normalized_text.
    """
    character_count: int
    word_count: int
    line_count: int


@dataclass
class ParsedDriveContent:
    """
    The fully parsed and normalised representation of a job description source.

    This is the stable contract between Phase 4.2 (ingestion) and Phase 4.3
    (intelligence generation).  The Drive Intelligence Engine accepts this as
    its sole input; it never processes raw PDFs or raw text directly.

    Attributes:
        contract_version: Version of this dataclass structure.
        drive_id:         Integer PK of the parent Drive entity.
        source_id:        UUID string of the DriveSource row.
        source_version:   Monotonic version number of this source within the drive.
        source_metadata:  Provenance and pipeline metadata.
        raw_text:         Unmodified extracted text (as produced by the extractor).
        normalized_text:  Cleaned, normalised text ready for intelligence processing.
        statistics:       Quantitative content metrics.
        extractor_warnings: Non-fatal warnings from the extraction step.
        normalizer_transformations: Transformation labels applied by the normaliser.
        is_duplicate:     True if this source's content_hash already exists for
                          this drive.  The record is still stored (auditability);
                          Phase 4.3 may choose to skip intelligence for duplicates.
        duplicate_of_version: Version number of the earlier duplicate, if applicable.
    """
    contract_version: str
    drive_id: int
    source_id: str
    source_version: int
    source_metadata: SourceMetadata
    raw_text: str
    normalized_text: str
    statistics: ContentStatistics
    extractor_warnings: list[str] = field(default_factory=list)
    normalizer_transformations: list[str] = field(default_factory=list)
    is_duplicate: bool = False
    duplicate_of_version: Optional[int] = None

    def to_dict(self) -> dict:
        """Serialize to a plain dict (JSON-safe for JSONB storage)."""
        return asdict(self)

    @classmethod
    def current_version(cls) -> str:
        """Return the current contract version string."""
        return CONTRACT_VERSION

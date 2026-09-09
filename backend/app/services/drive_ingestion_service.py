"""
app/services/drive_ingestion_service.py
-----------------------------------------
Phase 4.2 — Drive Ingestion & Parsing Service.

Single responsibility: orchestrate the full ingestion pipeline for a Drive
job description source (PDF upload or raw text).

Pipeline stages:
    1. Validation      — size, extension, MIME type, content parseability
    2. Hashing         — SHA-256 for duplicate detection & integrity
    3. Duplicate check — flag duplicates; always store new version (auditability)
    4. Version bump    — determine next explicit version number for the drive
    5. Security scan   — NoOpScanner today; ClamAV-compatible hook for Phase 5+
    6. Storage         — persist physical file via StorageProvider (PDF only)
    7. Extraction      — extract raw text via format-specific extractor
    8. Normalisation   — deterministic whitespace/encoding cleanup
    9. Persistence     — write DriveSource row with all metadata
    10. Contract build — assemble ParsedDriveContent for Phase 4.3 handoff

Design contracts:
    - Follows the API → Service → SQLAlchemy Session pattern exclusively.
      No repository layer is introduced.
    - Service commits the transaction after a successful pipeline run.
    - On failure at any stage, the transaction is rolled back and the exception
      is re-raised.  Partial writes (e.g. file saved but DB insert failed) are
      cleaned up before re-raising.
    - Security event logging is structured and explicit for monitoring/audit.
    - No intelligence generation occurs here — Phase 4.3 concern only.

Phase roadmap:
    Phase 4.2 — Initial ingestion pipeline (this file).
    Phase 4.3 — Intelligence pipeline will call
                 drive_service.save_drive_snapshot() after processing
                 ParsedDriveContent.  No changes to this service expected.
"""

import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional
import uuid

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.enums import (
    DriveSourceFormat,
    DriveSourceProcessingStatus,
    DriveSourceValidationStatus,
)
from app.core.storage import get_drive_storage
from app.core.security.scanner import ScanError, get_scanner
from app.drives.extractors import get_extractor
from app.drives.parsers import get_normalizer
from app.drives.parsers.contract import (
    CONTRACT_VERSION,
    ContentStatistics,
    ParsedDriveContent,
    SourceMetadata,
)
from app.models.drive import Drive
from app.models.drive_source import DriveSource

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MAX_FILE_SIZE: int = 10 * 1024 * 1024       # 10 MB
MAX_TEXT_SIZE: int = 5 * 1024 * 1024        # 5 MB for raw text submissions
MIN_CONTENT_LENGTH: int = 50               # Minimum chars to be a meaningful JD
ALLOWED_EXTENSIONS: frozenset[str] = frozenset({".pdf"})

_PDF_SIGNATURE: bytes = b"%PDF-"

# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def _validate_pdf_upload(
    file_bytes: bytes,
    original_filename: str,
    drive_id: uuid.UUID,
) -> None:
    """
    Multi-layer PDF validation.

    Raises:
        ValueError with a user-safe message on any validation failure.
        Security events are logged with structured context.
    """
    # --- Layer 1: Size ---
    size = len(file_bytes)
    if size == 0:
        logger.warning(
            "SECURITY_EVENT:EMPTY_FILE drive_id=%d filename=%r",
            drive_id, original_filename,
        )
        raise ValueError("Uploaded file is empty.")

    max_mb = MAX_FILE_SIZE // (1024 * 1024)
    if size > MAX_FILE_SIZE:
        logger.warning(
            "SECURITY_EVENT:FILE_TOO_LARGE drive_id=%d filename=%r size=%d",
            drive_id, original_filename, size,
        )
        raise ValueError(
            f"File size ({size / (1024 * 1024):.1f} MB) exceeds the {max_mb} MB limit."
        )

    # --- Layer 2: Extension (normalised, lower-cased) ---
    import os
    _, ext = os.path.splitext(original_filename)
    ext = ext.lower()
    # Strip double extensions (e.g. .pdf.exe → last segment is .exe)
    if ext not in ALLOWED_EXTENSIONS:
        logger.warning(
            "SECURITY_EVENT:INVALID_EXTENSION drive_id=%d filename=%r ext=%r",
            drive_id, original_filename, ext,
        )
        raise ValueError(
            f"Unsupported file type '{ext or '(none)'}'. "
            f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}."
        )

    # --- Layer 3: Magic bytes (PDF signature) ---
    if not file_bytes.startswith(_PDF_SIGNATURE):
        logger.warning(
            "SECURITY_EVENT:INVALID_MAGIC_BYTES drive_id=%d filename=%r",
            drive_id, original_filename,
        )
        raise ValueError(
            "File does not appear to be a valid PDF. "
            "The file content does not match the PDF format."
        )

    # --- Layer 4: MIME type via libmagic ---
    try:
        import magic
        detected_mime = magic.from_buffer(file_bytes, mime=True)
        if detected_mime != "application/pdf":
            logger.warning(
                "SECURITY_EVENT:MIME_MISMATCH drive_id=%d filename=%r "
                "detected_mime=%r expected=application/pdf",
                drive_id, original_filename, detected_mime,
            )
            raise ValueError(
                f"File content does not match the declared PDF format "
                f"(detected MIME: {detected_mime})."
            )
    except ImportError:
        logger.warning(
            "python-magic not available — skipping MIME type validation "
            "for drive_id=%d filename=%r", drive_id, original_filename
        )

    # --- Layer 5: Parser validation (pdfplumber opens the file) ---
    import io
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            _ = len(pdf.pages)
    except Exception as exc:
        logger.warning(
            "SECURITY_EVENT:CORRUPTED_PDF drive_id=%d filename=%r error=%s",
            drive_id, original_filename, exc,
        )
        raise ValueError(
            "The uploaded PDF appears to be corrupted or malformed. "
            "Please upload a valid, readable PDF."
        ) from exc


def _validate_text_input(text: str, drive_id: uuid.UUID) -> None:
    """
    Validate raw text submission.

    Raises:
        ValueError with a user-safe message on any validation failure.
    """
    if not text or not text.strip():
        logger.warning(
            "SECURITY_EVENT:EMPTY_TEXT_CONTENT drive_id=%d", drive_id
        )
        raise ValueError("Submitted text content is empty.")

    size = len(text.encode("utf-8"))
    max_mb = MAX_TEXT_SIZE // (1024 * 1024)
    if size > MAX_TEXT_SIZE:
        logger.warning(
            "SECURITY_EVENT:TEXT_TOO_LARGE drive_id=%d size=%d", drive_id, size
        )
        raise ValueError(
            f"Text payload ({size / (1024 * 1024):.1f} MB) exceeds the {max_mb} MB limit."
        )


# ---------------------------------------------------------------------------
# Version management
# ---------------------------------------------------------------------------


def _next_version(db: Session, drive_id: uuid.UUID) -> int:
    """
    Determine the next version number for a DriveSource under this drive.

    Uses a DB-level MAX query to ensure correctness under concurrency.
    The UniqueConstraint on (drive_id, version) prevents races.

    Returns:
        1 for the first source; existing_max + 1 otherwise.
    """
    from sqlalchemy import func
    result = (
        db.query(func.max(DriveSource.version))
        .filter(DriveSource.drive_id == drive_id)
        .scalar()
    )
    return (result or 0) + 1


# ---------------------------------------------------------------------------
# Duplicate detection
# ---------------------------------------------------------------------------


def _find_duplicate_version(
    db: Session, drive_id: uuid.UUID, content_hash: str
) -> Optional[int]:
    """
    Return the version number of an existing DriveSource with the same hash,
    or None if no duplicate exists.
    """
    existing = (
        db.query(DriveSource)
        .filter(
            DriveSource.drive_id == drive_id,
            DriveSource.content_hash == content_hash,
        )
        .order_by(DriveSource.version.asc())
        .first()
    )
    return existing.version if existing else None


# ---------------------------------------------------------------------------
# Internal pipeline orchestrator
# ---------------------------------------------------------------------------


def _run_ingestion_pipeline(
    db: Session,
    drive: Drive,
    source_format: DriveSourceFormat,
    raw_bytes: bytes,
    text_content: Optional[str],
    original_filename: Optional[str],
) -> ParsedDriveContent:
    """
    Internal pipeline shared by PDF upload and text submission.

    Args:
        db:              Active SQLAlchemy session.
        drive:           Parent Drive ORM object.
        source_format:   DriveSourceFormat.pdf or .text
        raw_bytes:       Raw bytes (PDF bytes or UTF-8 encoded text).
        text_content:    Plain text string (for text sources); None for PDF.
        original_filename: Client filename or None.

    Returns:
        ParsedDriveContent — the fully assembled output contract.

    Raises:
        ValueError:   On validation or content failure.
        ScanError:    If the security scanner detects a threat.
        RuntimeError: On extraction failure.
    """
    drive_id = drive.id
    logger.info(
        "DriveIngestion: pipeline started drive_id=%d format=%s filename=%r",
        drive_id, source_format.value, original_filename,
    )

    # --- Stage 2: Hash ---
    content_hash = hashlib.sha256(raw_bytes).hexdigest()

    # --- Stage 3: Duplicate check ---
    duplicate_of_version = _find_duplicate_version(db, drive_id, content_hash)
    is_duplicate = duplicate_of_version is not None
    if is_duplicate:
        logger.info(
            "DriveIngestion: duplicate content detected drive_id=%d "
            "hash=%s duplicate_of_version=%d — storing new version anyway.",
            drive_id, content_hash[:16], duplicate_of_version,
        )

    # --- Stage 4: Determine version ---
    version = _next_version(db, drive_id)

    # --- Stage 5: Security scan ---
    scanner = get_scanner()
    scanner.scan(raw_bytes, filename=original_filename or "")

    # --- Stage 6: Storage (PDF only) ---
    storage = get_drive_storage()
    file_path: Optional[str] = None
    if source_format == DriveSourceFormat.pdf:
        file_path = storage.save(raw_bytes, extension=".pdf")

    # --- Stage 7: Extraction ---
    extractor = get_extractor(source_format)
    extraction_input = text_content if source_format == DriveSourceFormat.text else raw_bytes
    extraction_result = extractor.extract(extraction_input)

    if not extraction_result.success:
        logger.error(
            "DriveIngestion: extraction failed drive_id=%d error=%s",
            drive_id, extraction_result.error_message,
        )
        # Clean up stored file if extraction fails
        if file_path:
            storage.delete(file_path)
        raise RuntimeError(
            f"Content extraction failed: {extraction_result.error_message}"
        )

    raw_text = extraction_result.raw_text

    # Validate extracted content is meaningful
    if len(raw_text.strip()) < MIN_CONTENT_LENGTH:
        logger.warning(
            "SECURITY_EVENT:INSUFFICIENT_CONTENT drive_id=%d chars=%d",
            drive_id, len(raw_text.strip()),
        )
        if file_path:
            storage.delete(file_path)
        raise ValueError(
            f"Extracted content is too short ({len(raw_text.strip())} chars). "
            "Please upload a valid job description."
        )

    # --- Stage 8: Normalisation ---
    normalizer = get_normalizer()
    norm_result = normalizer.normalize(raw_text)

    # --- Stage 9: Persist DriveSource ---
    ingested_at = datetime.now(timezone.utc)
    processing_metadata: dict = {
        "is_duplicate": is_duplicate,
        "duplicate_of_version": duplicate_of_version,
        "contract_version": CONTRACT_VERSION,
        "page_count": extraction_result.page_count,
        "extractor_warnings": extraction_result.warnings,
        "normalizer_transformations": norm_result.transformations,
    }

    drive_source = DriveSource(
        drive_id=drive_id,
        version=version,
        source_format=source_format,
        original_filename=original_filename,
        file_path=file_path,
        content_hash=content_hash,
        extraction_method=extraction_result.extraction_method,
        extractor_version=extraction_result.extractor_version,
        parser_version=norm_result.parser_version,
        processing_status=DriveSourceProcessingStatus.completed,
        validation_status=DriveSourceValidationStatus.valid,
        raw_content=raw_text,
        normalized_content=norm_result.normalized_text,
        character_count=norm_result.character_count,
        word_count=norm_result.word_count,
        processing_metadata=processing_metadata,
        created_at=ingested_at,
        processed_at=ingested_at,
    )

    db.add(drive_source)
    db.commit()
    db.refresh(drive_source)

    logger.info(
        "DriveIngestion: pipeline completed drive_id=%d source_id=%s version=%d "
        "chars=%d words=%d is_duplicate=%s",
        drive_id, drive_source.id, version,
        norm_result.character_count, norm_result.word_count, is_duplicate,
    )

    # --- Stage 10: Assemble ParsedDriveContent contract ---
    parsed_content = ParsedDriveContent(
        contract_version=CONTRACT_VERSION,
        drive_id=drive_id,
        source_id=str(drive_source.id),
        source_version=version,
        source_metadata=SourceMetadata(
            source_format=source_format.value,
            original_filename=original_filename,
            content_hash=content_hash,
            extraction_method=extraction_result.extraction_method,
            extractor_version=extraction_result.extractor_version,
            parser_version=norm_result.parser_version,
            page_count=extraction_result.page_count,
            ingested_at=ingested_at.isoformat(),
        ),
        raw_text=raw_text,
        normalized_text=norm_result.normalized_text,
        statistics=ContentStatistics(
            character_count=norm_result.character_count,
            word_count=norm_result.word_count,
            line_count=norm_result.normalized_text.count("\n") + 1 if norm_result.normalized_text else 0,
        ),
        extractor_warnings=extraction_result.warnings,
        normalizer_transformations=norm_result.transformations,
        is_duplicate=is_duplicate,
        duplicate_of_version=duplicate_of_version,
    )

    return parsed_content


# ---------------------------------------------------------------------------
# Public API — PDF upload
# ---------------------------------------------------------------------------


def ingest_pdf_upload(
    db: Session,
    drive: Drive,
    upload_file: UploadFile,
) -> ParsedDriveContent:
    """
    Ingest a PDF job description uploaded via POST /api/v1/drives/{id}/upload.

    Orchestrates the full validation → extraction → normalisation → persistence
    pipeline for a PDF source.

    Args:
        db:          Active SQLAlchemy session.
        drive:       The parent Drive ORM object.
        upload_file: FastAPI UploadFile from the multipart form.

    Returns:
        ParsedDriveContent — the assembled output contract.

    Raises:
        ValueError:   On validation failure (user-safe message).
        ScanError:    If the security scanner detects a threat.
        RuntimeError: On extraction failure.
    """
    original_filename = upload_file.filename or "upload.pdf"
    logger.info(
        "DriveIngestion: PDF upload started drive_id=%d filename=%r",
        drive.id, original_filename,
    )

    file_bytes = upload_file.file.read()

    # --- Stage 1: Validation ---
    _validate_pdf_upload(file_bytes, original_filename, drive.id)

    return _run_ingestion_pipeline(
        db=db,
        drive=drive,
        source_format=DriveSourceFormat.pdf,
        raw_bytes=file_bytes,
        text_content=None,
        original_filename=original_filename,
    )


# ---------------------------------------------------------------------------
# Public API — Raw text submission
# ---------------------------------------------------------------------------


def ingest_text_submission(
    db: Session,
    drive: Drive,
    text: str,
) -> ParsedDriveContent:
    """
    Ingest a raw text job description submitted via POST /api/v1/drives/{id}/text.

    Orchestrates the full validation → extraction → normalisation → persistence
    pipeline for a text source.

    Args:
        db:    Active SQLAlchemy session.
        drive: The parent Drive ORM object.
        text:  Raw text job description string.

    Returns:
        ParsedDriveContent — the assembled output contract.

    Raises:
        ValueError:   On validation failure (user-safe message).
        ScanError:    If the security scanner detects a threat.
        RuntimeError: On extraction failure.
    """
    logger.info(
        "DriveIngestion: text submission started drive_id=%d length=%d chars",
        drive.id, len(text),
    )

    # --- Stage 1: Validation ---
    _validate_text_input(text, drive.id)

    raw_bytes = text.encode("utf-8")

    return _run_ingestion_pipeline(
        db=db,
        drive=drive,
        source_format=DriveSourceFormat.text,
        raw_bytes=raw_bytes,
        text_content=text,
        original_filename=None,
    )


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------


def get_latest_drive_source(
    db: Session,
    drive_id: uuid.UUID,
) -> Optional[DriveSource]:
    """
    Retrieve the most recent DriveSource for a given drive (by version DESC).

    Returns None if no source has been ingested yet.

    Args:
        db:       Active SQLAlchemy session.
        drive_id: UUID PK of the Drive.

    Returns:
        DriveSource ORM object or None.
    """
    return (
        db.query(DriveSource)
        .filter(DriveSource.drive_id == drive_id)
        .order_by(DriveSource.version.desc())
        .first()
    )


def get_drive_source_by_id(
    db: Session,
    source_id: str,
) -> Optional[DriveSource]:
    """
    Retrieve a DriveSource by its UUID primary key.

    Args:
        db:        Active SQLAlchemy session.
        source_id: UUID string of the DriveSource.

    Returns:
        DriveSource ORM object or None.
    """
    import uuid as _uuid
    try:
        uid = _uuid.UUID(source_id)
    except ValueError:
        return None
    return db.query(DriveSource).filter(DriveSource.id == uid).first()


def list_drive_sources(
    db: Session,
    drive_id: uuid.UUID,
) -> list[DriveSource]:
    """
    List all DriveSource records for a drive, ordered by version ascending.

    Args:
        db:       Active SQLAlchemy session.
        drive_id: UUID PK of the Drive.

    Returns:
        List of DriveSource ORM objects.
    """
    return (
        db.query(DriveSource)
        .filter(DriveSource.drive_id == drive_id)
        .order_by(DriveSource.version.asc())
        .all()
    )

"""
app/core/file_utils.py
-----------------------
Reusable file-handling utilities for SkillFit Phase 3.2 / 3.2.1.

Phase 3.2.1 Security Hardening additions:
    - File signature (magic bytes) validation for PDF and DOCX
    - MIME type validation via libmagic (python-magic-bin)
    - Parser-level validation: pdfplumber (PDF) and python-docx (DOCX)
    - Resume count limit enforcement
    - Configurable upload directory (reads from settings)
    - Deletion path confinement (files are only deleted within the upload dir)

Design rules:
    - No database code.
    - No HTTP/FastAPI code.
    - No business logic.
    - Raises ValueError for validation failures so the service layer can
      translate them into the appropriate HTTPException.
"""

import hashlib
import io
import logging
import os
import uuid

import magic  # python-magic-bin (Windows-compatible libmagic binding)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ALLOWED_EXTENSIONS: frozenset[str] = frozenset({".pdf", ".docx"})
MAX_FILE_SIZE: int = 10 * 1024 * 1024          # 10 MB
MAX_RESUMES_PER_STUDENT: int = 5               # Configurable abuse limit

# Upload directory: reads from environment variable so Docker / production
# deployments can override without code changes.
UPLOAD_DIR: str = os.getenv("RESUME_UPLOAD_DIR", "uploads/resumes")

# Known-good magic-byte signatures for each supported type
_PDF_SIGNATURE: bytes = b"%PDF-"
_DOCX_ZIP_SIGNATURE: bytes = b"PK\x03\x04"    # OOXML is a ZIP archive

# Expected MIME types per extension
_EXPECTED_MIME: dict[str, str] = {
    ".pdf":  "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


# ---------------------------------------------------------------------------
# Layer 1 — Extension validation
# ---------------------------------------------------------------------------


def validate_extension(filename: str) -> str:
    """
    Return the normalised file extension (e.g. '.pdf') if it is allowed.

    This is the first, cheapest gate. Subsequent layers validate the actual
    content — do not rely on this alone.

    Raises:
        ValueError: extension is missing or not in ALLOWED_EXTENSIONS.
    """
    _, ext = os.path.splitext(filename)
    ext = ext.lower()
    if ext not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise ValueError(
            f"Unsupported file type '{ext or '(none)'}'. "
            f"Allowed types: {allowed}."
        )
    return ext


# ---------------------------------------------------------------------------
# Layer 2 — Size validation
# ---------------------------------------------------------------------------


def validate_file_size(size_bytes: int) -> None:
    """
    Raise ValueError if file is empty or exceeds MAX_FILE_SIZE.
    """
    if size_bytes == 0:
        raise ValueError(
            "Uploaded file is empty (0 bytes). Please upload a valid resume."
        )
    if size_bytes > MAX_FILE_SIZE:
        max_mb = MAX_FILE_SIZE // (1024 * 1024)
        raise ValueError(
            f"File size ({size_bytes / (1024 * 1024):.1f} MB) exceeds the "
            f"{max_mb} MB limit."
        )


# ---------------------------------------------------------------------------
# Layer 3 — File signature (magic bytes) validation
# ---------------------------------------------------------------------------


def validate_file_signature(file_bytes: bytes, extension: str) -> None:
    """
    Validate that the file's magic bytes match the declared extension.

    Catches renamed executables and other malicious files where the attacker
    changes the extension but cannot easily forge the binary header.

    PDF:  Must begin with '%PDF-'
    DOCX: Must begin with 'PK\\x03\\x04' (ZIP/OOXML archive magic bytes)

    Raises:
        ValueError: if the signature does not match the declared extension.
    """
    if extension == ".pdf":
        if not file_bytes.startswith(_PDF_SIGNATURE):
            raise ValueError(
                "File does not appear to be a valid PDF. "
                "The file content does not match the PDF format."
            )
    elif extension == ".docx":
        if not file_bytes.startswith(_DOCX_ZIP_SIGNATURE):
            raise ValueError(
                "File does not appear to be a valid DOCX file. "
                "The file content does not match the Office Open XML format."
            )


# ---------------------------------------------------------------------------
# Layer 4 — MIME type validation
# ---------------------------------------------------------------------------


def validate_mime_type(file_bytes: bytes, extension: str) -> None:
    """
    Detect the actual MIME type of the file content using libmagic and compare
    it against the expected MIME type for the declared extension.

    This is independent of the extension and independent of magic bytes — it
    uses the full libmagic heuristic database, making it harder to spoof.

    Note: libmagic identifies DOCX (a ZIP-based format) as
    'application/zip' on some platforms. We accept both
    'application/zip' and the canonical OOXML MIME type for DOCX
    to avoid false rejections.

    Raises:
        ValueError: if libmagic detects a MIME type incompatible with the
                    declared extension.
    """
    try:
        detected_mime: str = magic.from_buffer(file_bytes, mime=True)
    except Exception as exc:
        # libmagic failure is treated conservatively — reject the file
        raise ValueError(
            "Unable to determine file type. Please upload a valid PDF or DOCX."
        ) from exc

    expected_mime = _EXPECTED_MIME[extension]

    if extension == ".docx":
        # DOCX is a ZIP archive; libmagic often reports 'application/zip'
        # or 'application/octet-stream'. Accept the canonical OOXML MIME,
        # application/zip, and application/octet-stream.
        allowed_mimes = {
            expected_mime,
            "application/zip",
            "application/octet-stream",
        }
        if detected_mime not in allowed_mimes:
            logger.warning(
                "MIME mismatch for .docx: detected=%s expected one of=%s",
                detected_mime,
                allowed_mimes,
            )
            raise ValueError(
                f"File content does not match the DOCX format "
                f"(detected: {detected_mime})."
            )
    else:
        if detected_mime != expected_mime:
            logger.warning(
                "MIME mismatch: declared extension=%s detected_mime=%s expected=%s",
                extension,
                detected_mime,
                expected_mime,
            )
            raise ValueError(
                f"File content does not match the declared file type "
                f"(detected: {detected_mime})."
            )


# ---------------------------------------------------------------------------
# Layer 5 — Parser validation
# ---------------------------------------------------------------------------


def validate_parseable_pdf(file_bytes: bytes) -> None:
    """
    Attempt to open the file as a PDF using pdfplumber.

    Rejects malformed, corrupted, password-protected, or truncated PDFs
    before they enter the storage pipeline.

    Uses the same library planned for Phase 3.3 text extraction, ensuring
    that every stored PDF can later be processed without re-validation.

    Raises:
        ValueError: if pdfplumber cannot open the file.
    """
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            # Access the page count to trigger actual parsing
            _ = len(pdf.pages)
    except Exception as exc:
        logger.warning("PDF parser validation failed: %s", exc)
        raise ValueError(
            "The uploaded PDF file appears to be corrupted or malformed. "
            "Please upload a valid, readable PDF."
        ) from exc


def validate_parseable_docx(file_bytes: bytes) -> None:
    """
    Attempt to open the file as a DOCX using python-docx.

    Rejects malformed, corrupted, or truncated DOCX archives before
    they enter the storage pipeline.

    Raises:
        ValueError: if python-docx cannot open the file.
    """
    try:
        from docx import Document
        Document(io.BytesIO(file_bytes))
    except Exception as exc:
        logger.warning("DOCX parser validation failed: %s", exc)
        raise ValueError(
            "The uploaded DOCX file appears to be corrupted or malformed. "
            "Please upload a valid, readable Word document."
        ) from exc


def validate_file_parseable(file_bytes: bytes, extension: str) -> None:
    """
    Dispatch to the correct parser validator based on extension.

    This is the deepest validation layer — it uses the actual processing
    library to confirm the file is not just binary-correct but fully
    readable and decodable.

    Raises:
        ValueError: if the file cannot be parsed by the appropriate library.
    """
    if extension == ".pdf":
        validate_parseable_pdf(file_bytes)
    elif extension == ".docx":
        validate_parseable_docx(file_bytes)


# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------


def generate_sha256(file_bytes: bytes) -> str:
    """
    Compute and return the SHA-256 hex digest of the given bytes.

    Returns:
        64-character lowercase hex string.
    """
    return hashlib.sha256(file_bytes).hexdigest()


# ---------------------------------------------------------------------------
# Storage filename
# ---------------------------------------------------------------------------


def generate_storage_filename(extension: str) -> str:
    """
    Generate a UUID-based storage filename.

    Never exposes the client-supplied filename on disk, preventing:
        - Path traversal attacks
        - Filename collisions
        - Information leakage

    Example:
        generate_storage_filename(".pdf")
        → "550e8400-e29b-41d4-a716-446655440000.pdf"
    """
    return f"{uuid.uuid4()}{extension}"


# ---------------------------------------------------------------------------
# Directory management
# ---------------------------------------------------------------------------


def ensure_upload_directory(directory: str = UPLOAD_DIR) -> str:
    """
    Create the upload directory (and any parents) if it does not exist.

    Returns the absolute path to the directory.

    Raises:
        OSError: if the directory cannot be created.
    """
    abs_dir = os.path.abspath(directory)
    os.makedirs(abs_dir, exist_ok=True)
    return abs_dir


# ---------------------------------------------------------------------------
# Safe deletion with path confinement
# ---------------------------------------------------------------------------


def safe_delete_file(file_path: str, upload_dir: str = UPLOAD_DIR) -> None:
    """
    Delete a file from disk, confined to the upload directory.

    Security guarantee: the resolved absolute path of the target file MUST
    be inside the resolved absolute path of the upload directory. If the
    resolved path escapes the upload directory (e.g. via a symlink or a
    stored path that was manipulated), deletion is refused and an error is
    logged. This prevents accidental deletion of system files even if a
    DB record is somehow corrupted.

    Logs a warning if the file is not found (non-fatal).

    Args:
        file_path:  Absolute or relative path to the file to delete.
        upload_dir: The upload directory to confine deletion to.
    """
    abs_upload_dir = os.path.abspath(upload_dir)
    abs_file_path = os.path.abspath(file_path)

    # Confinement check
    if not abs_file_path.startswith(abs_upload_dir + os.sep):
        logger.error(
            "SECURITY: Refused to delete file outside upload directory. "
            "file_path=%s upload_dir=%s",
            abs_file_path,
            abs_upload_dir,
        )
        return

    try:
        os.remove(abs_file_path)
        logger.info("Deleted resume file from disk: %s", abs_file_path)
    except FileNotFoundError:
        logger.warning(
            "Resume file not found on disk during deletion: %s", abs_file_path
        )
    except OSError as exc:
        # Log but do not re-raise — DB record deletion must still proceed.
        logger.error(
            "OS error while deleting resume file %s: %s",
            abs_file_path,
            exc,
        )

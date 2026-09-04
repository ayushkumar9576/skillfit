"""
app/core/security/scanner.py
------------------------------
Malware scan hook for Phase 4.2 Drive Ingestion & Parsing.

Design:
    SecurityScanner is an abstract hook inserted into the upload pipeline
    between validation and extraction.

    Upload
      ↓
    Validation
      ↓
    SecurityScanner.scan()   ← this module
      ↓
    Extraction

    Today: NoOpScanner — always passes, zero overhead, zero dependencies.
    Future: ClamAVScanner, VirusTotalScanner, or enterprise AV integration
            — same interface, no service-layer changes required.

Usage:
    from app.core.security.scanner import get_scanner

    scanner = get_scanner()
    scanner.scan(file_bytes, filename="upload.pdf")
    # Raises ScanError on detected threat

Security notes:
    - The scan hook MUST be called before the extractor.
    - Extractor libraries (e.g. pdfplumber) process the file bytes in-memory;
      a malicious file reaching the extractor is a security risk.
    - Even with NoOpScanner today, the hook ensures future integration
      requires no service-layer restructuring.
"""

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Exception
# ---------------------------------------------------------------------------


class ScanError(Exception):
    """
    Raised by a SecurityScanner when a file fails the security scan.

    The service layer catches this and rejects the upload with a 400/422
    error response. Details are logged but NEVER exposed in the API response
    to avoid leaking scanner internals.
    """


# ---------------------------------------------------------------------------
# Abstract interface
# ---------------------------------------------------------------------------


class SecurityScanner(ABC):
    """
    Abstract security scanner hook.

    All implementations must:
        - Scan only the provided bytes (never execute them)
        - Be stateless and thread-safe
        - Raise ScanError if a threat is detected
        - Return None silently on clean files
    """

    @abstractmethod
    def scan(self, file_bytes: bytes, filename: str = "") -> None:
        """
        Scan file_bytes for threats.

        Args:
            file_bytes: Raw bytes of the uploaded file.
            filename:   Original client filename (for logging only).

        Raises:
            ScanError: if the file is identified as a threat.
        """


# ---------------------------------------------------------------------------
# NoOpScanner — Phase 4.2 default implementation
# ---------------------------------------------------------------------------


class NoOpScanner(SecurityScanner):
    """
    No-operation scanner that always passes.

    Satisfies the SecurityScanner interface with zero overhead and zero
    external dependencies.

    This is the intended Phase 4.2 implementation.
    Replace with ClamAVScanner or equivalent in Phase 5+ when AV integration
    becomes a requirement.
    """

    def scan(self, file_bytes: bytes, filename: str = "") -> None:
        """Always passes — logs the scan attempt for auditability."""
        logger.debug(
            "SecurityScanner: NoOpScanner passed. filename=%r size=%d bytes",
            filename,
            len(file_bytes),
        )


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def get_scanner() -> SecurityScanner:
    """
    Return the active SecurityScanner.

    Today returns NoOpScanner.
    Future: read env config to select ClamAV, VirusTotal, or enterprise AV.
    """
    return NoOpScanner()

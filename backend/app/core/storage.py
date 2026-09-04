"""
app/core/storage.py
--------------------
Storage abstraction for Phase 4.2 Drive Ingestion & Parsing.

Design:
    StorageProvider is a simple abstract interface that decouples the service
    layer from any specific file-storage backend.

    Today:  LocalStorage — writes files to a configured local directory.
    Future: S3Storage, AzureBlobStorage, GCSStorage — same interface, no
            service-layer changes required.

    The service layer deals only with StorageProvider; it never calls
    os.path or open() directly.

Security:
    - Storage filenames are always UUID-based (never the client filename).
    - Files are confined to the configured upload directory.
    - Deletion is path-confined to prevent traversal attacks.

Usage:
    from app.core.storage import get_drive_storage

    storage = get_drive_storage()
    path = storage.save(file_bytes, extension=".pdf")
    storage.delete(path)
"""

import logging
import os
import uuid
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Abstract interface
# ---------------------------------------------------------------------------


class StorageProvider(ABC):
    """
    Abstract file-storage provider.

    All implementations must be:
        - Deterministic: same bytes + extension → predictable storage format
        - Idempotent-safe: delete() on a missing path must not raise
        - Secure: filenames must never be derived from client input
    """

    @abstractmethod
    def save(self, file_bytes: bytes, extension: str) -> str:
        """
        Persist file_bytes and return the storage path (or key).

        Args:
            file_bytes: Raw bytes to store.
            extension:  File extension including the dot (e.g. ".pdf").

        Returns:
            An opaque path/key string that can later be passed to delete().
        """

    @abstractmethod
    def delete(self, path: str) -> None:
        """
        Remove a previously stored file.

        Must not raise if the file does not exist (log warning only).

        Args:
            path: The path/key returned by a previous save() call.
        """

    @abstractmethod
    def exists(self, path: str) -> bool:
        """Return True if the given path/key resolves to an existing file."""


# ---------------------------------------------------------------------------
# LocalStorage implementation
# ---------------------------------------------------------------------------

_DRIVE_UPLOAD_DIR: str = os.getenv("DRIVE_UPLOAD_DIR", "uploads/drives")


class LocalStorage(StorageProvider):
    """
    Stores files on the local filesystem under a configurable directory.

    Filenames are UUID-based to prevent:
        - Path traversal attacks
        - Filename collisions
        - Information leakage from original client filenames

    The upload directory is created on first use if it does not exist.
    """

    def __init__(self, upload_dir: str = _DRIVE_UPLOAD_DIR) -> None:
        self._upload_dir = os.path.abspath(upload_dir)

    def _ensure_directory(self) -> None:
        os.makedirs(self._upload_dir, exist_ok=True)

    def _safe_filename(self, extension: str) -> str:
        """Generate a UUID-based filename that is safe for filesystem storage."""
        return f"{uuid.uuid4()}{extension}"

    def save(self, file_bytes: bytes, extension: str) -> str:
        """
        Write file_bytes to a UUID-named file inside the upload directory.

        Returns:
            Absolute path to the saved file.

        Raises:
            OSError: if the file cannot be written.
        """
        self._ensure_directory()
        filename = self._safe_filename(extension)
        abs_path = os.path.join(self._upload_dir, filename)

        with open(abs_path, "wb") as f:
            f.write(file_bytes)

        logger.info("DriveSource file saved: path=%s size=%d bytes", abs_path, len(file_bytes))
        return abs_path

    def delete(self, path: str) -> None:
        """
        Delete a file, confined to the upload directory.

        Refuses to delete files outside the configured upload directory
        to prevent accidental system file deletion via corrupted DB records.
        """
        abs_path = os.path.abspath(path)

        # Path confinement check
        if not abs_path.startswith(self._upload_dir + os.sep):
            logger.error(
                "SECURITY: Refused to delete drive file outside upload directory. "
                "path=%s upload_dir=%s",
                abs_path,
                self._upload_dir,
            )
            return

        try:
            os.remove(abs_path)
            logger.info("DriveSource file deleted: path=%s", abs_path)
        except FileNotFoundError:
            logger.warning("DriveSource file not found during deletion: path=%s", abs_path)
        except OSError as exc:
            logger.error("OS error deleting DriveSource file %s: %s", abs_path, exc)

    def exists(self, path: str) -> bool:
        return os.path.isfile(os.path.abspath(path))


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def get_drive_storage() -> StorageProvider:
    """
    Return the active StorageProvider for drive source files.

    Today this returns LocalStorage.
    Future implementations may return S3Storage etc. based on env config.
    """
    return LocalStorage()

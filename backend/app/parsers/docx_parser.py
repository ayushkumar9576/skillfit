"""
app/parsers/docx_parser.py
--------------------------
Secure DOCX text extraction engine using python-docx.

Security & Integrity Controls:
    - Pre-parse ZIP bomb inspection (file size ratio, total entries, uncompressed bounds)
    - Macro/VBA safe: only extracts textual XML structures, never executes code
    - Extracts paragraph text and structured table data preserving order
    - Preserves headings and line breaks for downstream AI analysis
"""

import io
import logging
import zipfile
from typing import List
from docx import Document

logger = logging.getLogger(__name__)

# ZIP Bomb & DoS limits for DOCX packages
MAX_UNCOMPRESSED_DOCX_SIZE: int = 15 * 1024 * 1024  # 15 MB max uncompressed text/xml payload
MAX_ZIP_ENTRIES: int = 500                          # Max entries inside DOCX package
MAX_COMPRESSION_RATIO: float = 100.0                # Suspicious compression ratio threshold


def _inspect_docx_zip_safety(file_path: str) -> None:
    """
    Validate the internal ZIP container of a DOCX file to prevent ZIP bombs and DoS attacks.

    Raises:
        ValueError: if the archive violates security boundaries.
    """
    try:
        with zipfile.ZipFile(file_path, "r") as zf:
            infolist = zf.infolist()

            # 1. Entry count check
            if len(infolist) > MAX_ZIP_ENTRIES:
                raise ValueError(
                    f"DOCX archive contains too many files ({len(infolist)} > {MAX_ZIP_ENTRIES}). "
                    "Possible archive bomb detected."
                )

            total_uncompressed: int = 0
            total_compressed: int = 0

            for info in infolist:
                total_uncompressed += info.file_size
                total_compressed += info.compress_size

            # 2. Total uncompressed size check
            if total_uncompressed > MAX_UNCOMPRESSED_DOCX_SIZE:
                raise ValueError(
                    f"DOCX uncompressed content exceeds maximum allowed size "
                    f"({total_uncompressed / (1024 * 1024):.1f} MB > {MAX_UNCOMPRESSED_DOCX_SIZE // (1024 * 1024)} MB)."
                )

            # 3. High compression ratio check on non-trivial archives
            if total_compressed > 0 and total_uncompressed > 200_000:
                ratio = total_uncompressed / total_compressed
                if ratio > MAX_COMPRESSION_RATIO:
                    raise ValueError(
                        f"Suspicious compression ratio ({ratio:.1f}:1). "
                        "Possible ZIP bomb detected."
                    )

    except zipfile.BadZipFile as exc:
        raise ValueError("Invalid or corrupted DOCX archive structure.") from exc


def extract_docx_text(file_path: str) -> str:
    """
    Extract text content from a DOCX resume file including paragraphs and tables.

    Args:
        file_path: Absolute path to the DOCX file on disk.

    Returns:
        Extracted raw text string preserving section order.

    Raises:
        ValueError: if the DOCX is corrupted, invalid, or violates safety bounds.
    """
    # 1. Inspect ZIP container safety before loading full DOM
    _inspect_docx_zip_safety(file_path)

    try:
        doc = Document(file_path)
        extracted_sections: List[str] = []

        # 2. Extract paragraph text
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                extracted_sections.append(text)

        # 3. Extract table text (many resumes format skills/education in tables)
        for table in doc.tables:
            for row in table.rows:
                row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_cells:
                    # Join table cell text cleanly
                    extracted_sections.append(" | ".join(row_cells))

        if not extracted_sections:
            raise ValueError(
                "No readable text could be extracted from this DOCX file. "
                "The file may be empty or contain only embedded media."
            )

        return "\n\n".join(extracted_sections)

    except ValueError:
        raise
    except Exception as exc:
        logger.error("Failed to parse DOCX file %s: %s", file_path, exc)
        raise ValueError("Failed to extract text from DOCX document. File may be malformed or corrupted.") from exc

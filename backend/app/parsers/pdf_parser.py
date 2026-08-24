"""
app/parsers/pdf_parser.py
-------------------------
Secure PDF text extraction engine using pdfplumber.

Security & Integrity Controls:
    - Safe file descriptor lifecycle management via context manager
    - Encrypted / password-protected PDF detection and explicit rejection
    - Page limit enforcement (MAX_PDF_PAGES = 5) to prevent DoS
    - Preserves headings, spacing, and page ordering for downstream section parsing
    - No execution of PDF JavaScript, actions, or embedded attachments
"""

import logging
from typing import List
import pdfplumber

logger = logging.getLogger(__name__)

# Maximum allowed PDF pages for student resumes (abuse prevention)
MAX_PDF_PAGES: int = 5


def extract_pdf_text(file_path: str) -> str:
    """
    Extract text content from a PDF resume page-by-page.

    Args:
        file_path: Absolute path to the PDF file on disk.

    Returns:
        Extracted raw text string preserving page layout and line breaks.

    Raises:
        ValueError: if the PDF is encrypted, corrupted, exceeds MAX_PDF_PAGES,
                    or cannot be processed.
    """
    try:
        with pdfplumber.open(file_path) as pdf:
            # 1. Encryption check
            is_encrypted = getattr(pdf, "is_encrypted", False)
            if is_encrypted:
                raise ValueError("Password-protected or encrypted PDF files are not supported.")

            # 2. Page count enforcement
            page_count = len(pdf.pages)
            if page_count == 0:
                raise ValueError("The uploaded PDF contains no pages.")
            if page_count > MAX_PDF_PAGES:
                raise ValueError(
                    f"PDF exceeds the maximum allowed length of {MAX_PDF_PAGES} pages "
                    f"(detected: {page_count} pages)."
                )

            # 3. Extract text page by page preserving structure
            extracted_pages: List[str] = []
            for i, page in enumerate(pdf.pages):
                try:
                    # extract_text extracts visible text stream in reading order
                    page_text = page.extract_text(layout=False)
                    if page_text and page_text.strip():
                        extracted_pages.append(page_text.strip())
                except Exception as exc:
                    logger.warning("Error extracting text from PDF page %d in %s: %s", i + 1, file_path, exc)
                    # Continue attempting other pages if one page has font extraction warnings

            if not extracted_pages:
                raise ValueError(
                    "No readable text could be extracted from this PDF. "
                    "The file may be scanned, image-only, or empty."
                )

            return "\n\n".join(extracted_pages)

    except ValueError:
        raise
    except Exception as exc:
        logger.error("Failed to parse PDF file %s: %s", file_path, exc)
        err_msg = str(exc).lower()
        if "password" in err_msg or "encrypt" in err_msg:
            raise ValueError("Password-protected or encrypted PDF files are not supported.") from exc
        raise ValueError("Failed to extract text from PDF. The file may be malformed or corrupted.") from exc

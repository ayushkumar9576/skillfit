"""
app/parsers/__init__.py
-----------------------
Parser engines for extracting structured raw text from resume documents (.pdf, .docx).
"""

from app.parsers.pdf_parser import extract_pdf_text
from app.parsers.docx_parser import extract_docx_text
from app.parsers.resume_parser import (
    extract_resume_text,
    normalize_extracted_text,
    MAX_EXTRACTED_CHARS,
)

__all__ = [
    "extract_pdf_text",
    "extract_docx_text",
    "extract_resume_text",
    "normalize_extracted_text",
    "MAX_EXTRACTED_CHARS",
]

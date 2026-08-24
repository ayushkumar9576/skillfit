"""
app/parsers/resume_parser.py
----------------------------
Dispatcher and text normalizer for the SkillFit Resume Text Extraction Engine.

Responsibilities:
    - Route file to the appropriate parser based on verified extension (.pdf / .docx)
    - Normalize whitespace and line breaks without destroying section headings
    - Enforce character size bounds (MAX_EXTRACTED_CHARS = 200_000)
    - Preserve formatting necessary for downstream AI CV parsing
"""

import os
import re
import logging

from app.parsers.pdf_parser import extract_pdf_text
from app.parsers.docx_parser import extract_docx_text

logger = logging.getLogger(__name__)

# Max character limit for extracted resume text to prevent memory exhaustion
MAX_EXTRACTED_CHARS: int = 200_000


def normalize_extracted_text(text: str) -> str:
    """
    Clean and standardize extracted text while preserving section boundaries.

    Transformation rules:
        - Remove PDF font glyph encoding artifacts like (cid:131), (cid:239), (cid:123), etc.
        - Strip non-printable control characters, zero-width chars, and direction marks
        - Normalize line endings (\\r\\n and \\r to \\n)
        - Standardize unicode spaces (\\u00a0, \\u200b, \\u200e, \\u200f, \\ufeff)
        - Collapse multiple inline horizontal spaces (tabs/spaces) to a single space
        - Strip trailing whitespace from individual lines
        - Collapse 3+ consecutive line breaks to max 2 line breaks (preserves paragraphs & section headers)
        - Preserves all useful resume tokens (emails, phone numbers, github/linkedin URLs, headings, bullet points)

    Args:
        text: Raw text string from parser.

    Returns:
        Clean, structured text string.
    """
    if not text:
        return ""

    # 1. Normalize line endings first
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")

    # 2. Remove PDF font glyph encoding artifacts (e.g. (cid:131), (cid:239))
    # Replacing with a space ensures adjacent tokens do not merge if they lacked a space
    normalized = re.sub(r"\(cid:\d+\)", " ", normalized)

    # 3. Clean zero-width chars, direction marks, byte-order marks, and control codes
    normalized = re.sub(
        r"[\u200b\u200c\u200d\u200e\u200f\ufeff\u0000-\u0008\u000b\u000c\u000e-\u001f]",
        "",
        normalized,
    )

    # 4. Standardize non-breaking spaces
    normalized = normalized.replace("\u00a0", " ")

    # 5. Clean each line: collapse multiple horizontal spaces while preserving line structure
    lines = []
    for line in normalized.split("\n"):
        cleaned_line = re.sub(r"[ \t]+", " ", line).strip()
        lines.append(cleaned_line)

    normalized = "\n".join(lines)

    # 6. Collapse 3+ consecutive line breaks into 2 line breaks (preserves paragraph spacing)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)

    # 7. Final trim
    return normalized.strip()


def extract_resume_text(file_path: str) -> str:
    """
    Dispatch resume file to the appropriate extraction engine and normalize output.

    Args:
        file_path: Absolute path to the resume file.

    Returns:
        Normalized text string extracted from the document.

    Raises:
        ValueError: if the file type is unsupported, extraction fails, or output exceeds limits.
    """
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    if ext == ".pdf":
        raw_text = extract_pdf_text(file_path)
    elif ext == ".docx":
        raw_text = extract_docx_text(file_path)
    else:
        raise ValueError(f"Unsupported file format '{ext}'. Only .pdf and .docx are supported.")

    normalized_text = normalize_extracted_text(raw_text)

    # Validate output length
    if not normalized_text:
        raise ValueError("Extracted text is empty after normalization.")

    if len(normalized_text) > MAX_EXTRACTED_CHARS:
        raise ValueError(
            f"Extracted resume text exceeds the maximum allowed character limit "
            f"({len(normalized_text):,} chars > {MAX_EXTRACTED_CHARS:,} limit)."
        )

    return normalized_text

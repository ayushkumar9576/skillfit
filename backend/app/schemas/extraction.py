"""
app/schemas/extraction.py
-------------------------
Pydantic v2 schemas for SkillFit Phase 3.3 Resume Text Extraction System.

Scope:
    - ExtractionResponse: Outbound summary schema after running extraction.
    - ExtractedTextResponse: Outbound payload containing extracted resume text.

Design rules:
    - No database or file system logic.
    - Strong typing and field documentation for OpenAPI/Swagger generation.
    - `from_attributes=True` enabled for ORM compatibility.
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ExtractionResponse(BaseModel):
    """
    Summary response after running text extraction on an uploaded resume.
    """

    model_config = ConfigDict(from_attributes=True)

    resume_id: uuid.UUID = Field(
        ...,
        description="Unique identifier of the processed resume.",
    )
    character_count: int = Field(
        ...,
        description="Total number of characters extracted and normalized.",
    )
    word_count: int = Field(
        ...,
        description="Total number of words extracted.",
    )
    status: str = Field(
        default="completed",
        description="Status of the extraction job ('completed').",
    )
    message: str = Field(
        default="Text extracted successfully.",
        description="Human-readable result summary.",
    )
    extracted_at: datetime = Field(
        ...,
        description="Timestamp when extraction completed.",
    )


class ExtractedTextResponse(BaseModel):
    """
    Detailed response returning the extracted plain-text content of a resume.
    """

    model_config = ConfigDict(from_attributes=True)

    resume_id: uuid.UUID = Field(
        ...,
        description="Unique identifier of the resume.",
    )
    file_name: str = Field(
        ...,
        description="Original uploaded filename.",
    )
    extracted_text: str = Field(
        ...,
        description="Extracted and normalized raw text content of the resume.",
    )
    character_count: int = Field(
        ...,
        description="Total number of characters in the extracted text.",
    )
    word_count: int = Field(
        ...,
        description="Total number of words in the extracted text.",
    )
    extracted_at: datetime = Field(
        ...,
        description="Timestamp when the text was extracted/updated.",
    )

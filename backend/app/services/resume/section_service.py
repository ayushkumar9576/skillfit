"""
app/services/resume/section_service.py
--------------------------------------
Internal service layer for SkillFit Phase 3.4 – Resume Section Detection.

Responsibilities:
    - Expose pure internal domain functions to parse raw resume text into structured sections.
    - Provide helper to retrieve extracted text from ResumeFile model and parse in-memory.
    - Strictly stateless: performs no database writes or schema modifications.
    - Enforce privacy-preserving logging (logs counts and section names, zero PII).
"""

import logging
import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.models.resume_file import ResumeFile
from app.models.student import Student
from app.services.resume.section_detector import (
    BaseSectionDetector,
    get_section_detector,
)
from app.services.resume.section_types import SectionDetectionResult

logger = logging.getLogger(__name__)


def detect_sections_from_text(
    raw_text: str,
    detector_type: str = "rule_based",
) -> SectionDetectionResult:
    """
    Parse raw resume text into structured canonical sections.

    Args:
        raw_text: Plain text extracted from the resume.
        detector_type: Type of detector to use ('rule_based', etc.).

    Returns:
        SectionDetectionResult containing the 12 canonical sections and metrics.
    """
    detector: BaseSectionDetector = get_section_detector(detector_type)
    result = detector.detect_sections(raw_text)
    return result


def detect_sections_for_resume(
    db: Session,
    resume_id: uuid.UUID,
    user_id: uuid.UUID,
    detector_type: str = "rule_based",
) -> SectionDetectionResult:
    """
    Retrieve extracted text for an owned resume record and detect sections in-memory.

    This function performs no database writes or updates. It is an internal
    helper for downstream analysis engines (Phases 3.7–3.11).

    Args:
        db: Active database session.
        resume_id: UUID of the ResumeFile.
        user_id: UUID of the authenticated user.
        detector_type: Type of detector to execute ('rule_based').

    Returns:
        SectionDetectionResult containing canonical sections and metrics.

    Raises:
        ValueError: If student profile is missing, ownership fails, or text is not extracted.
    """
    student: Optional[Student] = (
        db.query(Student).filter(Student.user_id == user_id).first()
    )
    if not student:
        raise ValueError(f"Student profile not found for user_id={user_id}")

    resume: Optional[ResumeFile] = (
        db.query(ResumeFile).filter(ResumeFile.id == resume_id).first()
    )
    if not resume:
        raise ValueError(f"Resume with id={resume_id} not found.")

    if resume.student_id != student.id:
        raise PermissionError(
            f"User {user_id} does not have ownership of resume {resume_id}."
        )

    if not resume.extracted_text:
        raise ValueError(
            f"Resume {resume_id} has no extracted text. Run text extraction first."
        )

    logger.info(
        "Executing section detection for resume_id=%s, student_id=%s",
        resume.id,
        student.id,
    )

    return detect_sections_from_text(resume.extracted_text, detector_type=detector_type)

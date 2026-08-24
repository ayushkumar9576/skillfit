"""
app/analysis/models/certification_models.py
-------------------------------------------
Certification and credential domain models for SkillFit Phase 3.5.

Consumed by:
    - Phase 3.9: Certification Analysis Engine
    - Phase 3.10: Evidence-Based Skill Engine
    - Phase 3.11: Readiness Engine
    - Phase 3.12: Analysis Persistence
    - Phase 3.13: Public CV APIs
"""

from dataclasses import dataclass, field
from typing import List, Optional

from app.analysis.models.base import AnalysisEvidence


@dataclass
class CertificationEvidence:
    """
    Represents a verified professional certification, license, or accredited course.

    Attributes:
        certification_name: Title of the certification (e.g. 'AWS Certified Solutions Architect').
        issuer: Organization issuing the certification (e.g. 'Amazon Web Services', 'Coursera').
        issue_date: Date or year obtained.
        expiry_date: Expiration date if applicable.
        credential_id: Official license or certification verification ID.
        credential_url: Public credential verification link.
        confidence: Extraction confidence score (0.0 to 1.0).
        evidences: List of supporting resume textual statements.
    """
    certification_name: str
    issuer: str
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None
    credential_id: Optional[str] = None
    credential_url: Optional[str] = None
    confidence: float = 1.0
    evidences: List[AnalysisEvidence] = field(default_factory=list)


@dataclass
class CertificationAnalysisResult:
    """
    Container for all certification findings extracted from a resume.

    Attributes:
        certifications: List of certification evidence objects.
        total_certifications_count: Total count of certifications identified.
    """
    certifications: List[CertificationEvidence] = field(default_factory=list)
    total_certifications_count: int = 0

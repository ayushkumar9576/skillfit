"""
app/api/v1/student_resumes.py
------------------------------
Phase 3.13B Student CV Analysis API — all endpoints under /api/v1/resumes.

Endpoints:
    POST   /api/v1/resumes                            — Upload resume (no pipeline trigger)
    GET    /api/v1/resumes                            — List own resumes
    GET    /api/v1/resumes/{resume_id}                — Get single resume metadata
    DELETE /api/v1/resumes/{resume_id}                — Delete resume (409 if processing)
    GET    /api/v1/resumes/{resume_id}/readiness      — DEPRECATED. Readiness score from snapshot
    GET    /api/v1/resumes/{resume_id}/skills         — DEPRECATED. Skills from snapshot
    GET    /api/v1/resumes/{resume_id}/projects       — DEPRECATED. Projects from snapshot
    GET    /api/v1/resumes/{resume_id}/internships    — DEPRECATED. Internships from snapshot
    GET    /api/v1/resumes/{resume_id}/certifications — DEPRECATED. Certifications from snapshot
    GET    /api/v1/resumes/{resume_id}/sections       — Sections, contact stripped (completed only)
    GET    /api/v1/resumes/{resume_id}/profile        — Canonical CandidateIntelligenceProfile

Architecture (Phase 3.13B):
    All deprecated endpoints now derive their data from CandidateIntelligenceProfile
    loaded via analysis_persistence_service.get_profile(). Zero runtime reads from
    CVAnalysis, StudentSkill, StudentProject, StudentInternship, or Certification.
    Response schemas are unchanged to maintain backward compatibility.

Security:
    - All endpoints require UserRole.student via require_roles().
    - Ownership is enforced: resume.student_id must equal current student.id.
      Violations return 404 (not 403) to prevent IDOR enumeration.
    - Analysis endpoints return 404 with "Analysis not yet available." when
      processing_status != completed — never leak internal state.
    - contact section is always removed from sections response.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles, require_onboarding_completed
from app.core.enums import (
    ConfidenceLevel,
    ComplexityLabel,
    ExperienceStrengthLabel,
    ProcessingStatus,
    ReadinessLevel,
    ResumeType,
    TechnicalDepthLabel,
    UserRole,
)
from app.models.resume_file import ResumeFile
from app.models.student import Student
from app.models.user import User
from app.schemas.resume import ResumeListResponse, ResumeResponse
from app.schemas.resume_analysis import (
    CertificationResponse,
    CertificationsListResponse,
    InternshipResponse,
    InternshipsListResponse,
    ProjectResponse,
    ProjectsListResponse,
    ReadinessResponse,
    SectionsResponse,
    SkillResponse,
    SkillsListResponse,
    _SAFE_SECTION_KEYS,
)
from app.services import resume_service
from app.services.analysis_persistence_service import get_profile, get_latest_snapshot

router = APIRouter(prefix="/api/v1/resumes", tags=["Student — Resume & Analysis"])


# ---------------------------------------------------------------------------
# Internal security helpers
# ---------------------------------------------------------------------------


def _get_student(db: Session, user: User) -> Student:
    """Resolve the Student profile for this User. Returns 403 if not found."""
    student: Student | None = (
        db.query(Student).filter(Student.user_id == user.id).first()
    )
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to student accounts.",
        )
    return student


def _get_owned_resume(db: Session, resume_id: uuid.UUID, student_id: int) -> ResumeFile:
    """
    Load a resume by ID and verify ownership.

    Returns 404 regardless of whether the record doesn't exist or belongs to
    another student — this prevents IDOR enumeration attacks.
    """
    resume: ResumeFile | None = (
        db.query(ResumeFile).filter(ResumeFile.id == resume_id).first()
    )
    if resume is None or resume.student_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found.",
        )
    return resume


def _require_completed(resume: ResumeFile) -> None:
    """Raise 404 if analysis is not yet complete. Never expose internal status."""
    if resume.processing_status != ProcessingStatus.completed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not yet available.",
        )


# ---------------------------------------------------------------------------
# Internal profile helpers — snapshot-derived data mappers
# ---------------------------------------------------------------------------

# VerificationStatus → ConfidenceLevel (for backward-compatible skill responses)
_VERIFICATION_TO_CONFIDENCE = {
    "STRONGLY_VERIFIED": ConfidenceLevel.high,
    "VERIFIED": ConfidenceLevel.high,
    "WEAKLY_VERIFIED": ConfidenceLevel.medium,
    "UNVERIFIED": ConfidenceLevel.low,
}

# VerificationStatus → confidence score (0–100)
_VERIFICATION_TO_SCORE = {
    "STRONGLY_VERIFIED": 95,
    "VERIFIED": 80,
    "WEAKLY_VERIFIED": 55,
    "UNVERIFIED": 20,
}

# DemonstrationLevel → TechnicalDepthLabel
_DEMO_TO_DEPTH = {
    "ARCHITECTED": TechnicalDepthLabel.expert,
    "DESIGNED": TechnicalDepthLabel.advanced,
    "IMPLEMENTED": TechnicalDepthLabel.advanced,
    "USED": TechnicalDepthLabel.intermediate,
    "REFERENCED": TechnicalDepthLabel.basic,
    "CLAIMED": TechnicalDepthLabel.basic,
}

# DemonstrationLevel → ComplexityLabel
_DEMO_TO_COMPLEXITY = {
    "ARCHITECTED": ComplexityLabel.expert,
    "DESIGNED": ComplexityLabel.advanced,
    "IMPLEMENTED": ComplexityLabel.advanced,
    "USED": ComplexityLabel.intermediate,
    "REFERENCED": ComplexityLabel.beginner,
    "CLAIMED": ComplexityLabel.beginner,
}

# OwnershipLevel → ExperienceStrengthLabel
_OWNERSHIP_TO_STRENGTH = {
    "LED": ExperienceStrengthLabel.strong,
    "OWNED": ExperienceStrengthLabel.strong,
    "IMPLEMENTED": ExperienceStrengthLabel.moderate,
    "CONTRIBUTED": ExperienceStrengthLabel.moderate,
    "OBSERVED": ExperienceStrengthLabel.weak,
}


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=ResumeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a resume",
    description=(
        "Upload a PDF or DOCX resume file with a specified type. "
        "Analysis is NOT triggered automatically — an Admin must trigger it via "
        "POST /api/v1/admin/resumes/{id}/analyze. "
        "Returns immediately after file validation and storage."
    ),
)
async def upload_resume(
    file: UploadFile = File(..., description="Resume file (.pdf or .docx, max 10 MB)."),
    resume_type: ResumeType = Form(..., description="'generic' or 'specialized'."),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.student)),
    _: User = Depends(require_onboarding_completed),
) -> ResumeResponse:
    return await resume_service.upload_resume(
        db, file, current_user.id, resume_type
    )


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=ResumeListResponse,
    status_code=status.HTTP_200_OK,
    summary="List own resumes",
    description="Returns all resumes uploaded by the authenticated student, newest first.",
)
def list_resumes(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.student)),
    _: User = Depends(require_onboarding_completed),
) -> ResumeListResponse:
    return resume_service.list_resumes(db, current_user.id)


# ---------------------------------------------------------------------------
# Get single resume
# ---------------------------------------------------------------------------


@router.get(
    "/{resume_id}",
    response_model=ResumeResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a single resume",
    description=(
        "Returns metadata for one resume including processing_status. "
        "Ownership strictly enforced."
    ),
)
def get_resume(
    resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.student)),
    _: User = Depends(require_onboarding_completed),
) -> ResumeResponse:
    student = _get_student(db, current_user)
    resume = _get_owned_resume(db, resume_id, student.id)
    return ResumeResponse.model_validate(resume)


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


@router.delete(
    "/{resume_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a resume",
    description=(
        "Permanently deletes a resume and its analysis data. "
        "Returns 409 Conflict if analysis is currently running."
    ),
)
def delete_resume(
    resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.student)),
    _: User = Depends(require_onboarding_completed),
) -> None:
    resume_service.delete_resume(db, resume_id, current_user.id)


# ---------------------------------------------------------------------------
# Readiness (DEPRECATED — derived from CandidateIntelligenceProfile snapshot)
# ---------------------------------------------------------------------------


@router.get(
    "/{resume_id}/readiness",
    response_model=ReadinessResponse,
    status_code=status.HTTP_200_OK,
    summary="Get readiness analysis",
    description=(
        "DEPRECATED. Use GET /{resume_id}/profile instead. "
        "Returns readiness analysis derived from CandidateIntelligenceProfile snapshot. "
        "Response schema is unchanged for backward compatibility."
    ),
    deprecated=True,
)
def get_readiness(
    resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.student)),
    _: User = Depends(require_onboarding_completed),
) -> ReadinessResponse:
    student = _get_student(db, current_user)
    resume = _get_owned_resume(db, resume_id, student.id)
    _require_completed(resume)

    profile = get_profile(db, resume_id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not yet available.",
        )

    # Derive readiness level from profile findings
    critical_or_high = [f for f in profile.findings if f.severity in ("HIGH", "CRITICAL")]
    gap_findings = [f for f in profile.findings if f.type == "MISSING_SIGNAL"]

    if not critical_or_high and not gap_findings:
        readiness_level = ReadinessLevel.placement_ready
    elif len(critical_or_high) <= 2:
        readiness_level = ReadinessLevel.moderately_ready
    else:
        readiness_level = ReadinessLevel.needs_improvement

    # Build strengths and weaknesses payloads from findings
    strength_items = [
        {"title": f.title, "description": f.description}
        for f in profile.findings
        if f.type == "STRENGTH"
    ]
    weakness_items = [
        {"title": f.title, "description": f.description}
        for f in profile.findings
        if f.type in ("WEAKNESS", "MISSING_SIGNAL")
    ]

    # Build summary from recommendations
    rec_titles = [r.title for r in profile.recommendations[:3]]
    summary_lines = [
        f"Skills verified: {len(profile.skills)} | Technologies: {len(profile.technologies)}",
        f"Projects analyzed: {profile.metadata.total_projects_analyzed} | "
        f"Internships: {profile.metadata.total_internships_analyzed} | "
        f"Certifications: {profile.metadata.total_certifications_analyzed}",
    ]
    if rec_titles:
        summary_lines.append(f"Top recommendations: {', '.join(rec_titles)}")
    summary = "\n".join(summary_lines)

    # Readiness explanation from recommendations
    if profile.recommendations:
        explanation_parts = [r.title for r in profile.recommendations[:3]]
        readiness_explanation = "Focus areas: " + "; ".join(explanation_parts)
    else:
        readiness_explanation = "Profile is strong. No critical gaps identified."

    return ReadinessResponse(
        resume_id=resume_id,
        readiness_level=readiness_level,
        readiness_explanation=readiness_explanation,
        summary=summary,
        strengths={"items": strength_items},
        weaknesses={"items": weakness_items},
        analyzed_at=datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# Skills (DEPRECATED — derived from CandidateIntelligenceProfile snapshot)
# ---------------------------------------------------------------------------


@router.get(
    "/{resume_id}/skills",
    response_model=SkillsListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get skill profiles",
    description=(
        "DEPRECATED. Use GET /{resume_id}/profile instead. "
        "Returns skills derived from CandidateIntelligenceProfile snapshot. "
        "Response schema is unchanged for backward compatibility."
    ),
    deprecated=True,
)
def get_skills(
    resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.student)),
    _: User = Depends(require_onboarding_completed),
) -> SkillsListResponse:
    student = _get_student(db, current_user)
    resume = _get_owned_resume(db, resume_id, student.id)
    _require_completed(resume)

    profile = get_profile(db, resume_id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not yet available.",
        )

    skills = sorted(
        profile.skills,
        key=lambda s: _VERIFICATION_TO_SCORE.get(s.verification_status, 0),
        reverse=True,
    )

    skill_responses = [
        SkillResponse(
            skill_name=s.skill,
            confidence_score=_VERIFICATION_TO_SCORE.get(s.verification_status),
            confidence_level=_VERIFICATION_TO_CONFIDENCE.get(s.verification_status),
            evidence_sources={
                "sources": [
                    {
                        "source_type": e.source.value if hasattr(e.source, "value") else str(e.source),
                        "source_name": e.source_id,
                        "confidence": _VERIFICATION_TO_SCORE.get(s.verification_status, 20) / 100,
                    }
                    for e in s.evidence[:3]
                ]
            },
        )
        for s in skills
    ]

    return SkillsListResponse(
        resume_id=resume_id,
        skills=skill_responses,
        total=len(skill_responses),
    )


# ---------------------------------------------------------------------------
# Projects (DEPRECATED — derived from CandidateIntelligenceProfile snapshot)
# ---------------------------------------------------------------------------


@router.get(
    "/{resume_id}/projects",
    response_model=ProjectsListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get project intelligence",
    description=(
        "DEPRECATED. Use GET /{resume_id}/profile instead. "
        "Returns projects derived from CandidateIntelligenceProfile snapshot. "
        "Response schema is unchanged for backward compatibility."
    ),
    deprecated=True,
)
def get_projects(
    resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.student)),
    _: User = Depends(require_onboarding_completed),
) -> ProjectsListResponse:
    student = _get_student(db, current_user)
    resume = _get_owned_resume(db, resume_id, student.id)
    _require_completed(resume)

    profile = get_profile(db, resume_id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not yet available.",
        )

    # Derive projects from TechnologyIntelligence evidence and metadata
    # Each unique project-sourced evidence item becomes a project entry
    seen_projects: dict = {}
    for tech in profile.technologies:
        for ev in tech.evidence:
            src = ev.source.value if hasattr(ev.source, "value") else str(ev.source)
            if src == "project" and ev.source_id not in seen_projects:
                depth_label = _DEMO_TO_DEPTH.get(tech.demonstration_level)
                complexity_label = _DEMO_TO_COMPLEXITY.get(tech.demonstration_level)
                seen_projects[ev.source_id] = ProjectResponse(
                    project_name=ev.source_id,
                    domain=None,
                    description=ev.quote or f"Project involving {tech.technology}",
                    tech_stack=tech.technology,
                    complexity_score=_VERIFICATION_TO_SCORE.get(
                        profile.skills[0].verification_status if profile.skills else "USED", 60
                    ),
                    complexity_label=complexity_label,
                    technical_depth_score=_VERIFICATION_TO_SCORE.get(
                        profile.skills[0].verification_status if profile.skills else "USED", 60
                    ),
                    technical_depth_label=depth_label,
                    github_url=None,
                )

    project_list = list(seen_projects.values())

    # Fall back to one entry per domain if no project evidence found
    if not project_list:
        for domain in profile.domains:
            project_list.append(ProjectResponse(
                project_name=f"{domain.domain.replace('_', ' ').title()} Project",
                domain=domain.domain,
                description=f"Domain expertise demonstrated in {domain.domain}",
                tech_stack=", ".join(domain.supporting_technologies[:5]),
                complexity_score=None,
                complexity_label=None,
                technical_depth_score=None,
                technical_depth_label=None,
                github_url=None,
            ))

    return ProjectsListResponse(
        resume_id=resume_id,
        projects=project_list,
        total=len(project_list),
    )


# ---------------------------------------------------------------------------
# Internships (DEPRECATED — derived from CandidateIntelligenceProfile snapshot)
# ---------------------------------------------------------------------------


@router.get(
    "/{resume_id}/internships",
    response_model=InternshipsListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get internship intelligence",
    description=(
        "DEPRECATED. Use GET /{resume_id}/profile instead. "
        "Returns internships derived from CandidateIntelligenceProfile snapshot. "
        "Response schema is unchanged for backward compatibility."
    ),
    deprecated=True,
)
def get_internships(
    resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.student)),
    _: User = Depends(require_onboarding_completed),
) -> InternshipsListResponse:
    student = _get_student(db, current_user)
    resume = _get_owned_resume(db, resume_id, student.id)
    _require_completed(resume)

    profile = get_profile(db, resume_id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not yet available.",
        )

    # Derive internships from TechnologyIntelligence with internship evidence
    seen_internships: dict = {}
    for tech in profile.technologies:
        for ev in tech.evidence:
            src = ev.source.value if hasattr(ev.source, "value") else str(ev.source)
            if src == "internship" and ev.source_id not in seen_internships:
                # Derive strength from highest ownership signal for this source
                matching_ownership = [
                    o for o in profile.ownership_signals
                    if any(
                        (e.source.value if hasattr(e.source, "value") else str(e.source)) == "internship"
                        and e.source_id == ev.source_id
                        for e in o.evidence
                    )
                ]
                ownership_level = matching_ownership[0].ownership_level if matching_ownership else "CONTRIBUTED"
                strength_label = _OWNERSHIP_TO_STRENGTH.get(ownership_level, ExperienceStrengthLabel.moderate)

                seen_internships[ev.source_id] = InternshipResponse(
                    company_name=ev.source_id,
                    role="Intern",
                    description=ev.quote,
                    industry=None,
                    technologies_used={"technologies": [tech.technology]},
                    experience_strength_score=_OWNERSHIP_TO_STRENGTH_SCORE.get(ownership_level, 60),
                    experience_strength_label=strength_label,
                )

    # Enrich internships from workplace_exposure
    for exposure in profile.workplace_exposure:
        for ev in exposure.evidence:
            src = ev.source.value if hasattr(ev.source, "value") else str(ev.source)
            if src == "internship" and ev.source_id in seen_internships:
                existing = seen_internships[ev.source_id]
                seen_internships[ev.source_id] = InternshipResponse(
                    company_name=existing.company_name,
                    role=existing.role,
                    description=f"{existing.description or ''} | {exposure.exposure_type}".strip(" |"),
                    industry=exposure.exposure_type if not existing.industry else existing.industry,
                    technologies_used=existing.technologies_used,
                    experience_strength_score=existing.experience_strength_score,
                    experience_strength_label=existing.experience_strength_label,
                )

    internship_list = list(seen_internships.values())

    return InternshipsListResponse(
        resume_id=resume_id,
        internships=internship_list,
        total=len(internship_list),
    )


# ---------------------------------------------------------------------------
# Certifications (DEPRECATED — derived from CandidateIntelligenceProfile snapshot)
# ---------------------------------------------------------------------------


@router.get(
    "/{resume_id}/certifications",
    response_model=CertificationsListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get certification assessments",
    description=(
        "DEPRECATED. Use GET /{resume_id}/profile instead. "
        "Returns certifications derived from CandidateIntelligenceProfile snapshot. "
        "Response schema is unchanged for backward compatibility."
    ),
    deprecated=True,
)
def get_certifications(
    resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.student)),
    _: User = Depends(require_onboarding_completed),
) -> CertificationsListResponse:
    student = _get_student(db, current_user)
    resume = _get_owned_resume(db, resume_id, student.id)
    _require_completed(resume)

    profile = get_profile(db, resume_id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not yet available.",
        )

    cert_responses = [
        CertificationResponse(
            name=c.certification_name,
            issuer=c.category or "Unknown",
            issue_date=None,
            credential_url=None,
            technical_depth_score=None,
            industry_relevance=c.industry_recognition or None,
            industry_value=None,
        )
        for c in profile.certifications
    ]

    return CertificationsListResponse(
        resume_id=resume_id,
        certifications=cert_responses,
        total=len(cert_responses),
    )


# ---------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------


@router.get(
    "/{resume_id}/sections",
    response_model=SectionsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get detected resume sections",
    description=(
        "Returns the raw text sections detected in this resume. "
        "The 'contact' section is always removed to protect PII. "
        "contact_present indicates whether contact information was detected. "
        "Only available after analysis completes."
    ),
)
def get_sections(
    resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.student)),
    _: User = Depends(require_onboarding_completed),
) -> SectionsResponse:
    student = _get_student(db, current_user)
    resume = _get_owned_resume(db, resume_id, student.id)
    _require_completed(resume)

    raw_sections: dict = resume.extracted_sections or {}

    # Check for contact before stripping
    contact_present = "contact" in raw_sections and bool(raw_sections["contact"])

    # Return only safe section keys
    safe_sections = {
        k: v for k, v in raw_sections.items()
        if k in _SAFE_SECTION_KEYS
    }

    return SectionsResponse(
        resume_id=resume_id,
        contact_present=contact_present,
        sections=safe_sections,
    )


# ---------------------------------------------------------------------------
# Profile (Phase 3.13) — canonical endpoint
# ---------------------------------------------------------------------------


@router.get(
    "/{resume_id}/profile",
    status_code=status.HTTP_200_OK,
    summary="Get canonical candidate intelligence profile",
    description=(
        "Returns the full, canonical CandidateIntelligenceProfile from the latest snapshot. "
        "This is the primary intelligence endpoint. All deprecated endpoints derive their "
        "data from this same snapshot."
    ),
)
def get_resume_profile(
    resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.student)),
    _: User = Depends(require_onboarding_completed),
) -> dict:
    student = _get_student(db, current_user)
    resume = _get_owned_resume(db, resume_id, student.id)
    _require_completed(resume)

    snapshot = get_latest_snapshot(db, resume_id)
    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis snapshot not found.",
        )

    # Return the 'profile' dict directly from the snapshot JSON payload
    return snapshot.profile_json.get("profile", {})


# ---------------------------------------------------------------------------
# Module-level constant — used in get_internships internship strength mapping
# ---------------------------------------------------------------------------

_OWNERSHIP_TO_STRENGTH_SCORE = {
    "LED": 85,
    "OWNED": 80,
    "IMPLEMENTED": 65,
    "CONTRIBUTED": 55,
    "OBSERVED": 35,
}

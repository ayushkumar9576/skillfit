"""
app/services/analysis_persistence_service.py
--------------------------------------------
Phase 3.12 – Analysis Persistence Service.

Single-responsibility service that persists all AI analysis results
(Projects, Internships, Certifications, Skills, Readiness) into the
database within the resume processing pipeline.

Design contracts:
    - This service NEVER calls db.commit() or db.rollback().
    - It calls db.add() and db.delete() only.
    - Transaction ownership stays with the pipeline's _set_status(completed)
      call, which commits everything atomically after Stage 9 returns True.
    - All ORM records created here use RecordSource.resume as their source,
      making them the exclusive target of the cleanup DELETE filter.
    - Failures in individual record mapping (e.g. malformed dates) are
      logged and skipped gracefully — they never abort the whole stage.

Re-analysis strategy:
    Before inserting new records for a student, all existing
    RecordSource.resume records for that student are deleted.
    CVAnalysis records for the same resume_id are deleted-then-replaced.
    This guarantees:
        One student → one current analysis state
        No duplicate accumulation
        Manual/imported records are never touched (source filter)
"""

import logging
import uuid
from dataclasses import asdict
from datetime import date, datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.analysis.models.certification_models import (
    CertificationAnalysisResult,
    CertificationIntelligenceReport,
    PROVIDER_HIGH,
    PROVIDER_MEDIUM,
    PROVIDER_LOW,
)
from app.analysis.models.internship_models import (
    InternshipAnalysisResult,
    InternshipIntelligenceReport,
)
from app.analysis.models.project_models import (
    ProjectAnalysisResult,
    ProjectIntelligenceReport,
)
from app.analysis.models.readiness_models import (
    ReadinessAnalysisResult,
    ReadinessLevel as EngineReadinessLevel,
    AnalysisStatus as EngineAnalysisStatus,
)
from app.analysis.models.skill_models import SkillAnalysisResult, SkillProfile
from app.core.enums import (
    AnalysisStatus as DBAnalysisStatus,
    ComplexityLabel,
    ConfidenceLevel,
    ExperienceStrengthLabel,
    ReadinessLevel as DBReadinessLevel,
    RecordSource,
    TechnicalDepthLabel,
)
from app.models.certification import Certification
from app.models.cv_analysis import CVAnalysis
from app.models.student_internship import StudentInternship
from app.models.student_project import StudentProject
from app.models.student_skill import StudentSkill

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Source constant — all AI-generated records use this value
# ---------------------------------------------------------------------------

_AI_SOURCE = RecordSource.resume

# ---------------------------------------------------------------------------
# Score-to-enum buckets
# ---------------------------------------------------------------------------


def _complexity_label(score: float) -> Optional[ComplexityLabel]:
    """Map a 0–100 complexity score to ComplexityLabel."""
    if score >= 86:
        return ComplexityLabel.expert
    if score >= 61:
        return ComplexityLabel.advanced
    if score >= 31:
        return ComplexityLabel.intermediate
    if score > 0:
        return ComplexityLabel.beginner
    return None


def _technical_depth_label(score: float) -> Optional[TechnicalDepthLabel]:
    """Map a 0–100 engineering depth score to TechnicalDepthLabel."""
    if score >= 86:
        return TechnicalDepthLabel.expert
    if score >= 61:
        return TechnicalDepthLabel.advanced
    if score >= 31:
        return TechnicalDepthLabel.intermediate
    if score > 0:
        return TechnicalDepthLabel.basic
    return None


def _experience_strength_label(score: float) -> Optional[ExperienceStrengthLabel]:
    """Map a 0–100 internship technical depth score to ExperienceStrengthLabel."""
    if score >= 71:
        return ExperienceStrengthLabel.strong
    if score >= 41:
        return ExperienceStrengthLabel.moderate
    if score > 0:
        return ExperienceStrengthLabel.weak
    return None


def _confidence_level(level_str: str) -> Optional[ConfidenceLevel]:
    """
    Map analysis confidence_level strings to DB ConfidenceLevel enum.

    Analysis engine uses: "verified", "likely", "uncertain", "cannot_verify"
    DB uses: "high", "medium", "low"
    """
    level_lower = (level_str or "").lower()
    if level_lower == "verified":
        return ConfidenceLevel.high
    if level_lower == "likely":
        return ConfidenceLevel.medium
    return ConfidenceLevel.low


def _readiness_level(engine_level: EngineReadinessLevel) -> Optional[DBReadinessLevel]:
    """Map engine ReadinessLevel to DB ReadinessLevel."""
    mapping = {
        EngineReadinessLevel.HIGH: DBReadinessLevel.placement_ready,
        EngineReadinessLevel.MEDIUM: DBReadinessLevel.moderately_ready,
        EngineReadinessLevel.LOW: DBReadinessLevel.needs_improvement,
    }
    return mapping.get(engine_level)


def _analysis_status(engine_status: EngineAnalysisStatus) -> DBAnalysisStatus:
    """Map engine AnalysisStatus to DB AnalysisStatus."""
    if engine_status == EngineAnalysisStatus.FAILED:
        return DBAnalysisStatus.failed
    return DBAnalysisStatus.completed


# ---------------------------------------------------------------------------
# Certification date parser
# ---------------------------------------------------------------------------

_MONTH_ABBR = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

_MONTH_FULL = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
}


def _parse_cert_date(raw: Optional[str]) -> Optional[date]:
    """
    Parse a free-text certification date string into a Python date object.

    Supported formats (in priority order):
        "2024-06-15"   → date(2024, 6, 15)
        "2024-06"      → date(2024, 6, 1)
        "2024"         → date(2024, 1, 1)
        "Jun 2024"     → date(2024, 6, 1)
        "June 2024"    → date(2024, 6, 1)
        "15 Jun 2024"  → date(2024, 6, 15)
        None / ""      → None
        unparseable    → None (logged)
    """
    if not raw:
        return None

    text = raw.strip()
    if not text:
        return None

    # 1. ISO date: YYYY-MM-DD
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        pass

    # 2. ISO month: YYYY-MM
    try:
        return datetime.strptime(text, "%Y-%m").date().replace(day=1)
    except ValueError:
        pass

    # 3. Year only: YYYY
    if text.isdigit() and len(text) == 4:
        try:
            return date(int(text), 1, 1)
        except ValueError:
            pass

    # 4. Month Year short/full: "Jan 2024" / "January 2024"
    parts = text.split()
    if len(parts) == 2:
        month_word, year_str = parts
        year_str = year_str.strip()
        if year_str.isdigit() and len(year_str) == 4:
            year = int(year_str)
            month_low = month_word.lower()
            month = _MONTH_ABBR.get(month_low) or _MONTH_FULL.get(month_low)
            if month:
                try:
                    return date(year, month, 1)
                except ValueError:
                    pass

    # 5. Day Month Year: "15 Jun 2024"
    if len(parts) == 3:
        day_str, month_word, year_str = parts
        if day_str.isdigit() and year_str.isdigit() and len(year_str) == 4:
            month_low = month_word.lower()
            month = _MONTH_ABBR.get(month_low) or _MONTH_FULL.get(month_low)
            if month:
                try:
                    return date(int(year_str), month, int(day_str))
                except ValueError:
                    pass

    logger.warning("Certification date unparseable, storing NULL: %r", raw)
    return None


# ---------------------------------------------------------------------------
# Internal mappers
# ---------------------------------------------------------------------------


def _build_project_summary(report: ProjectIntelligenceReport) -> str:
    """Build a plain-text project description from available report fields."""
    parts = []
    if report.understanding.purpose:
        parts.append(report.understanding.purpose)
    if report.understanding.problem_solved and report.understanding.problem_solved not in parts:
        parts.append(report.understanding.problem_solved)
    return " ".join(parts) or report.project_title or "No description available."


def _build_skills_demonstrated(report: ProjectIntelligenceReport) -> dict:
    """Serialize skill evidence map to JSONB-compatible dict."""
    se = report.skill_evidence
    return {
        "verified": list(se.verified),
        "demonstrated": list(se.demonstrated),
        "claimed": list(se.claimed),
        "unverified": list(se.unverified),
    }


def _build_tech_stack(report: ProjectIntelligenceReport) -> str:
    """Build comma-separated tech stack string, max 500 chars."""
    if report.source_project and report.source_project.technologies:
        raw = ", ".join(report.source_project.technologies)
    else:
        # Fall back to tech from intelligence report
        tech_names = [tu.technology for tu in report.technology_usage if tu.technology]
        raw = ", ".join(tech_names)

    if not raw:
        raw = "Not specified"

    # Enforce String(500) limit
    if len(raw) > 500:
        raw = raw[:497] + "..."
    return raw


def _build_evidence_text(report: ProjectIntelligenceReport) -> Optional[str]:
    """Build newline-joined evidence from project highlights."""
    if report.source_project and report.source_project.highlights:
        return "\n".join(report.source_project.highlights)
    return None


def _map_project(student_id: int, report: ProjectIntelligenceReport) -> StudentProject:
    """Map one ProjectIntelligenceReport → StudentProject ORM object."""
    complexity_score = report.complexity.overall.score
    depth_score = report.engineering_depth.score
    sp = report.source_project

    return StudentProject(
        student_id=student_id,
        project_name=(sp.title if sp and sp.title else report.project_title or "Untitled Project")[:255],
        domain=(report.understanding.domain or None),
        description=_build_project_summary(report),
        tech_stack=_build_tech_stack(report),
        complexity_score=round(complexity_score) if complexity_score else None,
        complexity_label=_complexity_label(complexity_score),
        technical_depth_score=round(depth_score) if depth_score else None,
        technical_depth_label=_technical_depth_label(depth_score),
        skills_demonstrated=_build_skills_demonstrated(report),
        evidence=_build_evidence_text(report),
        github_url=(sp.project_url if sp else None),
        source=_AI_SOURCE,
    )


def _map_internship(student_id: int, report: InternshipIntelligenceReport) -> StudentInternship:
    """Map one InternshipIntelligenceReport → StudentInternship ORM object."""
    si = report.source_internship
    depth_score = report.technical_depth.score

    return StudentInternship(
        student_id=student_id,
        company_name=(si.organization if si else report.internship_organization or "Unknown")[:255],
        role=(si.role if si else report.internship_role or "Intern")[:255],
        description=(si.description if si else None),
        industry=(report.understanding.domain or None),
        technologies_used={"technologies": list(si.technologies_used) if si else []},
        experience_strength_score=round(depth_score) if depth_score else None,
        experience_strength_label=_experience_strength_label(depth_score),
        source=_AI_SOURCE,
    )


def _map_certification(
    student_id: int, report: CertificationIntelligenceReport
) -> Optional[Certification]:
    """Map one CertificationIntelligenceReport → Certification ORM object."""
    sc = report.source_certification
    if not sc:
        logger.warning(
            "CertificationIntelligenceReport has no source_certification — skipping."
        )
        return None

    cert = Certification(
        student_id=student_id,
        name=report.certification_name[:255] or sc.certification_name[:255],
        issuer=sc.issuer[:150] if sc.issuer else "Unknown",
        issue_date=_parse_cert_date(sc.issue_date),
        credential_url=sc.credential_url,
        technical_depth_score=round(report.certification_recognition.score) if report.certification_recognition.score else None,
        industry_relevance=(report.industry_relevance.reasoning or None)[:255]
        if report.industry_relevance.reasoning else None,
        industry_value=round(report.industry_relevance.score) if report.industry_relevance.score else None,
        source=_AI_SOURCE,
    )
    return cert


def _map_skill(student_id: int, profile: SkillProfile) -> StudentSkill:
    """Map one SkillProfile → StudentSkill ORM object."""
    # confidence_score: float 0.0–1.0 → int 0–100
    conf_int = round(profile.confidence_score * 100)

    # evidence_sources JSONB
    sources_payload = {
        "sources": [
            {
                "source_type": src.source_type,
                "source_name": src.source_name,
                "confidence": round(src.source_confidence, 4),
            }
            for src in profile.evidences
        ]
    }

    return StudentSkill(
        student_id=student_id,
        skill_name=profile.skill_name[:100],
        confidence_score=conf_int,
        confidence_level=_confidence_level(profile.confidence_level),
        evidence_sources=sources_payload,
        source=_AI_SOURCE,
    )


def _build_readiness_summary(result: ReadinessAnalysisResult) -> str:
    """Build a human-readable summary string for cv_analysis.summary."""
    sb = result.score_breakdown
    lines = [
        f"Readiness Score: {result.readiness_score:.1f}/100 "
        f"({result.readiness_level.value})",
        f"Projects: {sb.project_score:.1f} | "
        f"Internships: {sb.internship_score:.1f} | "
        f"Certifications: {sb.certification_score:.1f} | "
        f"Skills: {sb.skill_score:.1f}",
        f"Overall Confidence: {result.overall_confidence:.2f}",
    ]
    return "\n".join(lines)


def _build_readiness_explanation(result: ReadinessAnalysisResult) -> str:
    """Build a readiness explanation string for cv_analysis.readiness_explanation."""
    parts = []
    if result.strengths:
        strength_titles = ", ".join(s.title for s in result.strengths[:3])
        parts.append(f"Strengths: {strength_titles}.")
    if result.gaps:
        gap_titles = ", ".join(g.title for g in result.gaps[:3])
        parts.append(f"Gaps: {gap_titles}.")
    if not parts:
        return "No specific strengths or gaps identified."
    return " ".join(parts)


def _map_cv_analysis(
    student_id: int,
    resume_id: uuid.UUID,
    result: ReadinessAnalysisResult,
) -> CVAnalysis:
    """Map ReadinessAnalysisResult → CVAnalysis ORM object."""
    strengths_payload = {"items": [s.to_dict() for s in result.strengths]}
    weaknesses_payload = {"items": [g.to_dict() for g in result.gaps]}

    return CVAnalysis(
        student_id=student_id,
        resume_id=resume_id,
        analysis_status=_analysis_status(result.analysis_status),
        summary=_build_readiness_summary(result),
        strengths=strengths_payload,
        weaknesses=weaknesses_payload,
        readiness_level=_readiness_level(result.readiness_level),
        readiness_explanation=_build_readiness_explanation(result),
        analysis_version=result.engine_version,
        analyzed_at=result.generated_at,
    )


# ---------------------------------------------------------------------------
# Cleanup helpers
# ---------------------------------------------------------------------------


def _delete_ai_records(db: Session, student_id: int) -> None:
    """
    Delete all AI-generated (source='resume') analysis records for a student.

    Order matters: child tables before parent-like tables to avoid FK conflicts
    if any are added in future. Current schema has no cross-table FKs between
    these four tables, so order is for clarity only.
    """
    deleted_projects = (
        db.query(StudentProject)
        .filter(StudentProject.student_id == student_id, StudentProject.source == _AI_SOURCE)
        .delete(synchronize_session=False)
    )
    deleted_internships = (
        db.query(StudentInternship)
        .filter(StudentInternship.student_id == student_id, StudentInternship.source == _AI_SOURCE)
        .delete(synchronize_session=False)
    )
    deleted_certs = (
        db.query(Certification)
        .filter(Certification.student_id == student_id, Certification.source == _AI_SOURCE)
        .delete(synchronize_session=False)
    )
    deleted_skills = (
        db.query(StudentSkill)
        .filter(StudentSkill.student_id == student_id, StudentSkill.source == _AI_SOURCE)
        .delete(synchronize_session=False)
    )
    logger.info(
        "Cleared prior AI analysis for student_id=%s: "
        "projects=%d internships=%d certs=%d skills=%d",
        student_id,
        deleted_projects,
        deleted_internships,
        deleted_certs,
        deleted_skills,
    )


def _delete_cv_analysis(db: Session, resume_id: uuid.UUID) -> None:
    """
    Delete any existing CVAnalysis row for this resume_id.

    CVAnalysis has UNIQUE(resume_id). Re-analysis of the same resume
    requires deleting the prior row before inserting the new one.
    """
    deleted = (
        db.query(CVAnalysis)
        .filter(CVAnalysis.resume_id == resume_id)
        .delete(synchronize_session=False)
    )
    if deleted:
        logger.info(
            "Deleted existing CVAnalysis for resume_id=%s (re-analysis)", resume_id
        )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def persist_analysis_results(
    db: Session,
    student_id: int,
    resume_id: uuid.UUID,
    project_result: Optional[ProjectAnalysisResult],
    internship_result: Optional[InternshipAnalysisResult],
    certification_result: Optional[CertificationAnalysisResult],
    skill_result: Optional[SkillAnalysisResult],
    readiness_result: Optional[ReadinessAnalysisResult],
) -> bool:
    """
    Persist all analysis engine outputs into the database.

    This function is the single public entry point for Phase 3.12 persistence.
    It is called from _stage_persist_analysis in resume_pipeline.py.

    Transaction contract:
        - Does NOT commit or rollback.
        - Calls db.add() and bulk delete only.
        - The pipeline's _set_status(completed) commit at line 589 atomically
          persists everything this function enqueued.

    Args:
        db:                  Active SQLAlchemy session (no autocommit).
        student_id:          Integer PK of the Student record.
        resume_id:           UUID PK of the ResumeFile record.
        project_result:      Output of Phase 3.7. May be None.
        internship_result:   Output of Phase 3.8. May be None.
        certification_result: Output of Phase 3.9. May be None.
        skill_result:        Output of Phase 3.10. May be None.
        readiness_result:    Output of Phase 3.11. May be None.

    Returns:
        True on success, False if a non-recoverable error occurs.
    """
    try:
        # ----------------------------------------------------------------
        # 1. Delete all prior AI-generated records for this student
        # ----------------------------------------------------------------
        _delete_ai_records(db, student_id)
        _delete_cv_analysis(db, resume_id)

        # ----------------------------------------------------------------
        # 2. Projects
        # ----------------------------------------------------------------
        project_count = 0
        if project_result and project_result.reports:
            for report in project_result.reports:
                try:
                    orm_obj = _map_project(student_id, report)
                    db.add(orm_obj)
                    project_count += 1
                except Exception as exc:
                    logger.warning(
                        "Skipping project persistence for %r: %s",
                        getattr(getattr(report, "source_project", None), "title", "?"),
                        exc,
                    )
        logger.info(
            "Queued %d project record(s) for student_id=%s", project_count, student_id
        )

        # ----------------------------------------------------------------
        # 3. Internships
        # ----------------------------------------------------------------
        internship_count = 0
        if internship_result and internship_result.reports:
            for report in internship_result.reports:
                try:
                    orm_obj = _map_internship(student_id, report)
                    db.add(orm_obj)
                    internship_count += 1
                except Exception as exc:
                    logger.warning(
                        "Skipping internship persistence for %r: %s",
                        getattr(report, "internship_role", "?"),
                        exc,
                    )
        logger.info(
            "Queued %d internship record(s) for student_id=%s",
            internship_count,
            student_id,
        )

        # ----------------------------------------------------------------
        # 4. Certifications
        # ----------------------------------------------------------------
        cert_count = 0
        if certification_result and certification_result.reports:
            for report in certification_result.reports:
                try:
                    orm_obj = _map_certification(student_id, report)
                    if orm_obj:
                        db.add(orm_obj)
                        cert_count += 1
                except Exception as exc:
                    logger.warning(
                        "Skipping certification persistence for %r: %s",
                        getattr(report, "certification_name", "?"),
                        exc,
                    )
        logger.info(
            "Queued %d certification record(s) for student_id=%s",
            cert_count,
            student_id,
        )

        # ----------------------------------------------------------------
        # 5. Skills
        # ----------------------------------------------------------------
        skill_count = 0
        if skill_result and skill_result.skills:
            for profile in skill_result.skills:
                try:
                    orm_obj = _map_skill(student_id, profile)
                    db.add(orm_obj)
                    skill_count += 1
                except Exception as exc:
                    logger.warning(
                        "Skipping skill persistence for %r: %s",
                        getattr(profile, "skill_name", "?"),
                        exc,
                    )
        logger.info(
            "Queued %d skill record(s) for student_id=%s", skill_count, student_id
        )

        # ----------------------------------------------------------------
        # 6. CV Analysis (Readiness)
        # ----------------------------------------------------------------
        if readiness_result:
            try:
                orm_obj = _map_cv_analysis(student_id, resume_id, readiness_result)
                db.add(orm_obj)
                logger.info(
                    "Queued CVAnalysis for student_id=%s resume_id=%s "
                    "readiness=%.1f",
                    student_id,
                    resume_id,
                    readiness_result.readiness_score,
                )
            except Exception as exc:
                logger.error(
                    "Failed to map CVAnalysis for student_id=%s resume_id=%s: %s",
                    student_id,
                    resume_id,
                    exc,
                )
                # CVAnalysis is the primary output of this stage.
                # Failure here is non-recoverable for this stage.
                return False

        # ----------------------------------------------------------------
        # 7. Flush to detect constraint errors before pipeline commits
        # ----------------------------------------------------------------
        db.flush()
        logger.info(
            "Analysis persistence flush successful: student_id=%s resume_id=%s "
            "[projects=%d internships=%d certs=%d skills=%d readiness=%s]",
            student_id,
            resume_id,
            project_count,
            internship_count,
            cert_count,
            skill_count,
            "YES" if readiness_result else "NO",
        )
        return True

    except Exception as exc:
        logger.error(
            "Analysis persistence FAILED for student_id=%s resume_id=%s: %s",
            student_id,
            resume_id,
            exc,
            exc_info=True,
        )
        return False

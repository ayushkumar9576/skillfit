"""
app/services/resume_pipeline.py
--------------------------------
Internal Resume Processing Pipeline Orchestrator — SkillFit Phase 3.14.

Purpose:
    Single authoritative orchestration point for all automated resume processing.
    Called as a FastAPI BackgroundTask immediately after a resume file is stored.
    Students never interact with this module directly.

Pipeline stages (all ACTIVE):
    1. [3.3]  Text extraction        — extraction_service
    2. [3.4]  Section detection      — section_service
    3. [3.7]  Project analysis       — ProjectAnalysisEngine → raw intelligence dict
    4. [3.8]  Internship analysis    — InternshipAnalysisEngine → raw intelligence dict
    5. [3.9]  Certification analysis — CertificationAnalysisEngine → raw intelligence dict
    6. [3.10] Intelligence profile   — CandidateIntelligenceAggregator.build() +
                                       SkillVerificationEngine → _temp_intelligence_profile
    7. [3.11] Readiness engine       — ReadinessEngine consumes _temp_intelligence_profile
    8. [3.12] Analysis persistence   — CandidateIntelligenceSnapshot written to DB

Design contract:
    - This module owns NO HTTP logic (no FastAPI imports used for routing).
    - It is the only module that calls extraction_service and section_service
      after upload — no other code path should trigger pipeline stages.
    - Each stage updates `processing_status` on the ResumeFile record so that
      future polling endpoints can reflect real progress.
    - All exceptions are caught and logged; the pipeline NEVER propagates
      unhandled exceptions into the HTTP request context.
    - The DB session used here is a new, independently-opened session — not the
      one used by the upload request — because background tasks run after the
      HTTP response is sent and the request-scoped session is closed.

Security:
    - No student-facing inputs are accepted.
    - ResumeFile record is loaded by UUID (primary key); ownership is implicit.
    - Stages 3-5 make authenticated outbound LLM calls. The API key is read
      only by the provider layer and is never logged; if it is absent/invalid
      the stage skips gracefully (LLMConfigurationError is caught) rather than
      failing the resume.
"""

import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import asdict
import json
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.core.enums import ProcessingStatus
from app.db.database import SessionLocal
from app.models.resume_file import ResumeFile
from app.services import extraction_service
from app.services.resume.section_service import detect_sections_from_text

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Debug output helper — lazy, never runs at import time (Bug #4 fix)
# ---------------------------------------------------------------------------


def _get_debug_dir() -> Path:
    """
    Return (and create) the debug output directory only when actually needed.

    Calling mkdir() at module level caused startup crashes on any deployment
    where the working directory is read-only (Docker, serverless, CI).
    This helper is called lazily inside individual stages instead.
    """
    debug_dir = Path("DEBUG/results")
    debug_dir.mkdir(parents=True, exist_ok=True)
    return debug_dir


# ---------------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------------


def _load_resume(db: Session, resume_id: uuid.UUID) -> ResumeFile | None:
    """
    Load a ResumeFile record by primary key.

    Returns None if the record no longer exists (e.g. deleted between upload
    and pipeline execution — this is a safe no-op).
    """
    return db.query(ResumeFile).filter(ResumeFile.id == resume_id).first()


def _set_status(db: Session, resume: ResumeFile, status: ProcessingStatus) -> None:
    """
    Persist a new processing_status on the resume record.

    Uses a narrow update rather than a full model flush to minimize lock time.
    """
    resume.processing_status = status
    resume.updated_at = datetime.now(timezone.utc)
    try:
        db.commit()
        logger.info(
            "Pipeline status update: resume_id=%s status=%s",
            resume.id,
            status.value,
        )
    except Exception as exc:
        db.rollback()
        logger.error(
            "Failed to persist pipeline status=%s for resume_id=%s: %s",
            status.value,
            resume.id,
            exc,
        )


# ---------------------------------------------------------------------------
# Stage Implementations
# ---------------------------------------------------------------------------


def _stage_extract_text(db: Session, resume: ResumeFile) -> bool:
    """
    Stage 1 — Text Extraction (Phase 3.3).

    Calls the existing extraction_service logic directly (no HTTP involved).
    Populates resume.extracted_text and commits.

    Returns:
        True if extraction succeeded; False on any error.
    """
    try:
        extraction_service.extract_resume_internal(db, resume)
        logger.info(
            "Pipeline Stage 1 (extraction) completed: resume_id=%s chars=%d",
            resume.id,
            len(resume.extracted_text or ""),
        )
        return True
    except Exception as exc:
        logger.error(
            "Pipeline Stage 1 (extraction) FAILED: resume_id=%s error=%s",
            resume.id,
            exc,
        )
        return False


def _stage_detect_sections(db: Session, resume: ResumeFile) -> bool:
    """
    Stage 2 — Section Detection (Phase 3.4).

    Runs the rule-based section detector on the already-extracted text.
    Result is currently not persisted (Phase 3.12 will handle persistence).

    Returns:
        True if detection completed; False if text is missing or detection fails.
    """
    if not resume.extracted_text:
        logger.warning(
            "Pipeline Stage 2 (section detection) skipped — no extracted text: resume_id=%s",
            resume.id,
        )
        return False
    try:
        result = detect_sections_from_text(resume.extracted_text, detector_type="rule_based")
        resume.extracted_sections = result.sections
        setattr(resume, "_temp_sections_result", result.sections)
        logger.info(
            "Pipeline Stage 2 (section detection) completed: resume_id=%s "
            "sections_detected=%d confidence=%.2f",
            resume.id,
            result.metrics.detected_sections_count,
            result.metrics.parsing_confidence,
        )
        return True
    except Exception as exc:
        logger.error(
            "Pipeline Stage 2 (section detection) FAILED: resume_id=%s error=%s",
            resume.id,
            exc,
        )
        return False


# ---------------------------------------------------------------------------
# Stage 3 — Project Analysis (Phase 3.7, ACTIVE)
# ---------------------------------------------------------------------------


def _stage_project_analysis(db: Session, resume: ResumeFile) -> bool:
    """
    Stage 3 — Project Analysis Engine (Phase 3.7).

    Calls ProjectAnalysisEngine.analyze() which returns a dict containing
    TechnologyIntelligence, CompetencyIntelligence, OwnershipIntelligence,
    EngineeringSignal, and Finding objects ready to be fed into the
    CandidateIntelligenceAggregator in Stage 6.

    Best-effort / non-fatal: a failure here must NOT fail the whole resume.

    Returns:
        Always True (non-fatal).
    """
    if not resume.extracted_text:
        logger.warning(
            "Pipeline Stage 3 (project analysis) skipped — no extracted text: resume_id=%s",
            resume.id,
        )
        return True

    from app.analysis.engines.project_analysis_engine import ProjectAnalysisEngine
    from app.services.llm.exceptions import LLMConfigurationError

    try:
        engine = ProjectAnalysisEngine()
        # Returns dict: {technologies, competencies, ownership_signals, engineering_signals, findings}
        result_dict: Dict[str, Any] = engine.analyze(
            resume_id=str(resume.id), raw_text=resume.extracted_text
        )
        # Store the raw intelligence dict for Stage 6 (CandidateIntelligenceAggregator)
        setattr(resume, "_temp_project_dict", result_dict)
        logger.info(
            "Pipeline Stage 3 (project analysis) completed: resume_id=%s "
            "technologies=%d competencies=%d findings=%d",
            resume.id,
            len(result_dict.get("technologies", [])),
            len(result_dict.get("competencies", [])),
            len(result_dict.get("findings", [])),
        )
        return True
    except LLMConfigurationError as exc:
        logger.warning(
            "Pipeline Stage 3 (project analysis) skipped — LLM not configured "
            "(resume_id=%s): %s",
            resume.id, exc,
        )
        return True
    except Exception as exc:
        logger.error(
            "Pipeline Stage 3 (project analysis) error (non-fatal): resume_id=%s %s: %s",
            resume.id, type(exc).__name__, exc,
        )
        return True


def _stage_internship_analysis(_db: Session, resume: ResumeFile) -> bool:
    """
    Stage 4 — Internship Analysis Engine (Phase 3.8).

    Calls InternshipAnalysisEngine.analyze() and stores the raw intelligence
    dict as _temp_internship_dict for Stage 6 (CandidateIntelligenceAggregator).
    Best-effort / non-fatal.
    """
    if not resume.extracted_text:
        logger.warning(
            "Pipeline Stage 4 (internship analysis) skipped — no extracted text: resume_id=%s",
            resume.id,
        )
        return True

    from app.analysis.engines.internship_analysis_engine import InternshipAnalysisEngine
    from app.services.resume.internship_extractor import get_internship_extractor
    from app.services.llm.exceptions import LLMConfigurationError

    try:
        extractor = get_internship_extractor("rule_based")
        extraction_result = extractor.extract(resume.extracted_text)

        engine = InternshipAnalysisEngine()
        result = engine.analyze(
            resume_id=str(resume.id), internships=extraction_result.internships
        )
        setattr(resume, "_temp_internship_result", result)
        logger.info(
            "Pipeline Stage 4 (internship analysis) completed: resume_id=%s "
            "technologies=%d competencies=%d findings=%d",
            resume.id,
            len(result.technologies),
            len(result.competencies),
            len(result.findings),
        )
        return True
    except LLMConfigurationError as exc:
        logger.warning(
            "Pipeline Stage 4 (internship analysis) skipped — LLM not configured "
            "(resume_id=%s): %s",
            resume.id, exc,
        )
        return True
    except Exception as exc:
        logger.error(
            "Pipeline Stage 4 (internship analysis) error (non-fatal): resume_id=%s %s: %s",
            resume.id, type(exc).__name__, exc,
        )
        return True


def _stage_certification_analysis(_db: Session, resume: ResumeFile) -> bool:
    """
    Stage 5 — Certification Analysis Engine (Phase 3.9).

    Calls CertificationAnalysisEngine.analyze() and stores the raw intelligence
    dict as _temp_certification_dict for Stage 6 (CandidateIntelligenceAggregator).
    Best-effort / non-fatal.
    """
    if not resume.extracted_text:
        logger.warning(
            "Pipeline Stage 5 (certification analysis) skipped — no extracted text: resume_id=%s",
            resume.id,
        )
        return True

    from app.analysis.engines.certification_analysis_engine import CertificationAnalysisEngine
    from app.services.resume.certification_extractor import get_certification_extractor
    from app.services.llm.exceptions import LLMConfigurationError

    try:
        extractor = get_certification_extractor()
        extraction_result = extractor.extract(resume.extracted_text)

        engine = CertificationAnalysisEngine()
        result = engine.analyze(
            resume_id=str(resume.id), certifications=extraction_result.certifications
        )
        setattr(resume, "_temp_certification_result", result)
        logger.info(
            "Pipeline Stage 5 (certification analysis) completed: resume_id=%s "
            "certifications=%d intelligence=%d",
            resume.id,
            len(extraction_result.certifications),
            len(result.intelligence),
        )
        return True
    except LLMConfigurationError as exc:
        logger.warning(
            "Pipeline Stage 5 (certification analysis) skipped — LLM not configured "
            "(resume_id=%s): %s",
            resume.id, exc,
        )
        return True
    except Exception as exc:
        logger.error(
            "Pipeline Stage 5 (certification analysis) error (non-fatal): resume_id=%s %s: %s",
            resume.id, type(exc).__name__, exc,
        )
        return True


def _stage_build_intelligence_profile(_db: Session, resume: ResumeFile) -> bool:
    """
    Stage 6 — Build CandidateIntelligenceProfile (Phase 3.10).

    Feeds all intelligence dicts from Stages 3-5 into
    CandidateIntelligenceAggregator, then runs SkillVerificationEngine
    on the resulting profile to populate verified skills.

    Stores the finished profile as _temp_intelligence_profile so that
    Stage 7 (ReadinessEngine) and Stage 8 (persistence) can consume it.

    This is a CRITICAL stage — returns False on failure to abort the pipeline.
    """
    try:
        from app.analysis.engines.candidate_intelligence import CandidateIntelligenceAggregator
        from app.analysis.engines.skill_analysis_engine import SkillVerificationEngine
        from app.analysis.models.candidate_profile import ProfileMetadata

        agg = CandidateIntelligenceAggregator()

        # ── Feed project intelligence ─────────────────────────────────────
        project_dict: Dict[str, Any] = getattr(resume, "_temp_project_dict", {}) or {}
        agg.add_technologies(project_dict.get("technologies", []))
        agg.add_competencies(project_dict.get("competencies", []))
        agg.add_ownership_signals(project_dict.get("ownership_signals", []))
        agg.add_engineering_signals(project_dict.get("engineering_signals", []))
        agg.add_findings(project_dict.get("findings", []))
        agg.add_project_sophistication(project_dict.get("project_sophistication", []))

        # ── Feed internship intelligence ──────────────────────────────────
        internship_result = getattr(resume, "_temp_internship_result", None)
        if internship_result:
            agg.add_technologies(internship_result.technologies)
            agg.add_competencies(internship_result.competencies)
            agg.add_ownership_signals(internship_result.ownership_signals)
            agg.add_engineering_signals(internship_result.engineering_signals)
            agg.add_workplace_exposure(internship_result.workplace_exposure)
            agg.add_findings(internship_result.findings)

        # ── Feed certification intelligence ───────────────────────────────
        cert_result = getattr(resume, "_temp_certification_result", None)
        if cert_result:
            agg.add_certifications(cert_result.intelligence)

        # ── Build the profile ────────────────────────────────────────────
        profile = agg.build()

        # ── Run skill verification over the assembled profile ─────────────
        temp_sections = getattr(resume, "_temp_sections_result", {}) or {}
        self_reported_raw = temp_sections.get("skills", "")
        self_reported_list = [
            s.strip() for s in (self_reported_raw or "").split(",") if s.strip()
        ] if self_reported_raw else []

        skill_engine = SkillVerificationEngine()
        verified_skills = skill_engine.verify(profile, self_reported_skills=self_reported_list)
        # Attach verified skills back onto the profile (profile.skills is already
        # populated by aggregator; override with the richer verification pass)
        profile.skills = verified_skills

        # ── Attach metadata ───────────────────────────────────────────────
        profile.metadata = ProfileMetadata(
            total_projects_analyzed=len(project_dict.get("technologies", [])),
            total_internships_analyzed=internship_result.total_internships_count if internship_result else 0,
            total_certifications_analyzed=cert_result.total_certifications_count if cert_result else 0,
            analysis_version="3.14.0",
        )

        # ── Store for downstream stages ───────────────────────────────────
        setattr(resume, "_temp_intelligence_profile", profile)

        logger.info(
            "Pipeline Stage 6 (intelligence profile) completed: resume_id=%s "
            "skills=%d technologies=%d domains=%d findings=%d",
            resume.id,
            len(profile.skills),
            len(profile.technologies),
            len(profile.domains),
            len(profile.findings),
        )
        return True
    except Exception as exc:
        logger.error(
            "Pipeline Stage 6 (intelligence profile build) FAILED: resume_id=%s error=%s",
            resume.id, exc,
            exc_info=True,
        )
        return False


def _stage_readiness_engine(db: Session, resume: ResumeFile) -> bool:
    """
    Stage 7 — Readiness Engine (Phase 3 Final Hardening).
    Derives readiness from CandidateIntelligenceProfile — not from old result types.
    """
    try:
        from app.analysis.engines.readiness_engine import ReadinessEngine

        # The CandidateIntelligenceProfile is set by Stage 6 (skill analysis)
        profile = getattr(resume, "_temp_intelligence_profile", None)
        if profile is None:
            logger.warning(
                "Pipeline Stage 7 (readiness) skipped — no intelligence profile available."
            )
            return True

        engine = ReadinessEngine()
        result = engine.analyze(
            resume_id=str(resume.id),
            profile=profile,
        )

        setattr(resume, "_temp_readiness_result", result)
        logger.info(
            "Pipeline Stage 7 (readiness) complete: resume_id=%s score=%.1f level=%s",
            resume.id, result.readiness_score, result.readiness_level.value,
        )
        return True
    except Exception as exc:
        logger.error(
            "Pipeline Stage 7 (readiness analysis) FAILED: resume_id=%s error=%s",
            resume.id, exc,
        )
        return False



def _stage_persist_analysis(db: Session, resume: ResumeFile) -> bool:
    """
    Stage 8 — Analysis Persistence (Phase 3.12).

    Persists all analysis engine outputs into the database within a single
    transaction boundary. This stage calls db.add() only — it does NOT
    commit. The commit happens in _set_status(completed) immediately after
    all stages succeed, making persistence atomic with the status update.

    Returns:
        True if persistence was staged successfully.
        False if a non-recoverable error occurs (pipeline marks as failed).
    """
    from app.services.analysis_persistence_service import persist_analysis_results

    project_result = getattr(resume, "_temp_project_result", None)
    internship_result = getattr(resume, "_temp_internship_result", None)
    certification_result = getattr(resume, "_temp_certification_result", None)
    skill_result = getattr(resume, "_temp_skill_result", None)
    readiness_result = getattr(resume, "_temp_readiness_result", None)
    intelligence_profile = getattr(resume, "_temp_intelligence_profile", None)

    success = persist_analysis_results(
        db=db,
        student_id=resume.student_id,
        resume_id=resume.id,
        project_result=project_result,
        internship_result=internship_result,
        certification_result=certification_result,
        skill_result=skill_result,
        readiness_result=readiness_result,
        intelligence_profile=intelligence_profile,
    )

    if success:
        logger.info(
            "Pipeline Stage 8 (analysis persistence) staged: resume_id=%s student_id=%s",
            resume.id,
            resume.student_id,
        )
    else:
        logger.error(
            "Pipeline Stage 8 (analysis persistence) FAILED: resume_id=%s student_id=%s",
            resume.id,
            resume.student_id,
        )
    return success


# ---------------------------------------------------------------------------
# Main Orchestrator — Public Entry Point
# ---------------------------------------------------------------------------


def process_resume_pipeline(resume_id: uuid.UUID) -> None:
    """
    Execute the full automated resume processing pipeline for a given resume.

    This function is designed to be called as a FastAPI BackgroundTask after
    the upload HTTP response has been sent. It opens its own DB session,
    executes all pipeline stages in order, updates `processing_status` at
    each lifecycle milestone, and always closes the session on exit.

    Args:
        resume_id: UUID of the ResumeFile to process.

    Error handling:
        - Each stage's failure is logged and the pipeline is marked 'failed'.
        - No exceptions escape this function (they are all caught and logged).
        - The upload response is never affected by pipeline errors.
    """
    db: Session = SessionLocal()
    try:
        logger.info("Pipeline started: resume_id=%s", resume_id)

        # 1. Load the resume record
        resume = _load_resume(db, resume_id)
        if resume is None:
            logger.warning(
                "Pipeline aborted — resume_id=%s no longer exists in DB.", resume_id
            )
            return

        # 2. Mark pipeline as processing
        _set_status(db, resume, ProcessingStatus.processing)

        # 3. Execute stages in order
        stages = [
            ("Stage 1: Text Extraction",           _stage_extract_text),
            ("Stage 2: Section Detection",          _stage_detect_sections),
            ("Stage 3: Project Analysis",           _stage_project_analysis),
            ("Stage 4: Internship Analysis",        _stage_internship_analysis),
            ("Stage 5: Certification Analysis",     _stage_certification_analysis),
            ("Stage 6: Intelligence Profile Build", _stage_build_intelligence_profile),
            ("Stage 7: Readiness Engine",           _stage_readiness_engine),
            ("Stage 8: Analysis Persistence",       _stage_persist_analysis),
        ]

        for stage_name, stage_fn in stages:
            logger.info("Executing %s for resume_id=%s", stage_name, resume_id)
            success = stage_fn(db, resume)
            if not success:
                # A critical stage failed; abort pipeline and mark as failed
                logger.error(
                    "Pipeline FAILED at %s for resume_id=%s — aborting remaining stages.",
                    stage_name,
                    resume_id,
                )
                _set_status(db, resume, ProcessingStatus.failed)
                return

        # 4. All stages succeeded
        _set_status(db, resume, ProcessingStatus.completed)
        logger.info("Pipeline completed successfully: resume_id=%s", resume_id)

    except Exception as exc:
        # Catch-all: no unhandled exception should escape the background task
        logger.error(
            "Pipeline encountered unexpected error for resume_id=%s: %s",
            resume_id,
            exc,
            exc_info=True,
        )
        try:
            resume = _load_resume(db, resume_id)
            if resume:
                _set_status(db, resume, ProcessingStatus.failed)
        except Exception as inner_exc:
            logger.error(
                "Failed to mark resume_id=%s as failed after pipeline crash: %s",
                resume_id,
                inner_exc,
            )
    finally:
        db.close()
        logger.info("Pipeline DB session closed: resume_id=%s", resume_id)

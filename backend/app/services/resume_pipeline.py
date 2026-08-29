"""
app/services/resume_pipeline.py
--------------------------------
Internal Resume Processing Pipeline Orchestrator — SkillFit Pre-Phase 3.6.

Purpose:
    Single authoritative orchestration point for all automated resume processing.
    Called as a FastAPI BackgroundTask immediately after a resume file is stored.
    Students never interact with this module directly.

Pipeline stages (current + future):
    1. [3.3 - ACTIVE]  Text extraction       — extract_resume_service
    2. [3.4 - ACTIVE]  Section detection     — section_service
    3. [3.7 - ACTIVE]  Project analysis      — project_analysis_engine
    4. [3.8 - FUTURE]  Internship analysis   — placeholder
    5. [3.9 - FUTURE]  Certification analysis — placeholder
    6. [3.10 - FUTURE] Skill analysis        — placeholder
    7. [3.11 - FUTURE] Readiness engine      — placeholder
    8. [3.6 - FUTURE]  LLM integration       — placeholder
    9. [3.12 - FUTURE] Analysis persistence  — placeholder

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
    - Stage 3 (project analysis) makes authenticated outbound LLM calls. The
      OPENAI_API_KEY is read only by the provider layer and is never logged; if
      it is absent/invalid the stage skips gracefully (LLMConfigurationError is
      caught) rather than failing the resume. No other stage makes external
      calls yet.
"""

import logging
import uuid
from datetime import datetime, timezone
from app.services.resume.project_extractor import get_project_extractor
from sqlalchemy.orm import Session

from app.core.enums import ProcessingStatus
from app.db.database import SessionLocal
from app.models.resume_file import ResumeFile
from app.services import extraction_service
from app.services.resume.section_service import detect_sections_from_text

import json
from pathlib import Path
from dataclasses import asdict

logger = logging.getLogger(__name__)


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
# Stage 3 — Project Analysis (Phase 3.7, ACTIVE).
# Stages 4–9 remain placeholders (filled in during Phases 3.8–3.11, 3.6, 3.12).
# ---------------------------------------------------------------------------

debug_dir = Path("DEBUG/results")
debug_dir.mkdir(parents=True, exist_ok=True)


def _stage_project_analysis(db: Session, resume: ResumeFile) -> bool:
    """
    Stage 3 — Project Analysis Engine (Phase 3.7).

    Rule-based extraction of discrete projects from the RAW extracted text,
    followed by ONE evidence-based LLM analysis call per project. Produces
    in-memory ``ProjectIntelligenceReport`` artifacts; persistence is deferred
    to Phase 3.12, so the outcome is logged rather than stored.

    Best-effort / non-fatal: because nothing is persisted yet, a failure here —
    including a missing / invalid LLM key — must NOT fail the whole resume. It
    is logged and the pipeline proceeds. (Failure semantics will be revisited
    when persistence lands in 3.12.)

    Returns:
        Always True (non-fatal). Skips cleanly when there is no extracted text,
        and skips gracefully when no LLM key is configured.
    """
    if not resume.extracted_text:
        logger.warning(
            "Pipeline Stage 3 (project analysis) skipped — no extracted text: resume_id=%s",
            resume.id,
        )
        return True

    # Lazy imports: keep app boot and keyless environments free of the LLM /
    # provider stack until project analysis actually runs.
    from app.analysis.engines.project_analysis_engine import ProjectAnalysisEngine
    from app.services.llm.exceptions import LLMConfigurationError

    try:
        extractor = get_project_extractor("rule_based")
        extraction = extractor.extract(resume.extracted_text)

        print("\n===== PROJECT EXTRACTION =====")
        print(f"Projects found: {len(extraction.projects)}")

        for i, p in enumerate(extraction.projects):
            print(f"Project {i+1}: {p.title}")

        print("==============================\n")

        engine = ProjectAnalysisEngine()
        result = engine.analyze(
            resume_id=str(resume.id), raw_text=resume.extracted_text
        )
        with open(debug_dir / "debug_project.json", "w", encoding="utf-8") as f:
            json.dump(
                asdict(result),
                f,
                indent=2,
                ensure_ascii=False,
            )
        
        # Temp save for downstream engines until Phase 3.12 persistence
        setattr(resume, "_temp_project_result", result)

        print("\n===== PROJECT ANALYSIS RESULT =====")
        print(f"Total Projects: {result.total_projects_count}")
        print(f"Reports Generated: {len(result.reports)}")

        for i, report in enumerate(result.reports):
            print(f"Report {i+1}")

        print("===================================\n")
        return True
    except LLMConfigurationError as exc:
        logger.warning(
            "Pipeline Stage 3 (project analysis) skipped — LLM not configured "
            "(resume_id=%s): %s: %s",
            resume.id,
            type(exc).__name__,
            exc,
        )
        return True
    except Exception as exc:
        logger.error(
            "Pipeline Stage 3 (project analysis) error (non-fatal): resume_id=%s %s: %s",
            resume.id,
            type(exc).__name__,
            exc,
        )
        return True


def _stage_internship_analysis(_db: Session, resume: ResumeFile) -> bool:
    """
    Stage 4 — Internship Analysis Engine (Phase 3.8).
    
    Like project analysis, this is best-effort and non-fatal.
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

        print("\n===== INTERNSHIP EXTRACTION =====")
        print(f"Internships found: {len(extraction_result.internships)}")

        for i, internship in enumerate(extraction_result.internships):
            print(f"Internship {i+1}:")
            print(f"Role: {internship.role}")
            print(f"Organization: {internship.organization}")

        print("=================================\n")
        
        engine = InternshipAnalysisEngine()
        result = engine.analyze(
            resume_id=str(resume.id), internships=extraction_result.internships
        )
        with open(debug_dir / "debug_internship.json", "w", encoding="utf-8") as f:
            json.dump(
                asdict(result),
                f,
                indent=2,
                ensure_ascii=False,
            )

        # Temp save for downstream engines until Phase 3.12 persistence
        setattr(resume, "_temp_internship_result", result)

        print("\n===== INTERNSHIP ANALYSIS RESULT =====")
        print(f"Total Internships: {result.total_internships_count}")
        print(f"Reports Generated: {len(result.reports)}")

        for i, report in enumerate(result.reports):
            print(f"Report {i+1}")

        print("=====================================\n")

        return True
    except LLMConfigurationError as exc:
        logger.warning(
            "Pipeline Stage 4 (internship analysis) skipped — LLM not configured "
            "(resume_id=%s): %s: %s",
            resume.id,
            type(exc).__name__,
            exc,
        )
        return True
    except Exception as exc:
        logger.error(
            "Pipeline Stage 4 (internship analysis) error (non-fatal): resume_id=%s %s: %s",
            resume.id,
            type(exc).__name__,
            exc,
        )
        return True


def _stage_certification_analysis(_db: Session, resume: ResumeFile) -> bool:
    """
    Stage 5 — Certification Analysis Engine (Phase 3.9).
    
    Rule-based extraction of certifications followed by batched LLM analysis.
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

        print("\n===== CERTIFICATION EXTRACTION =====")
        print(f"Certifications found: {len(extraction_result.certifications)}")

        for i, cert in enumerate(extraction_result.certifications):
            print(f"Cert {i+1}: {cert.certification_name} (Provider: {cert.issuer})")

        print("====================================\n")
        
        engine = CertificationAnalysisEngine()
        result = engine.analyze(
            resume_id=str(resume.id), certifications=extraction_result.certifications
        )
        with open(debug_dir / "debug_certification.json", "w", encoding="utf-8") as f:
            json.dump(
                asdict(result),
                f,
                indent=2,
                ensure_ascii=False,
            )

        # Temp save for downstream engines until Phase 3.12 persistence
        setattr(resume, "_temp_certification_result", result)

        print("\n===== CERTIFICATION ANALYSIS RESULT =====")
        print(f"Total Certifications: {result.total_certifications_count}")
        print(f"Reports Generated: {len(result.reports)}")

        for i, report in enumerate(result.reports):
            print(f"Report {i+1}: {report.certification_name} ({report.provider_tier})")

        print("=========================================\n")

        return True
    except LLMConfigurationError as exc:
        logger.warning(
            "Pipeline Stage 5 (certification analysis) skipped — LLM not configured "
            "(resume_id=%s): %s: %s",
            resume.id,
            type(exc).__name__,
            exc,
        )
        return True
    except Exception as exc:
        logger.error(
            "Pipeline Stage 5 (certification analysis) error (non-fatal): resume_id=%s %s: %s",
            resume.id,
            type(exc).__name__,
            exc,
        )
        return True


def _stage_skill_analysis(_db: Session, resume: ResumeFile) -> bool:
    """
    Stage 6 — Evidence-Based Skill Engine (Phase 3.10).
    Aggregates skills from Projects, Internships, and Certifications.
    """
    try:
        from app.analysis.engines.skill_analysis_engine import SkillAnalysisEngine
        
        project_result = getattr(resume, "_temp_project_result", None)
        internship_result = getattr(resume, "_temp_internship_result", None)
        certification_result = getattr(resume, "_temp_certification_result", None)
        
        p_reports = project_result.reports if project_result else []
        i_reports = internship_result.reports if internship_result else []
        c_reports = certification_result.reports if certification_result else []
        
        temp_sections = getattr(resume, "_temp_sections_result", {})
        self_reported = temp_sections.get("skills", "")
        
        engine = SkillAnalysisEngine()
        result = engine.analyze(
            project_reports=p_reports,
            internship_reports=i_reports,
            certification_reports=c_reports,
            self_reported_skills_text=self_reported
        )
        
        with open(debug_dir / "debug_skill.json", "w", encoding="utf-8") as f:
            json.dump(
                asdict(result),
                f,
                indent=2,
                ensure_ascii=False,
            )
            
        print("\n===== SKILL ANALYSIS RESULT =====")
        print(f"Total Skills: {result.total_skills_count}")
        for i, skill in enumerate(result.skills):
            print(f"Skill {i+1}: {skill.skill_name}")
            print(f"  Confidence: {skill.confidence_score} ({skill.confidence_level})")
            print(f"  Depth: {skill.skill_depth}")
            print(f"  Hiring Signal: {skill.hiring_signal}")
        print("=================================\n")
        
        setattr(resume, "_temp_skill_result", result)
        return True
    except Exception as exc:
        logger.error(
            "Pipeline Stage 6 (skill analysis) FAILED: resume_id=%s error=%s",
            resume.id,
            exc,
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



def _stage_synthesis_engine(db: Session, resume: ResumeFile) -> bool:
    """
    Stage 8 — Synthesis Engine (Phase 3 Final Hardening).
    Bridges CandidateIntelligenceProfile → legacy candidate_profile_dict
    for analysis_persistence_service.py.

    TEMPORARY: Removed when DB persistence sprint introduces
    CandidateIntelligenceSnapshot-based storage.
    """
    try:
        from app.analysis.engines.synthesis_engine import SynthesisEngine

        profile = getattr(resume, "_temp_intelligence_profile", None)
        if not profile:
            logger.warning("Pipeline Stage 8 (synthesis) skipped — no intelligence profile.")
            return True

        engine = SynthesisEngine()
        profile_dict = engine.synthesize(profile=profile)

        setattr(resume, "_temp_candidate_profile", profile_dict)
        logger.info("Pipeline Stage 8 (synthesis) complete: resume_id=%s", resume.id)
        return True
    except Exception as exc:
        logger.error(
            "Pipeline Stage 8 (synthesis) FAILED: resume_id=%s error=%s",
            resume.id, exc,
        )
        return False



def _stage_persist_analysis(db: Session, resume: ResumeFile) -> bool:
    """
    Stage 9 — Analysis Persistence (Phase 3.12).

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
    candidate_profile_dict = getattr(resume, "_temp_candidate_profile", None)

    success = persist_analysis_results(
        db=db,
        student_id=resume.student_id,
        resume_id=resume.id,
        project_result=project_result,
        internship_result=internship_result,
        certification_result=certification_result,
        skill_result=skill_result,
        readiness_result=readiness_result,
        candidate_profile_dict=candidate_profile_dict,
    )

    if success:
        logger.info(
            "Pipeline Stage 9 (analysis persistence) staged: resume_id=%s student_id=%s",
            resume.id,
            resume.student_id,
        )
    else:
        logger.error(
            "Pipeline Stage 9 (analysis persistence) FAILED: resume_id=%s student_id=%s",
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
            ("Stage 1: Text Extraction",       _stage_extract_text),
            ("Stage 2: Section Detection",      _stage_detect_sections),
            ("Stage 3: Project Analysis",       _stage_project_analysis),
            ("Stage 4: Internship Analysis",    _stage_internship_analysis),
            ("Stage 5: Certification Analysis", _stage_certification_analysis),
            ("Stage 6: Skill Analysis",         _stage_skill_analysis),
            ("Stage 7: Readiness Engine",       _stage_readiness_engine),
            ("Stage 8: Synthesis Engine",       _stage_synthesis_engine),
            ("Stage 9: Analysis Persistence",   _stage_persist_analysis),
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

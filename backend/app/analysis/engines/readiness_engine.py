"""
app/analysis/engines/readiness_engine.py
----------------------------------------
Readiness Engine for SkillFit Phase 3 Final Hardening.

Inputs (Phase 3 Remediation):
    A populated CandidateIntelligenceProfile — the single source of truth.
    No longer accepts ProjectAnalysisResult, InternshipAnalysisResult, etc.
    All scoring is derived from the profile's intelligence objects.

Outputs (unchanged — public contract preserved):
    ReadinessAnalysisResult with ReadinessLevel and ScoreBreakdown.

Scoring logic:
    Project score:      Derived from engineering_signals (DEPLOYMENT, TESTING, ARCHITECTURE)
                        and ownership_signals (OWNED, LED level entries).
    Internship score:   Derived from workplace_exposure count and ownership depth.
    Certification score: Derived from certifications (industry_recognition level).
    Skill score:        Derived from skills (VerificationStatus distribution).
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional

from app.analysis.models.candidate_profile import (
    CandidateIntelligenceProfile,
    EngineeringSignalCategory,
    OwnershipLevel,
    VerificationStatus,
)
from app.analysis.models.readiness_models import (
    ReadinessAnalysisResult,
    ReadinessLevel,
    AnalysisStatus,
    Severity,
    ScoreBreakdown,
    ReadinessStrength,
    ReadinessGap,
    HIRING_SIGNAL_WEIGHTS,
)

logger = logging.getLogger(__name__)


def _clamp(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    return max(min_val, min(value, max_val))


def _severity_to_int(severity: Severity) -> int:
    if severity == Severity.HIGH:
        return 3
    if severity == Severity.MEDIUM:
        return 2
    return 1


# ---------------------------------------------------------------------------
# Ownership level weights (higher ownership = more readiness signal)
# ---------------------------------------------------------------------------
_OWNERSHIP_WEIGHTS = {
    OwnershipLevel.OBSERVED.value: 0.2,
    OwnershipLevel.CONTRIBUTED.value: 0.4,
    OwnershipLevel.IMPLEMENTED.value: 0.6,
    OwnershipLevel.OWNED.value: 0.8,
    OwnershipLevel.LED.value: 1.0,
}

# Industry recognition → certification score multiplier
_RECOGNITION_MULTIPLIERS = {
    "high": 1.0,
    "moderate": 0.75,
    "low": 0.5,
    "unknown": 0.25,
    "theory-heavy": 0.4,
}

# VerificationStatus → skill point contribution
_SKILL_POINTS = {
    VerificationStatus.STRONGLY_VERIFIED.value: 15.0,
    VerificationStatus.VERIFIED.value: 10.0,
    VerificationStatus.WEAKLY_VERIFIED.value: 5.0,
    VerificationStatus.UNVERIFIED.value: 1.0,
}


class ReadinessEngine:
    """
    Deterministic Placement Readiness scoring engine.

    Consumes a CandidateIntelligenceProfile and outputs a ReadinessAnalysisResult.
    All scoring is evidence-based and reproducible — no LLM calls.
    """

    def __init__(self):
        self.weights = {
            "projects": 0.45,
            "internships": 0.15,
            "certifications": 0.10,
            "skills": 0.30,
        }

    def analyze(
        self,
        resume_id: str,
        profile: CandidateIntelligenceProfile,
    ) -> ReadinessAnalysisResult:
        """
        Compute a ReadinessAnalysisResult from the CandidateIntelligenceProfile.

        Args:
            resume_id: The source resume identifier (for tracing).
            profile:   The fully populated CandidateIntelligenceProfile.

        Returns:
            ReadinessAnalysisResult with all scoring and gap analysis.
        """
        try:
            return self._analyze_internal(resume_id, profile)
        except Exception:
            logger.exception("Readiness Engine critical failure for resume_id=%s", resume_id)
            return self._empty_result(resume_id, status=AnalysisStatus.FAILED)

    def _analyze_internal(
        self,
        resume_id: str,
        profile: CandidateIntelligenceProfile,
    ) -> ReadinessAnalysisResult:

        status = AnalysisStatus.SUCCESS
        meta = profile.metadata

        # Counts from profile metadata — never requires re-reading raw results
        project_count = meta.total_projects_analyzed
        internship_count = meta.total_internships_analyzed
        certification_count = meta.total_certifications_analyzed
        skill_count = len(profile.skills)

        # ── 1. Project Score ──────────────────────────────────────────────────
        # Derived from engineering signals and ownership signals.
        # Engineering signals provide evidence of technical practice quality.
        # Ownership signals indicate individual contribution depth.

        project_score = 0.0
        project_contributors = {
            "architecture": 0.0,
            "deployment": 0.0,
            "testing": 0.0,
            "security": 0.0,
            "ownership_depth": 0.0,
        }

        eng_signals = [s for s in profile.engineering_signals if s.demonstrated]
        ownership_sigs = [o for o in profile.ownership_signals if o.evidence]

        if eng_signals or ownership_sigs:
            # Engineering signal scoring: each demonstrated signal contributes
            # Category weights (deployment and testing are highest hiring signals)
            category_weights = {
                EngineeringSignalCategory.DEPLOYMENT.value: 22.0,
                EngineeringSignalCategory.ARCHITECTURE.value: 22.0,
                EngineeringSignalCategory.TESTING.value: 18.0,
                EngineeringSignalCategory.SECURITY.value: 15.0,
                EngineeringSignalCategory.MONITORING.value: 12.0,
                EngineeringSignalCategory.INTEGRATION.value: 10.0,
            }
            # Decay: first 3 signals per category count, rest discarded
            seen_per_category: dict = {}
            raw_eng_score = 0.0
            for sig in eng_signals:
                cat = sig.category
                seen_per_category[cat] = seen_per_category.get(cat, 0) + 1
                if seen_per_category[cat] <= 3:
                    decay = [1.0, 0.5, 0.25][seen_per_category[cat] - 1]
                    cat_weight = category_weights.get(cat, 8.0)
                    raw_eng_score += cat_weight * decay
                    key = cat.lower() if cat.lower() in project_contributors else "architecture"
                    project_contributors[key] += cat_weight * decay

            # Ownership signal scoring
            ownership_score = 0.0
            for sig in ownership_sigs[:5]:  # cap at 5 to prevent quantity bias
                weight = _OWNERSHIP_WEIGHTS.get(sig.ownership_level, 0.4)
                ownership_score += 5.0 * weight
            project_contributors["ownership_depth"] = ownership_score

            project_score = _clamp(raw_eng_score + ownership_score, 0.0, 100.0)
        elif project_count > 0:
            # Projects were detected but produced no signals
            status = AnalysisStatus.PARTIAL

        # ── 2. Internship Score ───────────────────────────────────────────────
        # Derived from workplace_exposure (breadth) and ownership signals (depth)
        # anchored to internship source type.

        internship_score = 0.0
        if profile.workplace_exposure:
            exposure_count = len(profile.workplace_exposure)
            base = min(exposure_count * 8.0, 60.0)  # Each exposure type = 8 pts, max 60

            # Add ownership depth from internship-sourced signals
            from app.analysis.models.candidate_profile import IntelligenceSourceType
            intern_ownership = [
                o for o in profile.ownership_signals
                if any(
                    ev.source == IntelligenceSourceType.INTERNSHIP
                    for ev in o.evidence
                )
            ]
            for sig in intern_ownership[:3]:
                weight = _OWNERSHIP_WEIGHTS.get(sig.ownership_level, 0.4)
                base += 10.0 * weight

            internship_score = _clamp(base, 0.0, 100.0)
        elif internship_count > 0:
            status = AnalysisStatus.PARTIAL

        # ── 3. Certification Score ────────────────────────────────────────────
        # Derived from certifications (industry_recognition field).

        certification_score = 0.0
        if profile.certifications:
            total_cert_score = 0.0
            for cert in profile.certifications:
                rec_lower = (cert.industry_recognition or "unknown").lower()
                multiplier = _RECOGNITION_MULTIPLIERS.get(rec_lower, 0.25)
                total_cert_score += 20.0 * multiplier
            certification_score = _clamp(total_cert_score, 0.0, 100.0)
        elif certification_count > 0:
            status = AnalysisStatus.PARTIAL

        # ── 4. Skill Score ────────────────────────────────────────────────────
        # Derived from SkillIntelligence verification_status distribution.

        skill_score = 0.0
        adv_skills = 0    # STRONGLY_VERIFIED
        int_skills = 0    # VERIFIED
        beg_skills = 0    # WEAKLY_VERIFIED or lower
        high_signal_skills = 0
        med_signal_skills = 0
        low_signal_skills = 0

        if profile.skills:
            total_points = 0.0
            for sk in profile.skills:
                status_val = sk.verification_status
                pts = _SKILL_POINTS.get(status_val, 1.0)

                if status_val == VerificationStatus.STRONGLY_VERIFIED.value:
                    adv_skills += 1
                    high_signal_skills += 1
                elif status_val == VerificationStatus.VERIFIED.value:
                    int_skills += 1
                    high_signal_skills += 1
                elif status_val == VerificationStatus.WEAKLY_VERIFIED.value:
                    beg_skills += 1
                    med_signal_skills += 1
                else:
                    beg_skills += 1
                    low_signal_skills += 1

                total_points += pts

            skill_score = _clamp(total_points, 0.0, 100.0)
        elif skill_count > 0:
            status = AnalysisStatus.PARTIAL

        # ── Final Readiness Calculation ───────────────────────────────────────
        readiness_score = _clamp(
            (project_score * self.weights["projects"]) +
            (internship_score * self.weights["internships"]) +
            (certification_score * self.weights["certifications"]) +
            (skill_score * self.weights["skills"]),
            0.0, 100.0
        )

        if readiness_score >= 80.0:
            readiness_level = ReadinessLevel.HIGH
        elif readiness_score >= 60.0:
            readiness_level = ReadinessLevel.MEDIUM
        else:
            readiness_level = ReadinessLevel.LOW

        # Evidence count (total distinct evidence items across all profile objects)
        evidence_count = sum(len(t.evidence) for t in profile.technologies)
        evidence_count += sum(len(c.evidence) for c in profile.competencies)
        evidence_count += sum(len(s.evidence) for s in profile.skills)

        # ── Strengths & Gaps ──────────────────────────────────────────────────
        strengths: List[ReadinessStrength] = []
        gaps: List[ReadinessGap] = []

        if project_count == 0:
            gaps.append(ReadinessGap(
                title="No Projects",
                severity=Severity.HIGH,
                reasoning="No project experience detected."
            ))
        elif not eng_signals and not ownership_sigs:
            gaps.append(ReadinessGap(
                title="Weak Project Signals",
                severity=Severity.HIGH,
                reasoning="Projects found but yielded no engineering or ownership signals."
            ))
        elif project_score >= 70.0:
            strengths.append(ReadinessStrength(
                title="Strong Engineering Signal Portfolio",
                evidence_count=len(eng_signals),
                reasoning=f"{len(eng_signals)} demonstrated engineering signals across {project_count} project(s).",
                impact_score=project_score * self.weights["projects"]
            ))

        if internship_count == 0:
            gaps.append(ReadinessGap(
                title="No Internships",
                severity=Severity.MEDIUM,
                reasoning="No industry internship experience detected."
            ))
        elif internship_score >= 70.0:
            strengths.append(ReadinessStrength(
                title="Strong Workplace Exposure",
                evidence_count=len(profile.workplace_exposure),
                reasoning=f"{len(profile.workplace_exposure)} distinct workplace exposure types demonstrated.",
                impact_score=internship_score * self.weights["internships"]
            ))

        if certification_count == 0:
            gaps.append(ReadinessGap(
                title="No Certifications",
                severity=Severity.LOW,
                reasoning="No external certifications detected."
            ))
        elif certification_score >= 70.0:
            strengths.append(ReadinessStrength(
                title="Strong Certification Profile",
                evidence_count=len(profile.certifications),
                reasoning=f"{len(profile.certifications)} recognized certification(s).",
                impact_score=certification_score * self.weights["certifications"]
            ))

        if high_signal_skills == 0 and skill_count > 0:
            gaps.append(ReadinessGap(
                title="No Strongly Verified Skills",
                severity=Severity.HIGH,
                reasoning="No skills reached VERIFIED or STRONGLY_VERIFIED status."
            ))
        elif adv_skills >= 3:
            strengths.append(ReadinessStrength(
                title="Extensive Verified Skill Base",
                evidence_count=adv_skills,
                reasoning=f"{adv_skills} skills at STRONGLY_VERIFIED status.",
                impact_score=skill_score * self.weights["skills"]
            ))

        # From profile findings: HIGH/CRITICAL findings become gaps
        for finding in profile.findings:
            if finding.severity in ("HIGH", "CRITICAL") and finding.type == "MISSING_SIGNAL":
                gaps.append(ReadinessGap(
                    title=finding.title,
                    severity=Severity.HIGH if finding.severity == "HIGH" else Severity.HIGH,
                    reasoning=finding.description,
                ))

        strengths.sort(key=lambda s: (-s.impact_score, s.title, -s.evidence_count))
        gaps.sort(key=lambda g: (-_severity_to_int(g.severity), g.title))
        strengths = strengths[:5]
        gaps = gaps[:5]

        return ReadinessAnalysisResult(
            resume_id=resume_id,
            engine_version="4.0.0",  # Phase 3 Final Hardening
            analysis_status=status,
            readiness_score=readiness_score,
            readiness_level=readiness_level,
            overall_confidence=1.0,  # Deterministic — no confidence scores
            score_breakdown=ScoreBreakdown(
                project_score=project_score,
                internship_score=internship_score,
                certification_score=certification_score,
                skill_score=skill_score,
                project_contributors={k: round(v, 2) for k, v in project_contributors.items()},
            ),
            strengths=strengths,
            gaps=gaps,
            advanced_skill_count=adv_skills,
            intermediate_skill_count=int_skills,
            beginner_skill_count=beg_skills,
            high_signal_skill_count=high_signal_skills,
            medium_signal_skill_count=med_signal_skills,
            low_signal_skill_count=low_signal_skills,
            project_count=project_count,
            internship_count=internship_count,
            certification_count=certification_count,
            skill_count=skill_count,
            evidence_count=evidence_count,
            generated_at=datetime.now(timezone.utc),
        )

    def _empty_result(self, resume_id: str, status: AnalysisStatus) -> ReadinessAnalysisResult:
        return ReadinessAnalysisResult(
            resume_id=resume_id,
            engine_version="4.0.0",
            analysis_status=status,
            readiness_score=0.0,
            readiness_level=ReadinessLevel.LOW,
            overall_confidence=0.0,
            score_breakdown=ScoreBreakdown(
                project_score=0.0,
                internship_score=0.0,
                certification_score=0.0,
                skill_score=0.0,
            ),
            strengths=[],
            gaps=[],
            advanced_skill_count=0,
            intermediate_skill_count=0,
            beginner_skill_count=0,
            high_signal_skill_count=0,
            medium_signal_skill_count=0,
            low_signal_skill_count=0,
            project_count=0,
            internship_count=0,
            certification_count=0,
            skill_count=0,
            evidence_count=0,
            generated_at=datetime.now(timezone.utc),
        )

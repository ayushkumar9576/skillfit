"""Canonical readiness assessment for pipeline results and older snapshots."""

from app.analysis.engines.readiness_engine import ReadinessEngine
from app.analysis.models.candidate_profile import CandidateIntelligenceProfile
from app.analysis.models.readiness_models import AnalysisStatus, ReadinessAnalysisResult


def apply_readiness_result(
    profile: CandidateIntelligenceProfile, result: ReadinessAnalysisResult
) -> None:
    if result.analysis_status != AnalysisStatus.SUCCESS:
        raise ValueError(f"Readiness analysis did not succeed: {result.analysis_status}")
    profile.readiness_score = float(result.readiness_score)
    profile.readiness_level = result.readiness_level.value
    profile.readiness_status = AnalysisStatus.SUCCESS.value
    profile.summary.readiness_highlights = [strength.title for strength in result.strengths]


def populate_readiness(profile: CandidateIntelligenceProfile, resume_id: str) -> None:
    """Preserve saved assessments; compute missing legacy values with the same engine."""
    if (profile.readiness_status in {None, "SUCCESS"}
            and profile.readiness_level in {"HIGH", "MEDIUM", "LOW"}
            and profile.readiness_score is not None):
        profile.readiness_status = AnalysisStatus.SUCCESS.value
        return
    result = ReadinessEngine().analyze(resume_id, profile)
    if result.analysis_status != AnalysisStatus.SUCCESS:
        # Legacy snapshots may be incomplete. Preserve their other insights,
        # but do not present a failed/partial assessment as a readiness score.
        profile.readiness_level = None
        profile.readiness_score = None
        profile.readiness_status = result.analysis_status.value
        profile.summary.readiness_highlights = [
            "Readiness is unavailable. A new analysis is needed to assess placement readiness."
        ]
        return
    apply_readiness_result(profile, result)

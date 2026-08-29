"""
app/analysis/engines/synthesis_engine.py
-----------------------------------------
SkillFit Synthesis Engine — Phase 3 Final Hardening.

Responsibility (post-remediation):
    Bridge the CandidateIntelligenceProfile to the legacy candidate_profile_dict
    contract expected by analysis_persistence_service.py.

    This engine no longer performs any domain inference or scoring logic.
    Those responsibilities now belong exclusively to CandidateIntelligenceAggregator.

    When the DB Persistence Sprint (Phase 3.13) replaces analysis_persistence_service.py
    with a CandidateIntelligenceSnapshot-based approach, this bridge engine can
    be deleted entirely.

Input:
    CandidateIntelligenceProfile

Output:
    Dict[str, Any] — matches the candidate_profile_dict schema that
    analysis_persistence_service.persist_analysis_results() expects:
        primary_domain
        secondary_domains
        domain_tiers
        domain_scores
        domain_signals
        project_tiers
        industry_exposure_levels
        candidate_primary_domain_confidence
        strongest_skills
        soft_skills
        role_affinities
        evidence_summary

NOTE:
    The AffinityEngine has been migrated to consume List[SkillIntelligence].
    SoftSkillEngine now operates on the profile directly.
    All domain signals are read from profile.domains — not computed here.
"""

import logging
from typing import Any, Dict, List

from app.analysis.models.candidate_profile import (
    CandidateIntelligenceProfile,
    DemonstrationLevel,
    VerificationStatus,
)
from app.analysis.engines.affinity_engine import AffinityEngine

logger = logging.getLogger(__name__)

# Demo level → sortable rank for top-skills ordering
_DEMO_RANK = {
    DemonstrationLevel.CLAIMED.value: 0,
    DemonstrationLevel.REFERENCED.value: 1,
    DemonstrationLevel.USED.value: 2,
    DemonstrationLevel.IMPLEMENTED.value: 3,
    DemonstrationLevel.DESIGNED.value: 4,
    DemonstrationLevel.ARCHITECTED.value: 5,
}

# VerificationStatus → "confidence" float for strongest_skills payload
_STATUS_CONFIDENCE = {
    VerificationStatus.STRONGLY_VERIFIED.value: 0.95,
    VerificationStatus.VERIFIED.value: 0.80,
    VerificationStatus.WEAKLY_VERIFIED.value: 0.55,
    VerificationStatus.UNVERIFIED.value: 0.20,
}


class SynthesisEngine:
    """
    Profile-to-persistence bridge engine.

    Translates a CandidateIntelligenceProfile into the legacy dict schema
    required by analysis_persistence_service.py.

    This is a temporary bridge only. It will be removed when the DB sprint
    introduces native CandidateIntelligenceSnapshot persistence.
    """

    def __init__(self):
        self.affinity_engine = AffinityEngine()

    def synthesize(
        self,
        profile: CandidateIntelligenceProfile,
    ) -> Dict[str, Any]:
        """
        Translate CandidateIntelligenceProfile → legacy candidate_profile_dict.

        Args:
            profile: The fully populated CandidateIntelligenceProfile.

        Returns:
            Dict matching the candidate_profile_dict schema consumed by
            analysis_persistence_service.persist_analysis_results().
        """
        # ── Domain signals ────────────────────────────────────────────────
        domain_scores: Dict[str, float] = {}
        domain_tiers: Dict[str, str] = {}
        primary_domain: str | None = None
        secondary_domains: List[str] = []
        candidate_primary_domain_confidence = 0.0
        domain_signals_set: set = set()

        for d in profile.domains:
            domain_name = d.domain
            # Score = number of supporting competencies + technologies (proxy for evidence depth)
            score = len(d.supporting_competencies) * 10.0 + len(d.supporting_technologies) * 5.0
            domain_scores[domain_name] = score
            domain_tiers[domain_name] = "INTERMEDIATE"  # Tier is refined in Phase 4
            for tech in d.supporting_technologies:
                domain_signals_set.add(tech)

        if domain_scores:
            sorted_domains = sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)
            primary_domain = sorted_domains[0][0]
            total_score = sum(domain_scores.values())
            purity = domain_scores[primary_domain] / total_score if total_score > 0 else 0.0
            candidate_primary_domain_confidence = round(purity, 2)
            secondary_domains = [d for d, _ in sorted_domains[1:] if _ >= 5.0]

        # ── Strongest skills ──────────────────────────────────────────────
        sorted_skills = sorted(
            profile.skills,
            key=lambda s: (
                _STATUS_CONFIDENCE.get(s.verification_status, 0.0),
                _DEMO_RANK.get(s.demonstration_level, 0),
                s.evidence_count,
            ),
            reverse=True,
        )
        strongest_skills = [
            {
                "name": s.skill,
                "confidence": _STATUS_CONFIDENCE.get(s.verification_status, 0.2),
                "evidence_count": s.evidence_count,
                "depth": s.demonstration_level,
            }
            for s in sorted_skills[:10]
        ]

        # ── Soft skills (from ownership signals) ──────────────────────────
        # Soft skills are SkillIntelligence items with soft skill keywords.
        # They are already mixed into profile.skills by the SoftSkillEngine.
        _SOFT_KEYWORDS = frozenset({
            "leadership", "communication", "collaboration", "ownership",
            "problem solving", "teamwork", "initiative", "mentoring",
            "stakeholder", "agile",
        })
        soft_skills = [
            {
                "name": s.skill,
                "confidence": _STATUS_CONFIDENCE.get(s.verification_status, 0.2),
                "evidence_count": s.evidence_count,
            }
            for s in profile.skills
            if any(kw in s.skill.lower() for kw in _SOFT_KEYWORDS)
        ]

        # ── Role affinities (from migrated AffinityEngine) ────────────────
        role_affinities: Dict[str, Any] = {}
        try:
            affinities_list = self.affinity_engine.analyze(profile.skills)
            for aff in affinities_list:
                role_affinities[aff["role"]] = {
                    "confidence": aff["confidence"],
                    "evidence": aff["evidence"],
                }
        except Exception as exc:
            logger.warning("AffinityEngine failed (non-fatal): %s", exc)

        # ── Evidence summary ──────────────────────────────────────────────
        evidence_summary = {
            "total_projects": profile.metadata.total_projects_analyzed,
            "total_internships": profile.metadata.total_internships_analyzed,
            "total_certifications": profile.metadata.total_certifications_analyzed,
            "total_technologies": len(profile.technologies),
            "total_skills": len(profile.skills),
            "total_findings": len(profile.findings),
        }

        return {
            "primary_domain": primary_domain,
            "secondary_domains": secondary_domains,
            "domain_tiers": domain_tiers,
            "domain_scores": domain_scores,
            "domain_signals": list(domain_signals_set),
            "project_tiers": {},  # Retired: was per-project, now domain-level
            "industry_exposure_levels": {
                w.exposure_type: "PRESENT"
                for w in profile.workplace_exposure
            },
            "candidate_primary_domain_confidence": candidate_primary_domain_confidence,
            "strongest_skills": strongest_skills,
            "soft_skills": soft_skills,
            "role_affinities": role_affinities,
            "evidence_summary": evidence_summary,
        }

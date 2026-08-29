"""
app/analysis/engines/skill_analysis_engine.py
----------------------------------------------
Skill Verification Engine — Phase 3 Remediation.

Role: Deterministic skill verification from aggregated intelligence.

This engine is NOT an independent intelligence generator.
It does NOT call the LLM.
It does NOT generate confidence scores.
It does NOT classify skills as Beginner/Intermediate/Advanced.

Architecture:
    Project Intelligence   ──┐
    Internship Intelligence ──┤─→ CandidateIntelligenceAggregator → SkillVerificationEngine → List[SkillIntelligence]
    Certification Intel.   ──┘

Inputs:
    A populated CandidateIntelligenceProfile containing technologies,
    competencies, certifications, ownership signals, and engineering signals.
    All evidence is already structured as IntelligenceEvidence objects.

Outputs:
    List[SkillIntelligence] — one entry per unique skill, with:
        - skill: normalized name
        - verification_status: VerificationStatus (UNVERIFIED → STRONGLY_VERIFIED)
        - demonstration_level: DemonstrationLevel (CLAIMED → ARCHITECTED)
        - evidence: List[IntelligenceEvidence]
        - evidence_count: int (deterministic count, not a probability)

Verification Logic:
    Each evidence item carries a source type ("project", "internship", "certification").
    A configurable weight is applied per source type (SKILL_EVIDENCE_WEIGHTS).
    The cumulative weighted score maps to a VerificationStatus threshold.

Demonstration Level Resolution:
    The highest DemonstrationLevel observed across all evidence sources wins.
    ARCHITECTED > DESIGNED > IMPLEMENTED > USED > REFERENCED > CLAIMED

Design Rules:
    - Pure standard library. Zero framework dependencies.
    - No LLM calls.
    - No confidence scores.
    - No probabilistic reasoning.
    - Fully reproducible from the same input profile.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional

from app.analysis.models.candidate_profile import (
    CandidateIntelligenceProfile,
    CompetencyType,
    DemonstrationLevel,
    IntelligenceEvidence,
    IntelligenceSourceType,
    SkillIntelligence,
    VerificationStatus,
)

# ---------------------------------------------------------------------------
# Configurable Evidence Weights (sourced from candidate_intelligence.py)
# Defined here as well for standalone use; must be kept in sync.
# ---------------------------------------------------------------------------

SKILL_EVIDENCE_WEIGHTS: Dict[str, float] = {
    IntelligenceSourceType.PROJECT.value: 1.0,
    IntelligenceSourceType.INTERNSHIP.value: 0.7,
    IntelligenceSourceType.CERTIFICATION.value: 0.3,
    IntelligenceSourceType.SELF_REPORTED.value: 0.1,
}

VERIFICATION_THRESHOLDS: Dict[str, float] = {
    VerificationStatus.STRONGLY_VERIFIED.value: 2.0,
    VerificationStatus.VERIFIED.value: 1.0,
    VerificationStatus.WEAKLY_VERIFIED.value: 0.3,
}

# Ordered from weakest to strongest — used for max-wins resolution
_DEMO_LEVEL_ORDER: List[str] = [
    DemonstrationLevel.CLAIMED.value,
    DemonstrationLevel.REFERENCED.value,
    DemonstrationLevel.USED.value,
    DemonstrationLevel.IMPLEMENTED.value,
    DemonstrationLevel.DESIGNED.value,
    DemonstrationLevel.ARCHITECTED.value,
]

# Soft skill signals detected deterministically via regex
# These are NOT LLM outputs — they are heuristic findings from ownership signals
_SOFT_SKILL_PATTERNS: Dict[str, re.Pattern] = {
    "Leadership": re.compile(
        r'\b(led|lead|leading|directed|managed|orchestrated|spearheaded|guided|mentored|coordinated)\b',
        re.IGNORECASE
    ),
    "Communication": re.compile(
        r'\b(communicated|presented|negotiated|documented|reported|articulated|facilitated|pitched)\b',
        re.IGNORECASE
    ),
    "Ownership": re.compile(
        r'\b(owned|ownership|accountable|drove|delivered|sole|autonomous|end-to-end)\b',
        re.IGNORECASE
    ),
    "Collaboration": re.compile(
        r'\b(collaborated|teamwork|team player|partnered|cross-functional|pair programming|co-authored)\b',
        re.IGNORECASE
    ),
    "Problem Solving": re.compile(
        r'\b(solved|resolved|troubleshot|debugged|optimized|overcame|analyzed|investigated)\b',
        re.IGNORECASE
    ),
    "Mentorship": re.compile(
        r'\b(mentored|taught|tutored|trained|guided|onboarded|coached)\b',
        re.IGNORECASE
    ),
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _resolve_verification(evidence: List[IntelligenceEvidence]) -> str:
    """
    Deterministically compute VerificationStatus from evidence sources.

    Sums the weights of all evidence items' source types. Maps the
    cumulative score to the highest satisfied threshold.
    """
    total = sum(SKILL_EVIDENCE_WEIGHTS.get(ev.source, 0.0) for ev in evidence)
    for status, threshold in sorted(
        VERIFICATION_THRESHOLDS.items(), key=lambda x: x[1], reverse=True
    ):
        if total >= threshold:
            return status
    return VerificationStatus.UNVERIFIED.value


def _max_demo_level(a: str, b: str) -> str:
    """Return the stronger of two DemonstrationLevel values."""
    idx_a = _DEMO_LEVEL_ORDER.index(a) if a in _DEMO_LEVEL_ORDER else 0
    idx_b = _DEMO_LEVEL_ORDER.index(b) if b in _DEMO_LEVEL_ORDER else 0
    return _DEMO_LEVEL_ORDER[max(idx_a, idx_b)]


def _normalize(name: str) -> str:
    """Lowercase, strip, collapse whitespace for deduplication keying."""
    return re.sub(r'\s+', ' ', name.strip().lower())


# ---------------------------------------------------------------------------
# Skill Verification Engine
# ---------------------------------------------------------------------------

class SkillVerificationEngine:
    """
    Deterministic skill verification from a CandidateIntelligenceProfile.

    This engine aggregates evidence already structured by the upstream
    Project, Internship, and Certification intelligence engines. It never
    re-parses resume text and never calls the LLM.

    Usage:
        engine = SkillVerificationEngine()
        skills = engine.verify(profile, self_reported_skills=["Python", "SQL"])
    """

    def verify(
        self,
        profile: CandidateIntelligenceProfile,
        self_reported_skills: Optional[List[str]] = None,
    ) -> List[SkillIntelligence]:
        """
        Produce a List[SkillIntelligence] from all intelligence sources in profile.

        Sources consumed (in priority order):
            1. profile.technologies — highest-signal source; carries demonstration level
            2. profile.competencies — maps CompetencyType → skill entry
            3. profile.certifications — adds WEAKLY_VERIFIED certification evidence
            4. profile.ownership_signals — reinforces existing skills via signal text
            5. profile.engineering_signals — reinforces technical skills
            6. self_reported_skills — adds UNVERIFIED/WEAKLY_VERIFIED entries

        Returns skills sorted by evidence_count descending, then alphabetically.
        """
        # Accumulator: key = normalized skill name → evidence list
        evidence_map: Dict[str, List[IntelligenceEvidence]] = {}
        # Accumulator: key → highest demo level seen
        demo_level_map: Dict[str, str] = {}

        def _add(
            skill_name: str,
            evidence: List[IntelligenceEvidence],
            demo_level: str = DemonstrationLevel.CLAIMED.value,
        ) -> None:
            key = _normalize(skill_name)
            if not key:
                return
            if key not in evidence_map:
                evidence_map[key] = []
                demo_level_map[key] = DemonstrationLevel.CLAIMED.value
            evidence_map[key].extend(evidence)
            demo_level_map[key] = _max_demo_level(demo_level_map[key], demo_level)

        # ── 1. Technologies ────────────────────────────────────────────────
        for tech in profile.technologies:
            if not tech.technology:
                continue
            _add(tech.technology, tech.evidence, tech.demonstration_level)

        # ── 2. Competencies ───────────────────────────────────────────────
        # Competencies are domain-level concepts (e.g. BACKEND_DEVELOPMENT).
        # Map them as skill entries and also add their supporting technologies.
        for comp in profile.competencies:
            if not comp.competency or not comp.demonstrated:
                continue
            _add(comp.competency, comp.evidence, comp.demonstration_level)
            # Reinforce supporting technologies with the same competency evidence
            for tech_name in comp.supporting_technologies:
                _add(tech_name, comp.evidence, comp.demonstration_level)

        # ── 3. Certifications ─────────────────────────────────────────────
        # Certifications contribute lightweight evidence for their competencies.
        # Create synthetic IntelligenceEvidence objects from the cert itself.
        for cert in profile.certifications:
            cert_evidence = cert.evidence or []
            # If no evidence attached, create a minimal synthetic entry
            if not cert_evidence:
                cert_evidence = [
                    IntelligenceEvidence(
                        source=IntelligenceSourceType.CERTIFICATION,
                        source_id=cert.certification_name,
                        section="certifications",
                        quote=f"Certification: {cert.certification_name}",
                    )
                ]
            for comp_name in cert.supported_competencies:
                _add(comp_name, cert_evidence, DemonstrationLevel.REFERENCED.value)

        # ── 4. Ownership signals ──────────────────────────────────────────
        # Ownership signals reinforce technical skills implied by the signal text.
        # We do NOT invent new skills here — only reinforce what is already tracked.
        for sig in profile.ownership_signals:
            if not sig.evidence:
                continue
            # Reinforce any tracked skill whose name appears in the signal text
            for key in list(evidence_map.keys()):
                if key in _normalize(sig.signal):
                    evidence_map[key].extend(sig.evidence)
                    # Ownership signals imply at least USED level
                    demo_level_map[key] = _max_demo_level(
                        demo_level_map[key], DemonstrationLevel.USED.value
                    )

        # ── 5. Engineering signals ────────────────────────────────────────
        # Engineering signals (DEPLOYMENT, TESTING, etc.) reinforce technical skills
        for esig in profile.engineering_signals:
            if not esig.demonstrated or not esig.evidence:
                continue
            # Reinforce existing keys that appear in the signal description
            for key in list(evidence_map.keys()):
                if key in _normalize(esig.signal):
                    evidence_map[key].extend(esig.evidence)

        # ── 6. Soft skills from ownership signals (heuristic) ─────────────
        for sig in profile.ownership_signals:
            for soft_skill, pattern in _SOFT_SKILL_PATTERNS.items():
                if pattern.search(sig.signal):
                    _add(soft_skill, sig.evidence, DemonstrationLevel.REFERENCED.value)

        # ── 7. Self-reported skills ───────────────────────────────────────
        # Self-reported skills start at UNVERIFIED unless the profile already
        # contains evidence for them (in which case they inherit existing status).
        for skill in (self_reported_skills or []):
            key = _normalize(skill)
            if key and key not in evidence_map:
                # No corroborating evidence found — create minimal entry
                self_reported_ev = IntelligenceEvidence(
                    source=IntelligenceSourceType.SELF_REPORTED,
                    source_id="skills_section",
                    section="skills",
                    quote=f"Self-reported: {skill}",
                )
                _add(skill, [self_reported_ev], DemonstrationLevel.CLAIMED.value)
            # If already tracked, no action needed — profile evidence wins

        # ── Build final SkillIntelligence list ────────────────────────────
        result: List[SkillIntelligence] = []
        for key, evidence_list in evidence_map.items():
            # Deduplicate evidence by (source, source_id, quote) tuple
            seen: set = set()
            unique_evidence: List[IntelligenceEvidence] = []
            for ev in evidence_list:
                dedup_key = (ev.source, ev.source_id, ev.quote[:80])
                if dedup_key not in seen:
                    seen.add(dedup_key)
                    unique_evidence.append(ev)

            if not unique_evidence:
                continue  # Never emit a skill without evidence

            verification_status = _resolve_verification(unique_evidence)
            demo_level = demo_level_map.get(key, DemonstrationLevel.CLAIMED.value)

            result.append(
                SkillIntelligence(
                    skill=key,
                    verification_status=verification_status,
                    demonstration_level=demo_level,
                    evidence=unique_evidence,
                    evidence_count=len(unique_evidence),
                )
            )

        # Sort: most evidence first, then alphabetically
        result.sort(key=lambda s: (-s.evidence_count, s.skill))
        return result


# ---------------------------------------------------------------------------
# Convenience alias for backward compatibility during transition
# (Do not rely on this in new code — use SkillVerificationEngine directly)
# ---------------------------------------------------------------------------

class SkillAnalysisEngine(SkillVerificationEngine):
    """
    Deprecated alias for SkillVerificationEngine.
    Provided only for transitional compatibility with existing pipeline references.
    New code must use SkillVerificationEngine directly.
    """

    def analyze(
        self,
        profile: CandidateIntelligenceProfile,
        self_reported_skills: Optional[List[str]] = None,
        # Legacy kwargs silently ignored:
        **_ignored,
    ) -> List[SkillIntelligence]:
        return self.verify(profile, self_reported_skills=self_reported_skills)

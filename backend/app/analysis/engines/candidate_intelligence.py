"""
app/analysis/engines/candidate_intelligence.py
-----------------------------------------------
Candidate Intelligence Aggregator — Phase 3 Remediation.

Consumes intelligence outputs from Project, Internship, and Certification
engines and produces a unified, evidence-backed CandidateIntelligenceProfile.

Responsibilities:
    - Merge technology intelligence across all sources (highest demonstration
      level wins; evidence is accumulated)
    - Aggregate competencies (same canonical CompetencyType merged)
    - Resolve VerificationStatus for each skill using configurable evidence weights
    - Infer DomainIntelligence from competencies and technologies
    - Collect all engineering signals and workplace exposures
    - Aggregate all findings (STRENGTH, WEAKNESS, MISSING_SIGNAL)
    - Deterministically generate Recommendations from HIGH/CRITICAL findings
    - Generate CandidateSummary as the dashboard layer

Python responsibilities (no LLM involved):
    - evidence_count calculation
    - VerificationStatus resolution
    - Recommendation generation
    - CandidateSummary generation
    - DemonstrationLevel merging (max wins)

Design Rules:
    - Pure standard library. No framework dependencies.
    - All input comes from the structured intelligence objects in candidate_profile.py.
    - The output is a CandidateIntelligenceProfile ready for persistence wrapping.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.analysis.models.candidate_profile import (
    CandidateIntelligenceProfile,
    CandidateIntelligenceSnapshot,
    CandidateSummary,
    CertificationIntelligence,
    CompetencyIntelligence,
    CompetencyType,
    DemonstrationLevel,
    DomainIntelligence,
    DomainType,
    EngineeringSignal,
    Finding,
    FindingSeverity,
    FindingType,
    IntelligenceEvidence,
    OwnershipIntelligence,
    Recommendation,
    SkillIntelligence,
    TechnologyIntelligence,
    VerificationStatus,
    WorkplaceExposure,
)

# ---------------------------------------------------------------------------
# Configurable Evidence Weights (tune without code changes)
# ---------------------------------------------------------------------------

SKILL_EVIDENCE_WEIGHTS: Dict[str, float] = {
    "project": 1.0,
    "internship": 0.7,
    "certification": 0.3,
}

# Minimum weighted score thresholds for verification status
VERIFICATION_THRESHOLDS: Dict[str, float] = {
    VerificationStatus.STRONGLY_VERIFIED.value: 2.0,
    VerificationStatus.VERIFIED.value: 1.0,
    VerificationStatus.WEAKLY_VERIFIED.value: 0.3,
}

# Ordered demonstration levels for max-wins merging
_DEMO_LEVEL_ORDER = [
    DemonstrationLevel.CLAIMED.value,
    DemonstrationLevel.REFERENCED.value,
    DemonstrationLevel.USED.value,
    DemonstrationLevel.IMPLEMENTED.value,
    DemonstrationLevel.DESIGNED.value,
    DemonstrationLevel.ARCHITECTED.value,
]

# Finding severities that trigger automatic recommendations
_RECOMMENDATION_SEVERITIES = {FindingSeverity.HIGH.value, FindingSeverity.CRITICAL.value}

# Domain → competency mapping for domain inference
_DOMAIN_COMPETENCY_MAP: Dict[str, List[str]] = {
    DomainType.MACHINE_LEARNING.value: [
        CompetencyType.MACHINE_LEARNING.value,
        CompetencyType.DEEP_LEARNING.value,
        CompetencyType.MLOPS.value,
    ],
    DomainType.BACKEND.value: [
        CompetencyType.BACKEND_DEVELOPMENT.value,
        CompetencyType.API_DEVELOPMENT.value,
        CompetencyType.DATABASE_DESIGN.value,
    ],
    DomainType.FRONTEND.value: [
        CompetencyType.FRONTEND_DEVELOPMENT.value,
    ],
    DomainType.FULL_STACK.value: [
        CompetencyType.FULL_STACK_DEVELOPMENT.value,
    ],
    DomainType.DATA_ENGINEERING.value: [
        CompetencyType.DATA_ENGINEERING.value,
        CompetencyType.DATA_SCIENCE.value,
    ],
    DomainType.CLOUD.value: [
        CompetencyType.CLOUD_COMPUTING.value,
        CompetencyType.MLOPS.value,
    ],
    DomainType.DEVOPS.value: [
        CompetencyType.DEVOPS.value,
    ],
    DomainType.SECURITY.value: [
        CompetencyType.CYBERSECURITY.value,
    ],
    DomainType.MOBILE.value: [
        CompetencyType.MOBILE_DEVELOPMENT.value,
    ],
    DomainType.DISTRIBUTED_SYSTEMS.value: [
        CompetencyType.DISTRIBUTED_SYSTEMS.value,
        CompetencyType.SYSTEM_DESIGN.value,
    ],
    DomainType.DATA_SCIENCE.value: [
        CompetencyType.DATA_SCIENCE.value,
        CompetencyType.MACHINE_LEARNING.value,
    ],
    DomainType.MLOPS.value: [
        CompetencyType.MLOPS.value,
        CompetencyType.DEVOPS.value,
    ],
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _max_demo_level(a: str, b: str) -> str:
    """Return the higher of two DemonstrationLevel values."""
    idx_a = _DEMO_LEVEL_ORDER.index(a) if a in _DEMO_LEVEL_ORDER else 0
    idx_b = _DEMO_LEVEL_ORDER.index(b) if b in _DEMO_LEVEL_ORDER else 0
    return _DEMO_LEVEL_ORDER[max(idx_a, idx_b)]


def _resolve_verification(evidence: List[IntelligenceEvidence]) -> str:
    """
    Compute VerificationStatus from evidence sources using SKILL_EVIDENCE_WEIGHTS.

    Returns the highest threshold that the cumulative weighted score satisfies.
    """
    total = sum(SKILL_EVIDENCE_WEIGHTS.get(ev.source, 0.0) for ev in evidence)
    for status, threshold in sorted(
        VERIFICATION_THRESHOLDS.items(), key=lambda x: x[1], reverse=True
    ):
        if total >= threshold:
            return status
    return VerificationStatus.UNVERIFIED.value


# ---------------------------------------------------------------------------
# Aggregator
# ---------------------------------------------------------------------------

class CandidateIntelligenceAggregator:
    """
    Aggregates intelligence from all analysis engines into a unified profile.

    Usage:
        agg = CandidateIntelligenceAggregator()
        agg.add_project_intelligence(project_id, tech_list, competency_list, ...)
        agg.add_internship_intelligence(internship_id, ...)
        agg.add_certification_intelligence(cert_list)
        profile = agg.build()
        snapshot = agg.wrap_snapshot(profile, resume_id)
    """

    def __init__(self) -> None:
        # Internal keyed stores for deduplication
        self._technologies: Dict[str, TechnologyIntelligence] = {}
        self._competencies: Dict[str, CompetencyIntelligence] = {}
        self._skills: Dict[str, List[IntelligenceEvidence]] = {}
        self._certifications: List[CertificationIntelligence] = []
        self._ownership_signals: List[OwnershipIntelligence] = []
        self._engineering_signals: List[EngineeringSignal] = []
        self._workplace_exposure: Dict[str, WorkplaceExposure] = {}
        self._findings: List[Finding] = []

    # -- Public feed methods -----------------------------------------------

    def add_technologies(
        self,
        technologies: List[TechnologyIntelligence],
    ) -> None:
        """Merge technology intelligence. Highest demonstration level wins."""
        for tech in technologies:
            key = tech.technology.lower().strip()
            if not key:
                continue
            if key in self._technologies:
                existing = self._technologies[key]
                existing.demonstration_level = _max_demo_level(
                    existing.demonstration_level, tech.demonstration_level
                )
                existing.evidence.extend(tech.evidence)
                for st in tech.source_types:
                    if st not in existing.source_types:
                        existing.source_types.append(st)
            else:
                self._technologies[key] = TechnologyIntelligence(
                    technology=tech.technology,
                    demonstration_level=tech.demonstration_level,
                    evidence=list(tech.evidence),
                    source_types=list(tech.source_types),
                )

    def add_competencies(self, competencies: List[CompetencyIntelligence]) -> None:
        """Merge competencies. Same canonical type is accumulated, not duplicated."""
        for comp in competencies:
            key = comp.competency.upper().strip()
            if not key:
                continue
            if key in self._competencies:
                existing = self._competencies[key]
                existing.demonstration_level = _max_demo_level(
                    existing.demonstration_level, comp.demonstration_level
                )
                existing.evidence.extend(comp.evidence)
                for t in comp.supporting_technologies:
                    if t not in existing.supporting_technologies:
                        existing.supporting_technologies.append(t)
                for p in comp.supporting_projects:
                    if p not in existing.supporting_projects:
                        existing.supporting_projects.append(p)
                if comp.demonstrated:
                    existing.demonstrated = True
            else:
                self._competencies[key] = CompetencyIntelligence(
                    competency=comp.competency,
                    demonstrated=comp.demonstrated,
                    demonstration_level=comp.demonstration_level,
                    evidence=list(comp.evidence),
                    supporting_technologies=list(comp.supporting_technologies),
                    supporting_projects=list(comp.supporting_projects),
                )

    def add_skill_evidence(
        self, skill: str, evidence: List[IntelligenceEvidence]
    ) -> None:
        """Accumulate evidence for a named skill (used by skill verification engine)."""
        key = skill.lower().strip()
        if key not in self._skills:
            self._skills[key] = []
        self._skills[key].extend(evidence)

    def add_certifications(self, certifications: List[CertificationIntelligence]) -> None:
        self._certifications.extend(certifications)

    def add_ownership_signals(self, signals: List[OwnershipIntelligence]) -> None:
        self._ownership_signals.extend(signals)

    def add_engineering_signals(self, signals: List[EngineeringSignal]) -> None:
        self._engineering_signals.extend(signals)

    def add_workplace_exposure(self, exposures: List[WorkplaceExposure]) -> None:
        """Merge workplace exposure. Same exposure_type is deduplicated."""
        for exp in exposures:
            key = exp.exposure_type.lower().strip()
            if key in self._workplace_exposure:
                self._workplace_exposure[key].evidence.extend(exp.evidence)
            else:
                self._workplace_exposure[key] = WorkplaceExposure(
                    exposure_type=exp.exposure_type,
                    evidence=list(exp.evidence),
                )

    def add_findings(self, findings: List[Finding]) -> None:
        self._findings.extend(findings)

    # -- Build method -------------------------------------------------------

    def build(self) -> CandidateIntelligenceProfile:
        """Produce the final CandidateIntelligenceProfile."""
        technologies = list(self._technologies.values())
        competencies = list(self._competencies.values())
        skills = self._build_skills()
        domains = self._infer_domains(competencies, technologies)
        recommendations = self._derive_recommendations()
        summary = self._build_summary(technologies, competencies, domains)

        return CandidateIntelligenceProfile(
            technologies=technologies,
            competencies=competencies,
            domains=domains,
            skills=skills,
            certifications=self._certifications,
            ownership_signals=self._ownership_signals,
            engineering_signals=self._engineering_signals,
            workplace_exposure=list(self._workplace_exposure.values()),
            findings=self._findings,
            recommendations=recommendations,
            summary=summary,
        )

    def wrap_snapshot(
        self,
        profile: CandidateIntelligenceProfile,
        resume_id: str,
        profile_version: str = "1.0.0",
        analysis_version: str = "3.0.0",
    ) -> CandidateIntelligenceSnapshot:
        """Wrap a profile in a persistence snapshot."""
        return CandidateIntelligenceSnapshot(
            snapshot_id=str(uuid.uuid4()),
            resume_id=resume_id,
            profile_version=profile_version,
            analysis_version=analysis_version,
            profile=profile,
            generated_at=datetime.now(timezone.utc),
        )

    # -- Private build helpers ---------------------------------------------

    def _build_skills(self) -> List[SkillIntelligence]:
        """Resolve VerificationStatus and DemonstrationLevel for every skill."""
        skills: List[SkillIntelligence] = []
        for skill_name, evidence_list in self._skills.items():
            verification_status = _resolve_verification(evidence_list)
            # Determine demo level from evidence source mapping
            demo_level = DemonstrationLevel.CLAIMED.value
            # If a technology with same name exists, inherit its level
            if skill_name in self._technologies:
                demo_level = self._technologies[skill_name].demonstration_level
            skills.append(
                SkillIntelligence(
                    skill=skill_name,
                    verification_status=verification_status,
                    demonstration_level=demo_level,
                    evidence=evidence_list,
                    evidence_count=len(evidence_list),
                )
            )
        return sorted(skills, key=lambda s: s.evidence_count, reverse=True)

    def _infer_domains(
        self,
        competencies: List[CompetencyIntelligence],
        technologies: List[TechnologyIntelligence],
    ) -> List[DomainIntelligence]:
        """
        Deterministically infer domains from the competency → domain mapping.

        A domain is included if at least one of its mapped competencies is
        demonstrated. Technologies are included in the domain if they appear
        in the supporting_technologies of a domain-relevant competency.
        """
        comp_names = {c.competency.upper() for c in competencies if c.demonstrated}
        tech_names = [t.technology for t in technologies]

        domains: List[DomainIntelligence] = []
        for domain_type, mapped_comps in _DOMAIN_COMPETENCY_MAP.items():
            matched = [c for c in mapped_comps if c in comp_names]
            if not matched:
                continue

            # Gather supporting evidence from matched competencies
            evidence: List[IntelligenceEvidence] = []
            supporting_techs: List[str] = []
            for comp in competencies:
                if comp.competency.upper() in matched:
                    evidence.extend(comp.evidence)
                    supporting_techs.extend(comp.supporting_technologies)

            domains.append(
                DomainIntelligence(
                    domain=domain_type,
                    supporting_competencies=matched,
                    supporting_technologies=list(set(supporting_techs)),
                    evidence=evidence,
                )
            )
        return domains

    def _derive_recommendations(self) -> List[Recommendation]:
        """
        Deterministically generate Recommendations from HIGH/CRITICAL findings.

        Only WEAKNESS and MISSING_SIGNAL findings of HIGH or CRITICAL severity
        produce recommendations. The recommendation content is derived from the
        finding title and description — no LLM involved.
        """
        recommendations: List[Recommendation] = []
        for finding in self._findings:
            if (
                finding.type in {FindingType.WEAKNESS.value, FindingType.MISSING_SIGNAL.value}
                and finding.severity in _RECOMMENDATION_SEVERITIES
            ):
                recommendations.append(
                    Recommendation(
                        title=f"Address: {finding.title}",
                        description=finding.description,
                        derived_from=[finding.title],
                        estimated_impact="Improves hiring signal and domain readiness.",
                        priority=finding.severity,
                        target_competencies=[],  # Populated by domain-specific scoring layer
                    )
                )
        return recommendations

    def _build_summary(
        self,
        technologies: List[TechnologyIntelligence],
        competencies: List[CompetencyIntelligence],
        domains: List[DomainIntelligence],
    ) -> CandidateSummary:
        """
        Build the dashboard CandidateSummary deterministically.

        - primary_domains: domains with the most supporting competencies
        - strongest_competencies: demonstrated competencies at IMPLEMENTED+ level
        - strongest_technologies: technologies at IMPLEMENTED+ level
        - largest_gaps: MISSING_SIGNAL findings with HIGH/CRITICAL severity
        - readiness_highlights: STRENGTH findings with HIGH/CRITICAL severity
        """
        _high_demo = {
            DemonstrationLevel.IMPLEMENTED.value,
            DemonstrationLevel.DESIGNED.value,
            DemonstrationLevel.ARCHITECTED.value,
        }

        primary_domains = sorted(
            domains,
            key=lambda d: len(d.supporting_competencies),
            reverse=True,
        )[:3]

        strongest_competencies = [
            c.competency
            for c in competencies
            if c.demonstrated and c.demonstration_level in _high_demo
        ][:5]

        strongest_technologies = [
            t.technology
            for t in sorted(
                technologies,
                key=lambda t: _DEMO_LEVEL_ORDER.index(t.demonstration_level)
                if t.demonstration_level in _DEMO_LEVEL_ORDER else 0,
                reverse=True,
            )
            if t.demonstration_level in _high_demo
        ][:5]

        largest_gaps = [
            f.title
            for f in self._findings
            if f.type == FindingType.MISSING_SIGNAL.value
            and f.severity in _RECOMMENDATION_SEVERITIES
        ][:5]

        readiness_highlights = [
            f.title
            for f in self._findings
            if f.type == FindingType.STRENGTH.value
            and f.severity in _RECOMMENDATION_SEVERITIES
        ][:5]

        return CandidateSummary(
            primary_domains=[d.domain for d in primary_domains],
            strongest_competencies=strongest_competencies,
            strongest_technologies=strongest_technologies,
            largest_gaps=largest_gaps,
            readiness_highlights=readiness_highlights,
        )

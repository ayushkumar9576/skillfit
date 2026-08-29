"""
app/analysis/engines/soft_skill_engine.py
-----------------------------------------
Soft Skill Engine — Phase 3 Remediation.

Extracts soft skills deterministically from ownership signals already
present in the CandidateIntelligenceProfile.

No LLM calls.
No legacy report structures.
No confidence scores.
"""

import re
from typing import List

from app.analysis.models.candidate_profile import (
    CandidateIntelligenceProfile,
    DemonstrationLevel,
    IntelligenceEvidence,
    SkillIntelligence,
    VerificationStatus,
)

# Heuristic patterns — same set as before, but now run over structured signals
SOFT_SKILL_HEURISTICS = {
    "Leadership": re.compile(
        r'\b(led|lead|leading|directed|managed|orchestrated|spearheaded|guided|mentored|coordinated)\b',
        re.IGNORECASE,
    ),
    "Communication": re.compile(
        r'\b(communicated|presented|negotiated|documented|reported|articulated|facilitated|pitched)\b',
        re.IGNORECASE,
    ),
    "Ownership": re.compile(
        r'\b(owned|ownership|accountable|drove|delivered|sole|autonomous|end-to-end)\b',
        re.IGNORECASE,
    ),
    "Collaboration": re.compile(
        r'\b(collaborated|teamwork|team player|partnered|cross-functional|pair programming|co-authored)\b',
        re.IGNORECASE,
    ),
    "Problem Solving": re.compile(
        r'\b(solved|resolved|troubleshot|debugged|optimized|overcame|analyzed|investigated)\b',
        re.IGNORECASE,
    ),
    "Mentorship": re.compile(
        r'\b(mentored|taught|tutored|trained|guided|onboarded|coached)\b',
        re.IGNORECASE,
    ),
}


class SoftSkillEngine:
    """
    Extracts soft skills from ownership signals in the CandidateIntelligenceProfile.

    Inputs:  CandidateIntelligenceProfile (ownership_signals, findings)
    Outputs: List[SkillIntelligence] with VerificationStatus and DemonstrationLevel

    All evidence is attached as IntelligenceEvidence from the profile's signals.
    No AnalysisEvidence, no confidence scores, no Beginner/Intermediate/Advanced.
    """

    def analyze(self, profile: CandidateIntelligenceProfile) -> List[SkillIntelligence]:
        """
        Scan ownership signals and STRENGTH findings for soft skill indicators.
        Returns one SkillIntelligence per matched soft skill.
        """
        accumulated: dict[str, List[IntelligenceEvidence]] = {}

        def _add(skill: str, evidence: List[IntelligenceEvidence]) -> None:
            if skill not in accumulated:
                accumulated[skill] = []
            accumulated[skill].extend(evidence)

        # Scan ownership signals
        for sig in profile.ownership_signals:
            for skill_name, pattern in SOFT_SKILL_HEURISTICS.items():
                if pattern.search(sig.signal):
                    _add(skill_name, sig.evidence)

        # Also scan STRENGTH findings for corroborating soft signals
        for finding in profile.findings:
            if finding.type != "STRENGTH":
                continue
            for skill_name, pattern in SOFT_SKILL_HEURISTICS.items():
                text = f"{finding.title} {finding.description}"
                if pattern.search(text):
                    _add(skill_name, finding.evidence)

        # Build SkillIntelligence output
        result: List[SkillIntelligence] = []
        for skill_name, evidence_list in accumulated.items():
            # Deduplicate
            seen: set = set()
            unique: List[IntelligenceEvidence] = []
            for ev in evidence_list:
                key = (ev.source, ev.source_id, ev.quote[:80])
                if key not in seen:
                    seen.add(key)
                    unique.append(ev)

            source_types = {ev.source for ev in unique}
            # Multi-source soft skill → VERIFIED; single source → WEAKLY_VERIFIED
            if len(source_types) >= 2:
                status = VerificationStatus.VERIFIED.value
            else:
                status = VerificationStatus.WEAKLY_VERIFIED.value

            result.append(
                SkillIntelligence(
                    skill=skill_name,
                    verification_status=status,
                    demonstration_level=DemonstrationLevel.REFERENCED.value,
                    evidence=unique,
                    evidence_count=len(unique),
                )
            )

        result.sort(key=lambda s: (-s.evidence_count, s.skill))
        return result

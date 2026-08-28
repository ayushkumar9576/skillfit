"""
app/analysis/engines/soft_skill_engine.py
-----------------------------------------
The Soft Skill Engine (Phase 3.X).
Extracts soft skills deterministically from Project and Internship reports using heuristics,
with optional LLM-assisted classification of the evidence.
"""

import logging
import re
from typing import List, Dict, Set, Tuple

from app.analysis.models.base import AnalysisEvidence
from app.analysis.models.project_models import ProjectIntelligenceReport
from app.analysis.models.internship_models import InternshipIntelligenceReport
from app.analysis.models.skill_models import (
    SkillProfile,
    SkillEvidenceSource,
)

logger = logging.getLogger(__name__)

# Core soft skills and their heuristic regex triggers
SOFT_SKILL_HEURISTICS = {
    "Leadership": re.compile(r'\b(led|lead|leading|directed|managed|orchestrated|spearheaded|guided|mentored|coordinated)\b', re.IGNORECASE),
    "Communication": re.compile(r'\b(communicated|presented|negotiated|documented|reported|articulated|facilitated|pitched)\b', re.IGNORECASE),
    "Ownership": re.compile(r'\b(owned|ownership|accountable|drove|delivered|sole|autonomous|end-to-end)\b', re.IGNORECASE),
    "Collaboration": re.compile(r'\b(collaborated|teamwork|team player|partnered|cross-functional|pair programming|co-authored)\b', re.IGNORECASE),
    "Problem Solving": re.compile(r'\b(solved|resolved|troubleshot|debugged|optimized|overcame|analyzed|investigated)\b', re.IGNORECASE),
    "Mentorship": re.compile(r'\b(mentored|taught|tutored|trained|guided|onboarded|coached)\b', re.IGNORECASE),
}

def calculate_diversity_score(source_count: int) -> float:
    if source_count >= 3:
        return 1.0
    if source_count == 2:
        return 0.8
    return 0.5

def calculate_evidence_score(evidence_count: int) -> float:
    if evidence_count >= 5:
        return 1.0
    if evidence_count >= 3:
        return 0.7
    return 0.4


class SoftSkillEngine:
    """
    Extracts soft skills from projects and internships.
    Currently implements Layer 1 (Heuristic deterministic extraction).
    Layer 2 (LLM classification) can be integrated here via LLMService.
    """

    def analyze(
        self,
        project_reports: List[ProjectIntelligenceReport],
        internship_reports: List[InternshipIntelligenceReport],
    ) -> List[SkillProfile]:
        
        extracted_data: Dict[str, List[Tuple[str, str, float, List[AnalysisEvidence]]]] = {}

        def _add_evidence(skill_name: str, src_type: str, src_name: str, src_conf: float, evs: List[AnalysisEvidence]):
            if skill_name not in extracted_data:
                extracted_data[skill_name] = []
            extracted_data[skill_name].append((src_type, src_name, src_conf, evs))

        def _scan_evidence_lines(source_type: str, source_name: str, items: List[AnalysisEvidence]):
            """Scans lines for heuristic matches."""
            for ev in items:
                text = ev.evidence_text or ""
                for skill, regex in SOFT_SKILL_HEURISTICS.items():
                    if regex.search(text):
                        _add_evidence(skill, source_type, source_name, 0.7, [ev])

        # Scan Projects
        for p in project_reports:
            all_project_evidences: List[AnalysisEvidence] = []
            # Collect highlights and descriptions mapped as AnalysisEvidence
            for h in p.source_project.highlights:
                all_project_evidences.append(AnalysisEvidence(evidence_text=h, source_section="projects"))
            if p.source_project.description:
                all_project_evidences.append(AnalysisEvidence(evidence_text=p.source_project.description, source_section="projects"))
            
            _scan_evidence_lines("Project", p.project_title, all_project_evidences)

        # Scan Internships
        for i in internship_reports:
            all_internship_evidences: List[AnalysisEvidence] = []
            for h in i.source_internship.highlights:
                all_internship_evidences.append(AnalysisEvidence(evidence_text=h, source_section="internships"))
            if i.source_internship.description:
                all_internship_evidences.append(AnalysisEvidence(evidence_text=i.source_internship.description, source_section="internships"))
            
            _scan_evidence_lines("Internship", i.internship_role or i.internship_organization, all_internship_evidences)

        # Build Final Profiles
        final_skills: List[SkillProfile] = []
        for skill_name, sources in extracted_data.items():
            seen_evidence: Set[str] = set()
            merged_sources: Dict[Tuple[str, str], SkillEvidenceSource] = {}
            
            for src_type, src_name, src_conf, evs in sources:
                src_key = (src_type, src_name)
                if src_key not in merged_sources:
                    merged_sources[src_key] = SkillEvidenceSource(
                        source_type=src_type,
                        source_name=src_name,
                        source_id=None,
                        source_confidence=src_conf,
                        evidences=[]
                    )
                merged_sources[src_key].source_confidence = max(merged_sources[src_key].source_confidence, src_conf)
                
                for e in evs:
                    if e.evidence_text not in seen_evidence:
                        seen_evidence.add(e.evidence_text)
                        merged_sources[src_key].evidences.append(e)

            final_evidences = list(merged_sources.values())
            source_count = len(final_evidences)
            evidence_count = len(seen_evidence)

            report_conf_avg = sum(s.source_confidence for s in final_evidences) / source_count if source_count > 0 else 0.0
            div_score = calculate_diversity_score(source_count)
            ev_score = calculate_evidence_score(evidence_count)
            
            conf_score = (div_score + ev_score + report_conf_avg) / 3

            if conf_score >= 0.80:
                conf_level = "HIGH"
            elif conf_score >= 0.60:
                conf_level = "MEDIUM"
            else:
                conf_level = "LOW"

            if source_count >= 3 and evidence_count >= 5:
                depth = "Advanced"
            elif source_count >= 2 and evidence_count >= 2:
                depth = "Intermediate"
            else:
                depth = "Beginner"

            if conf_score > 0.75 and source_count >= 2:
                hiring_signal = "High"
            elif conf_score >= 0.5:
                hiring_signal = "Medium"
            else:
                hiring_signal = "Low"

            final_skills.append(
                SkillProfile(
                    skill_name=skill_name,
                    skill_type="soft_skill",
                    confidence_score=round(conf_score, 2),
                    confidence_level=conf_level,
                    evidence_count=evidence_count,
                    source_count=source_count,
                    skill_depth=depth,
                    hiring_signal=hiring_signal,
                    evidences=final_evidences
                )
            )

        final_skills.sort(key=lambda s: (-s.confidence_score, -s.evidence_count, s.skill_name))
        return final_skills

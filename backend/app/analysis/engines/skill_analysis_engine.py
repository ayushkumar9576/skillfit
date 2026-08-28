import json
import logging
import re
from typing import List, Dict, Set, Tuple

from app.analysis.models.project_models import ProjectIntelligenceReport
from app.analysis.models.internship_models import InternshipIntelligenceReport
from app.analysis.models.certification_models import CertificationIntelligenceReport
from app.analysis.models.skill_models import (
    SkillAnalysisResult,
    SkillProfile,
    SkillEvidenceSource,
)
from app.analysis.models.base import AnalysisEvidence
logger = logging.getLogger(__name__)

from app.analysis.engines.normalization_engine import normalize_skill_name, get_display_name

def calculate_diversity_score(source_count: int) -> float:
    if source_count >= 3:
        return 1.0
    if source_count == 2:
        return 0.8
    return 0.5

def calculate_evidence_score(evidence_count: int) -> float:
    if evidence_count >= 6:
        return 1.0
    if evidence_count >= 3:
        return 0.7
    return 0.4

class SkillAnalysisEngine:
    """
    Deterministic intelligence aggregation engine (Phase 3.10) that
    merges skills discovered by upstream engines into a unified profile.
    """

    def _is_valid_skill(self, raw_skill: str) -> bool:
        s = normalize_skill_name(raw_skill)
        return bool(s)

    def analyze(
        self,
        project_reports: List[ProjectIntelligenceReport],
        internship_reports: List[InternshipIntelligenceReport],
        certification_reports: List[CertificationIntelligenceReport],
        self_reported_skills_text: str = ""
    ) -> SkillAnalysisResult:
        
        # 1. Fast Exit
        if not project_reports and not internship_reports and not certification_reports and not self_reported_skills_text.strip():
            return SkillAnalysisResult(skills=[], total_skills_count=0)

        # Temp structures for aggregation
        # Mapping: normalized_skill_name -> list of (source_type, source_name, source_id, confidence, list[AnalysisEvidence])
        extracted_data: Dict[str, List[Tuple[str, str, str, float, List[AnalysisEvidence]]]] = {}

        # Helpers to add data
        def _add_evidence(skill_name: str, src_type: str, src_name: str, src_id: str, src_conf: float, evs: List[AnalysisEvidence]):
            if not self._is_valid_skill(skill_name):
                return
            norm = normalize_skill_name(skill_name)
            if norm not in extracted_data:
                extracted_data[norm] = []
            extracted_data[norm].append((src_type, src_name, src_id, src_conf, evs))

        # 2. Collect from Projects
        for p in project_reports:
            src_name = p.project_title
            src_id = None
            # Collect from skill_evidence.items
            for item in p.skill_evidence.items:
                _add_evidence(item.skill, "Project", src_name, src_id, item.confidence, item.evidence)
            # Collect from technology_usage
            for tech in p.technology_usage:
                _add_evidence(tech.technology, "Project", src_name, src_id, tech.confidence, tech.evidence)

        # 3. Collect from Internships
        for i in internship_reports:
            src_name = i.internship_role or i.internship_organization
            src_id = None
            for item in i.skill_evidence.items:
                _add_evidence(item.skill, "Internship", src_name, src_id, item.confidence, item.evidence)
            for tech in i.technology_usage:
                _add_evidence(tech.technology, "Internship", src_name, src_id, tech.confidence, tech.evidence)

        # 4. Collect from Certifications
        for c in certification_reports:
            src_name = c.certification_name
            src_id = None
            for item in c.skill_signals:
                _add_evidence(item.name, "Certification", src_name, src_id, item.confidence, item.evidence)

        # 4.5 Collect from Self-Reported Skills
        if self_reported_skills_text.strip():
            raw_skills = re.split(r'[,\n|/;]+', self_reported_skills_text)
            for skill in raw_skills:
                skill = skill.strip()
                if skill:
                    _add_evidence(skill, "self_reported", "skills_section", None, 0.25, [])

        # 5. Build Final Profiles
        final_skills: List[SkillProfile] = []
        for norm_skill, sources in extracted_data.items():
            
            seen_evidence_keys: Set[Tuple[str, str, int]] = set()
            merged_sources: Dict[Tuple[str, str], SkillEvidenceSource] = {}
            
            for src_type, src_name, src_id, src_conf, evs in sources:
                src_key = (src_type, src_name)
                if src_key not in merged_sources:
                    merged_sources[src_key] = SkillEvidenceSource(
                        source_type=src_type,
                        source_name=src_name,
                        source_id=src_id,
                        source_confidence=src_conf,
                        evidences=[]
                    )
                # Ensure we keep the max confidence if a project provides the same skill via both skill_evidence and technology_usage
                merged_sources[src_key].source_confidence = max(merged_sources[src_key].source_confidence, src_conf)
                
                # Deduplicate evidence lines
                for e in evs:
                    ev_key = (src_type, src_name, e.line_number)
                    if ev_key not in seen_evidence_keys:
                        seen_evidence_keys.add(ev_key)
                        merged_sources[src_key].evidences.append(e)

            # Build evidence block
            final_evidences = list(merged_sources.values())
            
            source_count = len(final_evidences)
            evidence_count = len(seen_evidence_keys)

            # Report confidence score (average of source confidences)
            report_conf_avg = sum(s.source_confidence for s in final_evidences) / source_count if source_count > 0 else 0.0

            # Compute Confidence
            div_score = calculate_diversity_score(source_count)
            ev_score = calculate_evidence_score(evidence_count)
            conf_score = (div_score + ev_score + report_conf_avg) / 3

            if conf_score >= 0.80:
                conf_level = "HIGH"
            elif conf_score >= 0.60:
                conf_level = "MEDIUM"
            else:
                conf_level = "LOW"

            # Compute Depth
            if source_count >= 3 and evidence_count >= 6:
                depth = "Advanced"
            elif source_count >= 2 and evidence_count >= 3:
                depth = "Intermediate"
            else:
                depth = "Beginner"

            # Compute Hiring Signal
            if conf_score > 0.75 and source_count > 1 and evidence_count >= 3:
                hiring_signal = "High"
            elif conf_score >= 0.5 or evidence_count >= 2:
                hiring_signal = "Medium"
            else:
                hiring_signal = "Low"

            # Construct profile (using properly capitalized display name)
            display_name = get_display_name(norm_skill)

            final_skills.append(
                SkillProfile(
                    skill_name=display_name,
                    confidence_score=round(conf_score, 2),
                    confidence_level=conf_level,
                    evidence_count=evidence_count,
                    source_count=source_count,
                    skill_depth=depth,
                    hiring_signal=hiring_signal,
                    evidences=final_evidences
                )
            )

        # 6. Deterministic Ordering
        final_skills.sort(
            key=lambda s: (
                -s.confidence_score,
                -s.evidence_count,
                s.skill_name,
            )
        )

        return SkillAnalysisResult(skills=final_skills, total_skills_count=len(final_skills))

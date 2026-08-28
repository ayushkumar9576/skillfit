"""
app/analysis/engines/synthesis_engine.py
----------------------------------------
Aggregates outputs from upstream engines to synthesize the final Candidate Profile.
"""

from typing import Dict, Any, List
import logging

from app.analysis.models.skill_models import SkillAnalysisResult
from app.analysis.models.project_models import ProjectIntelligenceReport
from app.analysis.models.internship_models import InternshipIntelligenceReport
from app.analysis.models.certification_models import CertificationIntelligenceReport

from app.analysis.engines.domain_engine import DomainEngine
from app.analysis.engines.affinity_engine import AffinityEngine
from app.analysis.engines.soft_skill_engine import SoftSkillEngine

logger = logging.getLogger(__name__)

class SynthesisEngine:
    def __init__(self):
        self.domain_engine = DomainEngine()
        self.affinity_engine = AffinityEngine()
        self.soft_skill_engine = SoftSkillEngine()

    def synthesize(
        self,
        tech_skills: SkillAnalysisResult,
        project_reports: List[ProjectIntelligenceReport],
        internship_reports: List[InternshipIntelligenceReport],
        certification_reports: List[CertificationIntelligenceReport]
    ) -> Dict[str, Any]:
        
        # Extract soft skills
        soft_skills_list = self.soft_skill_engine.analyze(project_reports, internship_reports)
        
        # Combine tech and soft skills for domains/affinities if needed
        # We generally use just tech skills for domains/affinities
        
        primary_domain_str, domains_list = self.domain_engine.analyze(tech_skills)
        affinities_list = self.affinity_engine.analyze(tech_skills)
        
        # Format primary and secondary domains
        primary_domain = None
        secondary_domains = []
        if domains_list:
            primary_domain = domains_list[0]
            secondary_domains = domains_list[1:]

        # Format strongest skills (top tech skills)
        strongest_skills = []
        for s in tech_skills.skills[:10]:
            strongest_skills.append({
                "name": s.skill_name,
                "confidence": s.confidence_score,
                "evidence_count": s.evidence_count,
                "depth": s.skill_depth
            })

        # Format soft skills
        formatted_soft_skills = []
        for s in soft_skills_list:
            formatted_soft_skills.append({
                "name": s.skill_name,
                "confidence": s.confidence_score,
                "evidence_count": s.evidence_count
            })

        # Build role affinities as dict mapping role to confidence & evidence
        role_affinities = {}
        for aff in affinities_list:
            role_affinities[aff["role"]] = {
                "confidence": aff["confidence"],
                "evidence": aff["evidence"]
            }

        # Build evidence summary
        evidence_summary = {
            "total_projects": len(project_reports),
            "total_internships": len(internship_reports),
            "total_certifications": len(certification_reports)
        }

        return {
            "primary_domain": primary_domain,
            "secondary_domains": secondary_domains,
            "strongest_skills": strongest_skills,
            "soft_skills": formatted_soft_skills,
            "role_affinities": role_affinities,
            "evidence_summary": evidence_summary
        }

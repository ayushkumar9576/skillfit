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

from app.analysis.engines.affinity_engine import AffinityEngine
from app.analysis.engines.soft_skill_engine import SoftSkillEngine

logger = logging.getLogger(__name__)

class SynthesisEngine:
    def __init__(self):
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
        affinities_list = self.affinity_engine.analyze(tech_skills)
        
        # Phase 3.12: Deterministic Domain Aggregation
        domain_points_map = {}
        domain_confidence_map = {}
        domain_tiers = {}
        project_tiers = {}
        industry_exposure_levels = {}
        domain_signals = set()
        
        # Helper to accumulate points with diminishing returns
        def add_points(domain, points, conf):
            if domain not in domain_points_map:
                domain_points_map[domain] = []
                domain_confidence_map[domain] = []
            domain_points_map[domain].append(points)
            domain_confidence_map[domain].append(conf)
            
        # Process Projects
        proj_pts = {
            "BEGINNER": 20,
            "INTERMEDIATE": 40,
            "ADVANCED": 60,
            "HIGH_IMPACT": 80,
            "EXCEPTIONAL": 100
        }
        for idx, p in enumerate(project_reports):
            dom = getattr(p, "primary_domain", "").strip().upper()
            tier = getattr(p, "project_tier", "BEGINNER").strip().upper()
            conf = getattr(p, "domain_confidence", 1.0)
            sigs = getattr(p, "domain_signals", [])
            
            if dom:
                pts = proj_pts.get(tier, 20)
                add_points(dom, pts, conf)
                project_tiers[f"project_{idx}"] = tier
                if dom not in domain_tiers or pts > proj_pts.get(domain_tiers[dom], 0):
                    domain_tiers[dom] = tier
                for sig in sigs:
                    domain_signals.add(sig)
                    
        # Process Internships
        intern_pts = {
            "LIMITED": 30,
            "MODERATE": 50,
            "STRONG": 70,
            "EXTENSIVE": 90
        }
        for idx, i in enumerate(internship_reports):
            dom = getattr(i, "primary_domain", "").strip().upper()
            exp = getattr(i, "industry_exposure_level", "LIMITED").strip().upper()
            conf = getattr(i, "domain_confidence", 1.0)
            
            if dom:
                pts = intern_pts.get(exp, 30)
                add_points(dom, pts, conf)
                industry_exposure_levels[f"internship_{idx}"] = exp
                
        # Calculate Final Domain Scores
        domain_scores = {}
        decay_weights = [1.0, 0.5, 0.25]
        total_domain_score = 0.0
        
        for dom, pts_list in domain_points_map.items():
            pts_list.sort(reverse=True)
            score = 0.0
            for i, p in enumerate(pts_list):
                weight = decay_weights[i] if i < len(decay_weights) else 0.0
                score += p * weight
            domain_scores[dom] = score
            total_domain_score += score
            
        # Determine Primary and Secondary Domains
        primary_domain = None
        secondary_domains = []
        candidate_primary_domain_confidence = 0.0
        
        if domain_scores:
            sorted_domains = sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)
            primary_domain = sorted_domains[0][0]
            primary_score = sorted_domains[0][1]
            
            for dom, score in sorted_domains[1:]:
                if score >= 40:
                    secondary_domains.append(dom)
                    
            # Candidate Confidence
            avg_llm_conf = sum(domain_confidence_map[primary_domain]) / len(domain_confidence_map[primary_domain])
            purity = primary_score / total_domain_score if total_domain_score > 0 else 0.0
            candidate_primary_domain_confidence = round(purity * avg_llm_conf, 2)

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
            "domain_tiers": domain_tiers,
            "domain_scores": domain_scores,
            "domain_signals": list(domain_signals),
            "project_tiers": project_tiers,
            "industry_exposure_levels": industry_exposure_levels,
            "candidate_primary_domain_confidence": candidate_primary_domain_confidence,
            "strongest_skills": strongest_skills,
            "soft_skills": formatted_soft_skills,
            "role_affinities": role_affinities,
            "evidence_summary": evidence_summary
        }

from typing import Dict, Any, List
from app.analysis.models.candidate_profile import CandidateIntelligenceProfile
from app.matching.vectorization.schema import CandidateVectorPayload, VECTOR_SCHEMA_VERSION
from app.matching.vectorization.canon import normalize_technology_name

class CandidateVectorizer:
    DEMONSTRATION_MULTIPLIERS = {
        "CLAIMED": 0.2,
        "REFERENCED": 0.4,
        "USED": 0.6,
        "IMPLEMENTED": 0.8,
        "DESIGNED": 0.9,
        "ARCHITECTED": 1.0,
    }

    @classmethod
    def _normalize_tech(cls, name: str) -> str:
        return normalize_technology_name(name)

    @classmethod
    def generate(cls, profile: CandidateIntelligenceProfile) -> CandidateVectorPayload:
        technologies = {}
        for tech in profile.technologies:
            normalized = cls._normalize_tech(tech.technology)
            score = cls.DEMONSTRATION_MULTIPLIERS.get(tech.demonstration_level, 0.2)
            if technologies.get(normalized, 0.0) < score:
                technologies[normalized] = score

        competencies = {}
        for comp in profile.competencies:
            score = cls.DEMONSTRATION_MULTIPLIERS.get(comp.demonstration_level, 0.2)
            if competencies.get(comp.competency, 0.0) < score:
                competencies[comp.competency] = score
                
        domains = {}
        for domain in profile.domains:
            domains[domain.domain] = 1.0
            
        # Domain hierarchy expansion: fine-grained domains map to high-level domain taxonomy
        sw_subdomains = {
            "BACKEND", "FRONTEND", "FULL_STACK", "DISTRIBUTED_SYSTEMS", 
            "SOFTWARE_ARCHITECTURE", "MOBILE", "DEVOPS", "CLOUD"
        }
        if any(d in sw_subdomains for d in domains):
            domains["SOFTWARE_ENGINEERING"] = 1.0
        if any(d in {"DATA_SCIENCE", "DATA_ENGINEERING"} for d in domains):
            domains["DATA"] = 1.0
        if any(d in {"MACHINE_LEARNING", "DEEP_LEARNING", "MLOPS"} for d in domains):
            domains["AI_ML"] = 1.0
        if any(d in {"QA_TESTING", "TESTING", "QA_AUTOMATION"} for d in domains):
            domains["QA_TESTING"] = 1.0
        if any(d in {"SECURITY", "CYBERSECURITY"} for d in domains):
            domains["SECURITY"] = 1.0
            
        # Compute project sophistication score
        scores = [p.sophistication_score for p in profile.project_sophistication]
        scores.sort(reverse=True)
        if len(scores) == 0:
            project_score = 0.0
        elif len(scores) == 1:
            project_score = scores[0] / 100.0
        else:
            project_score = sum(scores[:2]) / 200.0
            
        project_score = max(0.0, min(1.0, project_score))

        # Signals: combine direct engineering/ownership signals with evidence-derived signals
        signals = {}
        for eng_sig in profile.engineering_signals:
            if eng_sig.demonstrated:
                signals[eng_sig.category] = 1.0
        for own_sig in profile.ownership_signals:
            signals[own_sig.ownership_level] = 1.0

        # Derived hiring signals & success indicators backed by evidence
        if project_score >= 0.5 or getattr(profile, "highest_project_sophistication", 0) >= 60:
            signals["STRONG_PROJECTS"] = 1.0
            signals["PROJECT_FOCUSED"] = 0.8
        elif len(profile.project_sophistication) >= 1:
            signals["PROJECT_FOCUSED"] = 0.6

        dev_comps = {"BACKEND_DEVELOPMENT", "FRONTEND_DEVELOPMENT", "FULL_STACK_DEVELOPMENT", "API_DEVELOPMENT"}
        if any(c in dev_comps for c in competencies):
            signals["DEVELOPMENT_FOCUSED"] = 1.0

        if len(profile.workplace_exposure) > 0:
            signals["INTERNSHIP_EXPERIENCE"] = 0.85

        if competencies.get("PROBLEM_SOLVING", 0.0) >= 0.6 or "dsa" in technologies:
            signals["STRONG_DSA"] = 0.8
            signals["DSA_FOCUSED"] = 0.8

        if any(k in signals for k in ["OWNED", "LED"]):
            signals["LEADERSHIP_EXPERIENCE"] = 0.8
            
        return CandidateVectorPayload(
            schema_version=VECTOR_SCHEMA_VERSION,
            technologies=technologies,
            competencies=competencies,
            domains=domains,
            signals=signals,
            project_score=project_score
        )


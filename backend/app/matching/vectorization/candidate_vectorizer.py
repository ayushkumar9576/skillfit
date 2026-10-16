from typing import Dict, Any, List
from app.analysis.models.candidate_profile import CandidateIntelligenceProfile
from app.matching.vectorization.schema import CandidateVectorPayload, VECTOR_SCHEMA_VERSION

class CandidateVectorizer:
    DEMONSTRATION_MULTIPLIERS = {
        "CLAIMED": 0.2,
        "REFERENCED": 0.4,
        "USED": 0.6,
        "IMPLEMENTED": 0.8,
        "DESIGNED": 0.9,
        "ARCHITECTED": 1.0,
    }

    @staticmethod
    def _normalize_tech(name: str) -> str:
        return name.strip().lower()

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
            
        signals = {}
        for eng_sig in profile.engineering_signals:
            if eng_sig.demonstrated:
                signals[eng_sig.category] = 1.0
        for own_sig in profile.ownership_signals:
            signals[own_sig.ownership_level] = 1.0
            
        scores = [p.sophistication_score for p in profile.project_sophistication]
        scores.sort(reverse=True)
        if len(scores) == 0:
            project_score = 0.0
        elif len(scores) == 1:
            project_score = scores[0] / 100.0
        else:
            project_score = sum(scores[:2]) / 200.0
            
        project_score = max(0.0, min(1.0, project_score))
            
        return CandidateVectorPayload(
            schema_version=VECTOR_SCHEMA_VERSION,
            technologies=technologies,
            competencies=competencies,
            domains=domains,
            signals=signals,
            project_score=project_score
        )

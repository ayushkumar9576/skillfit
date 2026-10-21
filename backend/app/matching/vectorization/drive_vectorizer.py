from typing import Dict, Any, List
from app.analysis.drives.schemas.intelligence import DriveIntelligenceProfile
from app.matching.vectorization.schema import (
    DriveVectorPayload, 
    VECTOR_SCHEMA_VERSION,
    NAMESPACE_TECH,
    NAMESPACE_COMP,
    NAMESPACE_DOMAIN,
    NAMESPACE_SIGNAL
)
from app.matching.vectorization.canon import normalize_technology_name

class DriveVectorizer:
    IMPORTANCE_MULTIPLIERS = {
        "LOW": 0.25,
        "MEDIUM": 0.50,
        "HIGH": 0.75,
        "CRITICAL": 1.00,
    }
    
    STRENGTH_MULTIPLIERS = {
        "REQUIRED": 1.0,
        "PREFERRED": 0.75,
        "BONUS": 0.3,
    }

    @classmethod
    def _normalize_tech(cls, name: str) -> str:
        return normalize_technology_name(name)

    @classmethod
    def generate(cls, profile: DriveIntelligenceProfile) -> DriveVectorPayload:
        technologies = {}
        critical_requirements = []
        
        for tech in profile.technologies:
            normalized = cls._normalize_tech(tech.name)
            score = cls.IMPORTANCE_MULTIPLIERS.get(tech.importance, 0.25)
            if technologies.get(normalized, 0.0) < score:
                technologies[normalized] = score
            if tech.importance == "CRITICAL":
                critical_requirements.append(f"{NAMESPACE_TECH}{normalized}")
                
        competencies = {}
        for comp in profile.technical_competencies:
            score = cls.IMPORTANCE_MULTIPLIERS.get(comp.importance, 0.25)
            if competencies.get(comp.competency, 0.0) < score:
                competencies[comp.competency] = score
            if comp.importance == "CRITICAL":
                critical_requirements.append(f"{NAMESPACE_COMP}{comp.competency}")
                
        domains = {}
        if profile.domain:
            domains[profile.domain.domain] = 1.0
            
        signals = {}
        for signal in profile.hiring_signals:
            score = cls.IMPORTANCE_MULTIPLIERS.get(signal.importance, 0.25)
            if signals.get(signal.signal, 0.0) < score:
                signals[signal.signal] = score
                
        for ind in profile.success_indicators:
            score = cls.STRENGTH_MULTIPLIERS.get(ind.strength, 0.5)
            if signals.get(ind.indicator, 0.0) < score:
                signals[ind.indicator] = score

        # Deduplicate critical requirements safely
        critical_requirements = sorted(list(set(critical_requirements)))

        return DriveVectorPayload(
            schema_version=VECTOR_SCHEMA_VERSION,
            technologies=technologies,
            competencies=competencies,
            domains=domains,
            signals=signals,
            critical_requirements=critical_requirements
        )


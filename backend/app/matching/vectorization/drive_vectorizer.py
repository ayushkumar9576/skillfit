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

    @staticmethod
    def _normalize_tech(name: str) -> str:
        return name.strip().lower()

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
            # Domain is usually considered a fundamental expectation.
            # If domain isn't explicitly CRITICAL in Phase 5.1 we skip adding to critical_requirements 
            # unless instructed. Let's add it as CRITICAL since its score is hardcoded to 1.0.
            critical_requirements.append(f"{NAMESPACE_DOMAIN}{profile.domain.domain}")
            
        signals = {}
        for signal in profile.hiring_signals:
            score = cls.IMPORTANCE_MULTIPLIERS.get(signal.importance, 0.25)
            if signals.get(signal.signal, 0.0) < score:
                signals[signal.signal] = score
            if signal.importance == "CRITICAL":
                critical_requirements.append(f"{NAMESPACE_SIGNAL}{signal.signal}")
                
        for ind in profile.success_indicators:
            score = cls.STRENGTH_MULTIPLIERS.get(ind.strength, 0.5)
            if signals.get(ind.indicator, 0.0) < score:
                signals[ind.indicator] = score
            if ind.strength == "REQUIRED":
                critical_requirements.append(f"{NAMESPACE_SIGNAL}{ind.indicator}")

        # Deduplicate critical requirements safely
        critical_requirements = list(set(critical_requirements))

        return DriveVectorPayload(
            schema_version=VECTOR_SCHEMA_VERSION,
            technologies=technologies,
            competencies=competencies,
            domains=domains,
            signals=signals,
            critical_requirements=critical_requirements
        )

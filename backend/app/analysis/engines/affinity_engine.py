"""
app/analysis/engines/affinity_engine.py
---------------------------------------
Role Affinity Engine — Phase 3 Final Hardening.

Determines role affinities deterministically based on the candidate's
verified skills from CandidateIntelligenceProfile.

Input:  List[SkillIntelligence]   (from profile.skills)
Output: List[Dict[str, Any]]      (role → confidence, evidence)

Evidence weights now use VerificationStatus to scale confidence, rather
than the old float confidence_score.
"""

import logging
from typing import Any, Dict, List

from app.analysis.models.candidate_profile import (
    SkillIntelligence,
    VerificationStatus,
)

logger = logging.getLogger(__name__)

# VerificationStatus → confidence weight for role matching
_STATUS_WEIGHT = {
    VerificationStatus.STRONGLY_VERIFIED.value: 1.0,
    VerificationStatus.VERIFIED.value: 0.80,
    VerificationStatus.WEAKLY_VERIFIED.value: 0.55,
    VerificationStatus.UNVERIFIED.value: 0.20,
}

ROLE_MAPPING: Dict[str, Dict[str, List[str]]] = {
    "Machine Learning Engineer": {
        "required": ["Python", "Scikit-Learn", "Tensorflow", "Pytorch", "Machine Learning"],
        "bonus": ["Aws", "Docker", "Mlflow", "Sql"],
    },
    "Data Scientist": {
        "required": ["Python", "Pandas", "Numpy", "Sql", "Data Analysis", "Statistics"],
        "bonus": ["Tableau", "Machine Learning", "R"],
    },
    "Frontend Developer": {
        "required": ["Javascript", "Html", "Css", "React", "Angular", "Vue"],
        "bonus": ["Typescript", "Next.js", "Tailwind"],
    },
    "Backend Developer": {
        "required": ["Node.js", "Python", "Java", "Postgresql", "Mysql", "Mongodb"],
        "bonus": ["Docker", "Aws", "Redis", "Fastapi", "Django", "Spring Boot"],
    },
    "Full Stack Developer": {
        "required": ["Javascript", "React", "Node.js", "Python", "Postgresql"],
        "bonus": ["Aws", "Docker", "Typescript"],
    },
    "DevOps Engineer": {
        "required": ["Docker", "Kubernetes", "Aws", "Linux", "Jenkins", "Github Actions"],
        "bonus": ["Terraform", "Ansible", "Python"],
    },
}


class AffinityEngine:
    """
    Deterministic role affinity calculator.
    Consumes List[SkillIntelligence] — no LLM calls.
    """

    def analyze(self, skills: List[SkillIntelligence]) -> List[Dict[str, Any]]:
        """
        Return a list of role affinities sorted by confidence descending.

        Args:
            skills: List[SkillIntelligence] from CandidateIntelligenceProfile.skills.

        Returns:
            List of dicts: [{"role": str, "confidence": int, "evidence": List[str]}]
        """
        # Build lookup: normalized skill name → SkillIntelligence
        skill_lookup: Dict[str, SkillIntelligence] = {
            s.skill.lower(): s for s in skills
        }

        affinities: List[Dict[str, Any]] = []

        for role, criteria in ROLE_MAPPING.items():
            evidence: List[str] = []
            score = 0.0
            required_met = 0

            for req in criteria["required"]:
                sk = skill_lookup.get(req.lower())
                if sk:
                    weight = _STATUS_WEIGHT.get(sk.verification_status, 0.2)
                    evidence.append(sk.skill)
                    required_met += 1
                    score += weight * 15.0

            for bon in criteria["bonus"]:
                sk = skill_lookup.get(bon.lower())
                if sk:
                    weight = _STATUS_WEIGHT.get(sk.verification_status, 0.2)
                    evidence.append(sk.skill)
                    score += weight * 5.0

            if required_met > 0:
                max_possible = len(criteria["required"]) * 15.0 + len(criteria["bonus"]) * 5.0
                confidence = min(round((score / max_possible) * 100), 100)
                if confidence > 15:
                    affinities.append({
                        "role": role,
                        "confidence": confidence,
                        "evidence": evidence,
                    })

        affinities.sort(key=lambda x: x["confidence"], reverse=True)
        return affinities

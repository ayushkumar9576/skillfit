"""
app/analysis/engines/affinity_engine.py
---------------------------------------
Determines role affinities deterministically based on skills and domains.
"""

from typing import List, Dict, Any
from collections import defaultdict
import logging

from app.analysis.models.skill_models import SkillAnalysisResult

logger = logging.getLogger(__name__)

ROLE_MAPPING = {
    "Machine Learning Engineer": {
        "required": ["Python", "Scikit-Learn", "Tensorflow", "Pytorch", "Machine Learning"],
        "bonus": ["Aws", "Docker", "Mlflow", "Sql"]
    },
    "Data Scientist": {
        "required": ["Python", "Pandas", "Numpy", "Sql", "Data Analysis", "Statistics"],
        "bonus": ["Tableau", "Machine Learning", "R"]
    },
    "Frontend Developer": {
        "required": ["Javascript", "Html", "Css", "React", "Angular", "Vue"],
        "bonus": ["Typescript", "Next.js", "Tailwind"]
    },
    "Backend Developer": {
        "required": ["Node.js", "Python", "Java", "Postgresql", "Mysql", "Mongodb"],
        "bonus": ["Docker", "Aws", "Redis", "Fastapi", "Django", "Spring Boot"]
    },
    "Full Stack Developer": {
        "required": ["Javascript", "React", "Node.js", "Python", "Postgresql"],
        "bonus": ["Aws", "Docker", "Typescript"]
    },
    "DevOps Engineer": {
        "required": ["Docker", "Kubernetes", "Aws", "Linux", "Jenkins", "Github Actions"],
        "bonus": ["Terraform", "Ansible", "Python"]
    }
}

class AffinityEngine:
    def analyze(self, skill_result: SkillAnalysisResult) -> List[Dict[str, Any]]:
        """
        Returns list of role affinities with confidence and evidence.
        """
        affinities = []
        
        # Build lookup for fast matching
        student_skills = {s.skill_name.lower(): s for s in skill_result.skills}
        
        for role, criteria in ROLE_MAPPING.items():
            evidence = []
            score = 0.0
            
            # Check required
            required_met = 0
            for req in criteria["required"]:
                if req.lower() in student_skills:
                    s = student_skills[req.lower()]
                    evidence.append(s.skill_name)
                    required_met += 1
                    score += s.confidence_score * 15
            
            # Check bonus
            for bon in criteria["bonus"]:
                if bon.lower() in student_skills:
                    s = student_skills[bon.lower()]
                    evidence.append(s.skill_name)
                    score += s.confidence_score * 5
                    
            if required_met > 0:
                # Calculate confidence
                # Max score roughly (len(req)*15 + len(bonus)*5) -> scale to 100
                max_possible = len(criteria["required"]) * 15 + len(criteria["bonus"]) * 5
                confidence = min(round((score / max_possible) * 100), 100)
                
                # Only include if they have at least some match
                if confidence > 15:
                    affinities.append({
                        "role": role,
                        "confidence": confidence,
                        "evidence": evidence
                    })
                    
        affinities.sort(key=lambda x: x["confidence"], reverse=True)
        return affinities

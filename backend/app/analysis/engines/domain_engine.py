"""
app/analysis/engines/domain_engine.py
-------------------------------------
Determines candidate's domains (e.g. Web Development, Machine Learning)
based on deterministic mapping of their extracted skills.
"""

from typing import List, Dict, Any, Tuple
from collections import defaultdict
import logging

from app.analysis.models.skill_models import SkillAnalysisResult

logger = logging.getLogger(__name__)

DOMAIN_SKILL_MAPPING = {
    "Machine Learning & AI": {
        "Scikit-Learn", "Tensorflow", "Pytorch", "Keras", "Mlflow",
        "Deep Learning", "Nlp", "Computer Vision", "Machine Learning", "Openai"
    },
    "Data Science & Analytics": {
        "Pandas", "Numpy", "Matplotlib", "Seaborn", "Sql", "Tableau", 
        "Powerbi", "Data Analysis", "Statistics", "R"
    },
    "Web Development (Frontend)": {
        "React", "Angular", "Vue", "Next.js", "Html", "Css", "Tailwind",
        "Javascript", "Typescript", "Redux", "Bootstrap"
    },
    "Web Development (Backend)": {
        "Node.js", "Express", "Django", "Flask", "Fastapi", "Spring Boot", 
        "Java", "Python", "Go", "Ruby", "Php"
    },
    "Cloud & DevOps": {
        "Aws", "Azure", "Gcp", "Docker", "Kubernetes", "Jenkins", 
        "Github Actions", "Terraform", "Ansible", "Linux"
    },
    "Database Management": {
        "Postgresql", "Mysql", "Mongodb", "Redis", "Elasticsearch", 
        "Cassandra", "Sql Server", "Oracle"
    }
}

class DomainEngine:
    """
    DEPRECATED (Phase 3.12): Do not use. Domain intelligence is now deterministically
    synthesized from the CandidateIntelligenceAggregator via DomainIntelligence objects.
    The SynthesisEngine bridge has been removed (Phase 3.13B).
    """
    def analyze(self, skill_result: SkillAnalysisResult) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Returns (primary_domain, list_of_domains).
        """
        domain_evidence: Dict[str, List[str]] = defaultdict(list)
        domain_scores: Dict[str, float] = defaultdict(float)

        for skill in skill_result.skills:
            skill_name_lower = skill.skill_name.title()
            for domain, mapped_skills in DOMAIN_SKILL_MAPPING.items():
                if skill_name_lower in mapped_skills or skill.skill_name.lower() in [s.lower() for s in mapped_skills]:
                    domain_evidence[domain].append(skill.skill_name)
                    # Add to score based on confidence and depth
                    score_increment = skill.confidence_score * 10
                    if skill.skill_depth == "Advanced":
                        score_increment *= 1.5
                    elif skill.skill_depth == "Beginner":
                        score_increment *= 0.7
                    domain_scores[domain] += score_increment

        domains_list = []
        for domain, score in domain_scores.items():
            # Normalize confidence somewhat (max cap at 100)
            confidence = min(round(score * 2), 100)
            domains_list.append({
                "name": domain,
                "confidence": confidence,
                "evidence": domain_evidence[domain]
            })

        domains_list.sort(key=lambda x: x["confidence"], reverse=True)

        primary_domain = domains_list[0]["name"] if domains_list else "General Software Engineering"

        return primary_domain, domains_list

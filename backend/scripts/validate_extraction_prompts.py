import asyncio
import uuid
import sys
import logging

from app.analysis.models.base import AnalysisEvidence
from app.analysis.models.project_models import ProjectEvidence
from app.analysis.engines.project_analysis_engine import ProjectAnalysisEngine
from app.services.llm.service import LLMService

logging.basicConfig(level=logging.ERROR)

GENERIC_SKILLS = {
    "software development", "programming", "web development", 
    "application development", "backend development", "frontend development",
    "cloud computing", "it", "technology", "engineering", "full stack"
}

async def validate():
    engine = ProjectAnalysisEngine()
    
    samples = [
        {
            "desc": "Built an ecommerce website.",
            "technologies": []
        },
        {
            "desc": "Built an ecommerce website using React and Node.js.",
            "technologies": ["React", "Node.js"]
        },
        {
            "desc": "Built a MERN application for internal metrics.",
            "technologies": []
        },
        {
            "desc": "Built a full stack application for HR management.",
            "technologies": []
        }
    ]
    
    print("=" * 60)
    print("PROMPT VALIDATION REPORT")
    print("=" * 60)
    
    llm = engine._get_llm_service()
    
    for idx, sample in enumerate(samples):
        print(f"\n--- Sample {idx + 1} ---")
        print(f"Original Resume Evidence: \"{sample['desc']}\"")
        
        project = ProjectEvidence(
            title=f"Sample {idx+1}",
            description=sample["desc"],
            technologies=sample["technologies"],
            evidences=[
                AnalysisEvidence(
                    evidence_text=sample["desc"],
                    source_section="projects",
                    line_number=1,
                    confidence=0.9
                )
            ]
        )
        
        report = await engine._analyze_one(idx, project, llm)
        
        if not report:
            print("Failed to generate report.")
            continue
            
        skills_extracted = [s.skill for s in report.skill_evidence.items]
        
        generic_count = 0
        specific_count = 0
        
        for s in skills_extracted:
            if s.lower() in GENERIC_SKILLS:
                generic_count += 1
            else:
                specific_count += 1
                
        print("Extracted Skills:")
        if not skills_extracted:
            print("  (None)")
        else:
            for s in skills_extracted:
                kind = "GENERIC" if s.lower() in GENERIC_SKILLS else "SPECIFIC"
                print(f"  - {s} [{kind}]")
            
        print(f"\nGeneric Skill Count: {generic_count}")
        print(f"Specific Technology Count: {specific_count}")
        
    print("\nValidation complete.")

if __name__ == "__main__":
    asyncio.run(validate())

import sys
import uuid
import json
from pathlib import Path
from app.db.database import SessionLocal
from app.models.resume_file import ResumeFile
from app.services.resume_pipeline import (
    _load_resume,
    _stage_extract_text,
    _stage_project_analysis,
    _stage_internship_analysis,
    _stage_certification_analysis,
    _stage_skill_analysis
)
from app.core.enums import ProcessingStatus

def run_test():
    db = SessionLocal()
    # Create a mock resume file
    uid = uuid.uuid4()
    # We need a dummy user and student to satisfy constraints
    from app.models.user import User
    from app.models.student import Student
    
    user = User(
        id=uid,
        full_name="Test User",
        email="test_skill@example.com",
        registration_number="REG12345",
        password_hash="hash",
        role="student"
    )
    db.add(user)
    db.flush()
    
    student = Student(
        user_id=user.id,
        registration_number="REG12345"
    )
    db.add(student)
    db.flush()

    resume = ResumeFile(
        id=uid,
        student_id=student.id,
        file_name="test_skill_resume.pdf",
        file_path="test/path",
        file_type="application/pdf",
        file_size=1024,
        file_hash="dummyhash",
        processing_status=ProcessingStatus.processing
    )
    db.add(resume)
    db.commit()
    
    # We will inject extracted text directly so we don't need a real PDF
    resume.extracted_text = """
PROJECTS
E-Commerce Platform
ReactJS, Node.js | Jan 2023 - Present
• Built a scalable backend using node.js and express.
• Implemented dynamic frontend with ReactJS.

INTERNSHIPS
Software Engineer Intern
Google | May 2023 - Aug 2023
• Worked with React.js for the main dashboard.
• Developed internal tools using Python.

CERTIFICATIONS
AWS Certified Cloud Practitioner
Amazon Web Services
"""
    db.commit()

    print(f"Testing pipeline for UUID: {uid}")
    
    _stage_project_analysis(db, resume)
    _stage_internship_analysis(db, resume)
    _stage_certification_analysis(db, resume)
    
    success = _stage_skill_analysis(db, resume)
    
    if success:
        print("Pipeline stages completed successfully.")
        
        # Verify JSON was created
        debug_path = Path("DEBUG/results/debug_skill.json")
        if debug_path.exists():
            with open(debug_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            print("\n===== E2E VERIFICATION =====")
            print(f"Total Skills Aggregated: {data['total_skills_count']}")
            for skill in data['skills']:
                print(f"Skill: {skill['skill_name']}")
                print(f"  Confidence: {skill['confidence_score']} ({skill['confidence_level']})")
                print(f"  Sources: {skill['source_count']}, Evidences: {skill['evidence_count']}")
                print(f"  Depth: {skill['skill_depth']}")
                print(f"  Hiring Signal: {skill['hiring_signal']}")
                print("  Sources:")
                for src in skill['evidences']:
                    print(f"    - {src['source_type']}: {src['source_name']}")
            print("============================")
        else:
            print("FAILED: debug_skill.json not found.")
    else:
        print("Pipeline failed.")
        
    db.delete(resume)
    db.commit()
    db.close()

if __name__ == "__main__":
    run_test()

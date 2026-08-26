import asyncio
import uuid
import os
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.resume_file import ResumeFile
from app.services.resume_pipeline import _stage_certification_analysis

def run_pipeline():
    # We will just pick the last resume from the DB and run certification analysis on it
    db: Session = SessionLocal()
    resume = db.query(ResumeFile).filter(ResumeFile.extracted_text.isnot(None)).order_by(ResumeFile.created_at.desc()).first()
    
    if not resume:
        print("No resume found with extracted text.")
        return

    print(f"Running Certification Analysis on Resume ID: {resume.id}")
    _stage_certification_analysis(db, resume)
    print("Certification Pipeline Test Complete.")

if __name__ == "__main__":
    run_pipeline()

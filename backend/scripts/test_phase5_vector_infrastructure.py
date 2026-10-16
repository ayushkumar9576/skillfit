import uuid
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.resume_file import ResumeFile
from app.models.drive import Drive
from app.models.candidate_vector import CandidateVectorModel
from app.models.drive_vector import DriveVectorModel
from app.matching.services.vector_persistence_service import VectorPersistenceService

def run_tests():
    db: Session = SessionLocal()
    
    print("Testing Vector Infrastructure...")
    
    # Test Candidate Vectorizer
    resume = db.query(ResumeFile).filter(ResumeFile.processing_status == "completed").first()
    if resume:
        print(f"\n--- Testing Candidate Vector for Resume: {resume.id} ---")
        VectorPersistenceService.sync_resume_vector(db, resume.id)
        candidate_vector = VectorPersistenceService.get_candidate_vector(db, resume.id)
        if candidate_vector:
            print(f"SUCCESS: Candidate Vector Generated. Source Snapshot: {candidate_vector.source_snapshot_id}")
            print(f"Vector Snippet: {str(candidate_vector.vector_json)[:200]}...")
        else:
            print("FAILED: Candidate Vector not generated.")
    else:
        print("No completed resumes found to test candidate vector.")
        
    # Test Drive Vectorizer
    drive = db.query(Drive).filter(Drive.status == "ready").first()
    if drive:
        print(f"\n--- Testing Drive Vector for Drive: {drive.id} ---")
        VectorPersistenceService.sync_drive_vector(db, drive.id)
        drive_vector = VectorPersistenceService.get_drive_vector(db, drive.id)
        if drive_vector:
            print(f"SUCCESS: Drive Vector Generated. Source Snapshot: {drive_vector.source_snapshot_id}")
            print(f"Vector Snippet: {str(drive_vector.vector_json)[:200]}...")
        else:
            print("FAILED: Drive Vector not generated.")
    else:
        print("No ready drives found to test drive vector.")

    db.close()
    
if __name__ == "__main__":
    run_tests()

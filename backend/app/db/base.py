from app.db.database import Base

from app.models.user import User
from app.models.faculty import Faculty
from app.models.student import Student
from app.models.drive import Drive
from app.models.recommendation import Recommendation
from app.models.resume_file import ResumeFile
from app.models.candidate_intelligence_snapshot import CandidateIntelligenceSnapshotModel
# Phase 4.1 — Drive Intelligence persistence layer
from app.models.drive_snapshot import DriveSnapshotModel
# Phase 4.2 — Drive Ingestion versioned source layer
from app.models.drive_source import DriveSource
# Phase 4.3 — Drive Intelligence analysis execution records
from app.models.drive_analysis import DriveAnalysis
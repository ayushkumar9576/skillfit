from typing import List, Tuple
from sqlalchemy.orm import Session

from app.matching.models.result import MatchResult
from app.models.candidate_vector import CandidateVectorModel
from app.models.drive_vector import DriveVectorModel
from app.matching.services.vector_persistence_service import VectorPersistenceService
from app.matching.similarity.matching_engine import match
import uuid

class RecommendationService:
    @staticmethod
    def get_recommended_drives(
        db: Session, 
        resume_id: str, 
        limit: int = 20, 
        only_published: bool = False
    ) -> List[MatchResult]:
        try:
            resume_uuid = uuid.UUID(resume_id)
        except ValueError:
            return []
            
        candidate_vector = VectorPersistenceService.get_candidate_vector(db, resume_uuid)
        if not candidate_vector:
            raise ValueError("Candidate Vector not found.")
            
        # Avoid N+1, load drive vectors
        query = db.query(DriveVectorModel).filter(DriveVectorModel.schema_version == candidate_vector.schema_version)
        
        if only_published:
            from app.models.drive import Drive
            from app.core.enums import DriveStatus
            published_ids = [
                row[0] if isinstance(row, tuple) else getattr(row, 'id', row)
                for row in db.query(Drive.id).filter(Drive.status == DriveStatus.published).all()
            ]
            if not published_ids:
                return []
            query = query.filter(DriveVectorModel.drive_id.in_(published_ids))
            
        drive_vectors = query.all()
        if not drive_vectors:
            return []
            
        scored_drives: List[Tuple[MatchResult, DriveVectorModel]] = []
        
        for drive_vector in drive_vectors:
            # As per requirement 4, we must raise if they don't match right before comparison
            if candidate_vector.schema_version != drive_vector.schema_version:
                raise ValueError("Schema version mismatch between candidate and drive vectors.")
                
            match_result = match(candidate_vector, drive_vector)
            scored_drives.append((match_result, drive_vector))
            
        # Ranking order: 
        # 1. Higher overall score
        # 2. Fewer critical gaps
        # 3. Higher project sophistication
        # 4. Newer intelligence snapshot (of the drive, since we are ranking drives)
        cand_project_score = candidate_vector.vector_json.get("project_score", 0.0)
        
        scored_drives.sort(
            key=lambda x: (
                x[0].score.overall_score,
                -x[0].explanation.critical_gap_count,
                cand_project_score, # constant for this candidate, but safe to include
                x[1].updated_at.timestamp() if x[1].updated_at else 0.0
            ),
            reverse=True
        )
        
        return [res[0] for res in scored_drives[:limit]]

    @staticmethod
    def get_recommended_candidates(db: Session, drive_id: str, limit: int = 50) -> List[MatchResult]:
        try:
            drive_uuid = uuid.UUID(drive_id)
        except ValueError:
            return []
            
        drive_vector = VectorPersistenceService.get_drive_vector(db, drive_uuid)
        if not drive_vector:
            raise ValueError("Drive Vector not found.")
            
        candidate_vectors = db.query(CandidateVectorModel).filter(CandidateVectorModel.schema_version == drive_vector.schema_version).all()
        if not candidate_vectors:
            return []
            
        scored_candidates: List[Tuple[MatchResult, CandidateVectorModel]] = []
        
        for cand_vector in candidate_vectors:
            if cand_vector.schema_version != drive_vector.schema_version:
                raise ValueError("Schema version mismatch between candidate and drive vectors.")
                
            match_result = match(cand_vector, drive_vector)
            scored_candidates.append((match_result, cand_vector))
            
        # Ranking order:
        # 1. Higher overall score
        # 2. Fewer critical gaps
        # 3. Higher project sophistication (of the candidate)
        # 4. Newer intelligence snapshot (of the candidate)
        scored_candidates.sort(
            key=lambda x: (
                x[0].score.overall_score,
                -x[0].explanation.critical_gap_count,
                x[1].vector_json.get("project_score", 0.0),
                x[1].updated_at.timestamp() if x[1].updated_at else 0.0
            ),
            reverse=True
        )
        
        return [res[0] for res in scored_candidates[:limit]]

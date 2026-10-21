import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.core.enums import UserRole, DriveStatus
from app.models.user import User
from app.models.student import Student
from app.models.resume_file import ResumeFile
from app.models.drive import Drive
from app.schemas.matching import RecommendedDriveResponse, DimensionBreakdownDTO
from app.matching.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/api/v1/students", tags=["Students"])

@router.get("/me/recommended-drives", response_model=List[RecommendedDriveResponse])
def get_student_recommended_drives(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Authorization: Student Access
    # Students may access their own recommendations ONLY.
    if current_user.role != UserRole.student:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only students can access their recommended drives")
        
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")
        
    student_id = student.id
            
    # Resolve student's active resume
    active_resume = db.query(ResumeFile).filter(
        ResumeFile.student_id == student_id,
        ResumeFile.is_active == True
    ).first()
    
    if not active_resume:
        return []
        
    try:
        match_results = RecommendationService.get_recommended_drives(
            db, 
            str(active_resume.id),
            only_published=True
        )
    except ValueError:
        return []
        
    if not match_results:
        return []
        
    # Hydrate DTOs - Batch load drives to avoid N+1, restricting to PUBLISHED drives only
    drive_ids = [uuid.UUID(res.drive_id) for res in match_results]
    drives = db.query(Drive).filter(
        Drive.id.in_(drive_ids),
        Drive.status == DriveStatus.published
    ).all()
    drive_map = {d.id: d for d in drives}
    
    response = []
    for res in match_results:
        d_id = uuid.UUID(res.drive_id)
        drive_model = drive_map.get(d_id)
        
        # Only published drives are visible to students
        if not drive_model or drive_model.status != DriveStatus.published:
            continue
            
        top_strengths = [s.title.replace("Strong ", "") for s in res.explanation.strengths[:3]]
        top_gaps = [g.title.replace("Missing ", "") for g in res.explanation.gaps[:3]]

        # Hydrate per-dimension score breakdown
        dimension_breakdown = [
            DimensionBreakdownDTO(
                dimension=dim_key,
                raw_score=ds.raw_score,
                weight=ds.weight,
                weighted_score=ds.weighted_score,
                matched_items=ds.matched_items,
                total_items=ds.total_items,
                reasoning=ds.reasoning,
                strengths=[s.title.replace("Strong ", "") for s in res.explanation.strengths if s.dimension.value == dim_key],
                gaps=[g.title.replace("Missing ", "") for g in res.explanation.gaps if g.dimension.value == dim_key]
            )
            for dim_key, ds in res.score.dimension_scores.items()
        ]
            
        response.append(
            RecommendedDriveResponse(
                drive_id=d_id,
                drive_title=drive_model.role,
                company_name=drive_model.company_name,
                score=res.score.overall_score,
                raw_score=res.score.raw_score,
                tier=res.match_tier.value + "_MATCH",
                strengths=top_strengths,
                gaps=top_gaps,
                overall_narrative=res.explanation.overall_narrative,
                dimension_breakdown=dimension_breakdown
            )
        )
        
    return response


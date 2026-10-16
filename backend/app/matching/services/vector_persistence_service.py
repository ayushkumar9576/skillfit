import uuid
import dataclasses
from uuid import UUID
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from app.models.candidate_intelligence_snapshot import CandidateIntelligenceSnapshotModel
from app.models.drive_snapshot import DriveSnapshotModel
from app.models.candidate_vector import CandidateVectorModel
from app.models.drive_vector import DriveVectorModel

from app.analysis.serialization.profile_serializer import ProfileSerializer
from app.analysis.drives.schemas.intelligence import DriveIntelligenceProfile

from app.matching.vectorization.candidate_vectorizer import CandidateVectorizer
from app.matching.vectorization.drive_vectorizer import DriveVectorizer
from app.matching.vectorization.schema import VECTOR_SCHEMA_VERSION

class VectorPersistenceService:

    @staticmethod
    def sync_resume_vector(db: Session, resume_id: UUID) -> Optional[CandidateVectorModel]:
        """
        1. Fetch latest candidate snapshot
        2. Generate vector
        3. UPSERT candidate vector row
        """
        snapshot = db.query(CandidateIntelligenceSnapshotModel).filter(
            CandidateIntelligenceSnapshotModel.resume_id == resume_id
        ).order_by(
            CandidateIntelligenceSnapshotModel.generated_at.desc()
        ).first()

        if not snapshot:
            return None

        profile = ProfileSerializer.from_snapshot_payload(snapshot.profile_json)
        payload = CandidateVectorizer.generate(profile)

        stmt = insert(CandidateVectorModel).values(
            id=uuid.uuid4(),
            resume_id=resume_id,
            source_snapshot_id=snapshot.id,
            schema_version=VECTOR_SCHEMA_VERSION,
            vector_json=dataclasses.asdict(payload),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

        stmt = stmt.on_conflict_do_update(
            index_elements=['resume_id', 'schema_version'],
            set_=dict(
                source_snapshot_id=stmt.excluded.source_snapshot_id,
                vector_json=stmt.excluded.vector_json,
                updated_at=datetime.now(timezone.utc)
            )
        )

        db.execute(stmt)
        db.commit()
        
        return db.query(CandidateVectorModel).filter_by(
            resume_id=resume_id, schema_version=VECTOR_SCHEMA_VERSION
        ).first()

    @staticmethod
    def sync_drive_vector(db: Session, drive_id: UUID) -> Optional[DriveVectorModel]:
        """
        1. Fetch latest drive snapshot
        2. Generate vector
        3. UPSERT drive vector row
        """
        snapshot = db.query(DriveSnapshotModel).filter(
            DriveSnapshotModel.drive_id == drive_id
        ).order_by(
            DriveSnapshotModel.created_at.desc()
        ).first()

        if not snapshot:
            return None

        profile = DriveIntelligenceProfile.model_validate(snapshot.intelligence_payload)
        payload = DriveVectorizer.generate(profile)

        stmt = insert(DriveVectorModel).values(
            id=uuid.uuid4(),
            drive_id=drive_id,
            source_snapshot_id=snapshot.id,
            schema_version=VECTOR_SCHEMA_VERSION,
            vector_json=dataclasses.asdict(payload),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

        stmt = stmt.on_conflict_do_update(
            index_elements=['drive_id', 'schema_version'],
            set_=dict(
                source_snapshot_id=stmt.excluded.source_snapshot_id,
                vector_json=stmt.excluded.vector_json,
                updated_at=datetime.now(timezone.utc)
            )
        )

        db.execute(stmt)
        db.commit()

        return db.query(DriveVectorModel).filter_by(
            drive_id=drive_id, schema_version=VECTOR_SCHEMA_VERSION
        ).first()

    @staticmethod
    def get_candidate_vector(db: Session, resume_id: UUID) -> Optional[CandidateVectorModel]:
        return db.query(CandidateVectorModel).filter_by(
            resume_id=resume_id, schema_version=VECTOR_SCHEMA_VERSION
        ).first()

    @staticmethod
    def get_drive_vector(db: Session, drive_id: UUID) -> Optional[DriveVectorModel]:
        return db.query(DriveVectorModel).filter_by(
            drive_id=drive_id, schema_version=VECTOR_SCHEMA_VERSION
        ).first()

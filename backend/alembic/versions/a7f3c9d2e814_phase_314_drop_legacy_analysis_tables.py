"""Phase 3.14 — Drop legacy analysis tables

Revision ID: a7f3c9d2e814
Revises: 1cc54a3f84f8
Create Date: 2026-08-29

All six tables were superseded by CandidateIntelligenceSnapshot in Phase 3.13.
Runtime reads and writes to these tables were eliminated in Phase 3.13B.
ORM models, imports, and relationships were removed in Phase 3.14.

FK graph (verified against live DB before migration was written):
  cv_analyses.student_id         -> students
  cv_analyses.resume_id          -> resume_files
  candidate_profiles.student_id  -> students
  candidate_profiles.source_resume_id -> resume_files
  student_projects.student_id    -> students
  student_projects.resume_id     -> resume_files
  student_skills.student_id      -> students
  student_skills.resume_id       -> resume_files
  student_internships.student_id -> students
  student_internships.resume_id  -> resume_files
  certifications.student_id      -> students
  certifications.resume_id       -> resume_files

All 6 tables reference only `students` and `resume_files` (both retained).
Drop order among the 6 is unconstrained.

Also adds the missing FK constraint on candidate_intelligence_snapshots.resume_id
so that db.delete(resume_file) cascades snapshot cleanup at the DB level.
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "a7f3c9d2e814"
down_revision: Union[str, Sequence[str], None] = "1cc54a3f84f8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -----------------------------------------------------------------------
    # Step 1: Add missing FK on candidate_intelligence_snapshots.resume_id
    # The column was created in 1cc54a3f84f8 as a plain UUID column.
    # -----------------------------------------------------------------------
    op.create_foreign_key(
        "fk_candidate_intelligence_snapshots_resume_id",
        "candidate_intelligence_snapshots",
        "resume_files",
        ["resume_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # -----------------------------------------------------------------------
    # Step 2: Drop the 6 legacy analysis tables.
    # All reference only `students` and `resume_files` (both kept).
    # Order among the 6 is unconstrained.
    # -----------------------------------------------------------------------
    op.drop_table("cv_analyses")
    op.drop_table("candidate_profiles")
    op.drop_table("student_projects")
    op.drop_table("student_skills")
    op.drop_table("student_internships")
    op.drop_table("certifications")


def downgrade() -> None:
    raise NotImplementedError(
        "Phase 3.14: Legacy analysis tables were intentionally removed. "
        "No production data existed in these tables. "
        "This migration is irreversible. "
        "To recover the schema, restore from a pre-3.14 DB backup."
    )

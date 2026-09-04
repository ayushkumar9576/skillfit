"""a79b8dd9f9ad_phase_43_drive_intelligence_engine.py

Phase 4.3 — Drive Intelligence Engine migration.

Creates:
    drive_analysis_status enum
    drive_analyses table

Extends:
    drive_snapshots table with Phase 4.3 provenance columns:
        source_id, analysis_id, prompt_version, model_name,
        intelligence_schema_version

Revision ID: a79b8dd9f9ad
Revises: c5d6e7f8a9b0
Create Date: 2026-09-05

Design notes:
    - New columns on drive_snapshots are nullable so existing rows
      (created before Phase 4.3) are not affected.
    - drive_analyses.snapshot_id is a deferred FK resolved after snapshot
      creation, so it is nullable.
    - All indexes use explicit names to allow safe rollback.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "a79b8dd9f9ad"
down_revision = "c5d6e7f8a9b0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. Create drive_analysis_status enum
    # ------------------------------------------------------------------
    drive_analysis_status = postgresql.ENUM(
        "pending", "running", "completed", "failed",
        name="driveanalysisstatus",
        create_type=False,
    )
    drive_analysis_status.create(op.get_bind(), checkfirst=True)

    # ------------------------------------------------------------------
    # 2. Create drive_analyses table
    # ------------------------------------------------------------------
    op.create_table(
        "drive_analyses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "drive_id",
            sa.Integer(),
            sa.ForeignKey("drives.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "source_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("drive_sources.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        # snapshot_id is populated after COMPLETED — deferred nullable FK
        sa.Column(
            "snapshot_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="pending",
            index=True,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("analysis_version", sa.String(20), nullable=False),
        sa.Column("prompt_version", sa.String(20), nullable=False),
        sa.Column("model_name", sa.String(100), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("processing_metadata", postgresql.JSONB(), nullable=True),
    )

    # Composite index for "latest analyses per drive" query
    op.create_index(
        "ix_drive_analyses_drive_created",
        "drive_analyses",
        ["drive_id", "created_at"],
    )

    # ------------------------------------------------------------------
    # 3. Add snapshot_id FK after table exists (self-referential resolution)
    # ------------------------------------------------------------------
    op.create_foreign_key(
        "fk_drive_analyses_snapshot_id",
        "drive_analyses",
        "drive_snapshots",
        ["snapshot_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # ------------------------------------------------------------------
    # 4. Extend drive_snapshots with Phase 4.3 provenance columns
    # ------------------------------------------------------------------

    # source_id — links snapshot to the exact DriveSource analyzed
    op.add_column(
        "drive_snapshots",
        sa.Column(
            "source_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("drive_sources.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_drive_snapshots_source_id",
        "drive_snapshots",
        ["source_id"],
    )

    # analysis_id — links snapshot to its producing DriveAnalysis run
    op.add_column(
        "drive_snapshots",
        sa.Column(
            "analysis_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("drive_analyses.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_drive_snapshots_analysis_id",
        "drive_snapshots",
        ["analysis_id"],
    )

    # prompt_version — which prompt template produced this snapshot
    op.add_column(
        "drive_snapshots",
        sa.Column("prompt_version", sa.String(20), nullable=True),
    )

    # model_name — exact LLM model used
    op.add_column(
        "drive_snapshots",
        sa.Column("model_name", sa.String(100), nullable=True),
    )

    # intelligence_schema_version — DriveIntelligenceProfile schema version
    op.add_column(
        "drive_snapshots",
        sa.Column("intelligence_schema_version", sa.String(20), nullable=True),
    )


def downgrade() -> None:
    # ------------------------------------------------------------------
    # Reverse order: snapshots columns → analyses table → enum
    # ------------------------------------------------------------------

    # Remove Phase 4.3 columns from drive_snapshots
    op.drop_index("ix_drive_snapshots_analysis_id", table_name="drive_snapshots")
    op.drop_index("ix_drive_snapshots_source_id", table_name="drive_snapshots")
    op.drop_column("drive_snapshots", "intelligence_schema_version")
    op.drop_column("drive_snapshots", "model_name")
    op.drop_column("drive_snapshots", "prompt_version")
    op.drop_column("drive_snapshots", "analysis_id")
    op.drop_column("drive_snapshots", "source_id")

    # Drop drive_analyses table
    op.drop_index("ix_drive_analyses_drive_created", table_name="drive_analyses")
    op.drop_table("drive_analyses")

    # Drop enum
    op.execute("DROP TYPE IF EXISTS driveanalysisstatus")

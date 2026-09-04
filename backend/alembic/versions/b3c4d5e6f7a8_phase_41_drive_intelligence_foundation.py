"""Phase 4.1 — Drive Intelligence Foundation schema

Revision ID: b3c4d5e6f7a8
Revises: a7f3c9d2e814
Create Date: 2026-09-04

Changes:
    1. Add `status` column (DriveStatus enum) to `drives` table.
    2. Add `source_type` column (DriveSourceType enum) to `drives` table.
    3. Create `drive_snapshots` table for Drive Intelligence persistence.

Non-destructive:
    - Existing `drives` rows get status='draft' and source_type='manual'
      via server_default. No existing data is changed.
    - Existing Phase 3 tables are untouched.

Reversibility:
    - downgrade() is fully implemented and reverses all changes.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "b3c4d5e6f7a8"
down_revision: Union[str, Sequence[str], None] = "a7f3c9d2e814"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Phase 4.1 Drive Intelligence Foundation schema additions."""

    # -----------------------------------------------------------------------
    # Step 1: Create PostgreSQL enum types for Drive lifecycle fields.
    # Using create_type=False in the Column definition so we create them
    # explicitly here for clean control over ordering.
    # -----------------------------------------------------------------------
    drivestatus_enum = sa.Enum(
        "draft", "active", "closed",
        name="drivestatus",
    )
    drivestatus_enum.create(op.get_bind(), checkfirst=True)

    drivesourcetype_enum = sa.Enum(
        "manual", "parsed",
        name="drivesourcetype",
    )
    drivesourcetype_enum.create(op.get_bind(), checkfirst=True)

    # -----------------------------------------------------------------------
    # Step 2: Add `status` column to existing `drives` table.
    # server_default='draft' ensures all existing rows get a valid value.
    # -----------------------------------------------------------------------
    op.add_column(
        "drives",
        sa.Column(
            "status",
            sa.Enum("draft", "active", "closed", name="drivestatus", create_type=False),
            nullable=False,
            server_default="draft",
        ),
    )

    # -----------------------------------------------------------------------
    # Step 3: Add `source_type` column to existing `drives` table.
    # server_default='manual' is correct for all pre-4.1 drives.
    # -----------------------------------------------------------------------
    op.add_column(
        "drives",
        sa.Column(
            "source_type",
            sa.Enum("manual", "parsed", name="drivesourcetype", create_type=False),
            nullable=False,
            server_default="manual",
        ),
    )

    # -----------------------------------------------------------------------
    # Step 4: Create `drive_snapshots` table.
    # Mirrors candidate_intelligence_snapshots structure.
    # -----------------------------------------------------------------------
    op.create_table(
        "drive_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("drive_id", sa.Integer(), nullable=False),
        sa.Column("snapshot_version", sa.String(), nullable=False),
        sa.Column("analysis_version", sa.String(), nullable=False),
        sa.Column(
            "intelligence_payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "metadata_payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["drive_id"],
            ["drives.id"],
            name="fk_drive_snapshots_drive_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # -----------------------------------------------------------------------
    # Step 5: Create composite index for efficient latest-snapshot retrieval.
    # Mirrors ix_candidate_intelligence_snapshots_resume_latest.
    # -----------------------------------------------------------------------
    op.create_index(
        "ix_drive_snapshots_drive_latest",
        "drive_snapshots",
        ["drive_id", sa.text("created_at DESC NULLS LAST")],
        unique=False,
        postgresql_using="btree",
    )


def downgrade() -> None:
    """Reverse Phase 4.1 Drive Intelligence Foundation schema additions."""

    # Drop in reverse order of creation
    op.drop_index("ix_drive_snapshots_drive_latest", table_name="drive_snapshots")
    op.drop_table("drive_snapshots")

    op.drop_column("drives", "source_type")
    op.drop_column("drives", "status")

    # Drop enum types
    sa.Enum(name="drivesourcetype").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="drivestatus").drop(op.get_bind(), checkfirst=True)

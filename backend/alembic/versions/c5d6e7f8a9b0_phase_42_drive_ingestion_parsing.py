"""Phase 4.2 — Drive Ingestion & Parsing schema

Revision ID: c5d6e7f8a9b0
Revises: b3c4d5e6f7a8
Create Date: 2026-09-05

Changes:
    1. Create three PostgreSQL enum types:
           drivesourceformat           (pdf, text)
           drivesourceprocessingstatus (uploaded, processing, completed, failed)
           drivesourcevalidationstatus (pending, valid, invalid)
    2. Create `drive_sources` table for versioned ingestion records.
    3. Create composite index on (drive_id, version) for efficient retrieval.

Design notes:
    - drive_sources rows are immutable after creation.
    - (drive_id, version) is UNIQUE — prevents concurrent duplicate version creation.
    - Cascade deletes from drives.id ensure orphan cleanup.
    - raw_content and normalized_content are TEXT — Phase 4.2 output is text,
      not structured intelligence (JSONB belongs in Phase 4.3 DriveSnapshot).

Non-destructive:
    - No existing tables are modified.
    - No existing data is changed.
    - Phase 4.1 drives and drive_snapshots tables are untouched.

Reversibility:
    - downgrade() is fully implemented and reverses all changes in reverse order.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "c5d6e7f8a9b0"
down_revision: Union[str, Sequence[str], None] = "b3c4d5e6f7a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Phase 4.2 Drive Ingestion & Parsing schema additions."""

    # -----------------------------------------------------------------------
    # Step 1: Create PostgreSQL enum types
    # -----------------------------------------------------------------------

    drivesourceformat_enum = sa.Enum(
        "pdf", "text",
        name="drivesourceformat",
    )
    drivesourceformat_enum.create(op.get_bind(), checkfirst=True)

    drivesourceprocessingstatus_enum = sa.Enum(
        "uploaded", "processing", "completed", "failed",
        name="drivesourceprocessingstatus",
    )
    drivesourceprocessingstatus_enum.create(op.get_bind(), checkfirst=True)

    drivesourcevalidationstatus_enum = sa.Enum(
        "pending", "valid", "invalid",
        name="drivesourcevalidationstatus",
    )
    drivesourcevalidationstatus_enum.create(op.get_bind(), checkfirst=True)

    # -----------------------------------------------------------------------
    # Step 2: Create drive_sources table
    # -----------------------------------------------------------------------

    op.create_table(
        "drive_sources",

        # Primary key
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),

        # Foreign key to drives
        sa.Column("drive_id", sa.Integer(), nullable=False),

        # Explicit version number — managed by service layer, never inferred
        sa.Column("version", sa.Integer(), nullable=False),

        # Source provenance
        sa.Column(
            "source_format",
            sa.Enum("pdf", "text", name="drivesourceformat", create_type=False),
            nullable=False,
        ),
        sa.Column("original_filename", sa.String(500), nullable=True),
        sa.Column("file_path", sa.String(1000), nullable=True),

        # Integrity
        sa.Column("content_hash", sa.String(64), nullable=False),

        # Pipeline provenance
        sa.Column("extraction_method", sa.String(100), nullable=True),
        sa.Column("extractor_version", sa.String(20), nullable=True),
        sa.Column("parser_version", sa.String(20), nullable=True),

        # Lifecycle status
        sa.Column(
            "processing_status",
            sa.Enum(
                "uploaded", "processing", "completed", "failed",
                name="drivesourceprocessingstatus",
                create_type=False,
            ),
            nullable=False,
            server_default="uploaded",
        ),
        sa.Column(
            "validation_status",
            sa.Enum(
                "pending", "valid", "invalid",
                name="drivesourcevalidationstatus",
                create_type=False,
            ),
            nullable=False,
            server_default="pending",
        ),

        # Content — TEXT only for Phase 4.2; structured intelligence is Phase 4.3
        sa.Column("raw_content", sa.Text(), nullable=True),
        sa.Column("normalized_content", sa.Text(), nullable=True),

        # Content statistics
        sa.Column("character_count", sa.Integer(), nullable=True),
        sa.Column("word_count", sa.Integer(), nullable=True),

        # Flexible metadata bag (duplicate flags, warnings, transformations, etc.)
        sa.Column(
            "processing_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),

        # Timestamps — processed_at is tracked separately from created_at
        # to support future async processing where they may diverge.
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),

        # Constraints
        sa.ForeignKeyConstraint(
            ["drive_id"],
            ["drives.id"],
            name="fk_drive_sources_drive_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("drive_id", "version", name="uq_drive_source_version"),
    )

    # -----------------------------------------------------------------------
    # Step 3: Indexes
    # -----------------------------------------------------------------------

    # FK index for efficient drive → sources queries
    op.create_index(
        "ix_drive_sources_drive_id",
        "drive_sources",
        ["drive_id"],
        unique=False,
    )

    # Index on content_hash for duplicate detection queries
    op.create_index(
        "ix_drive_sources_content_hash",
        "drive_sources",
        ["content_hash"],
        unique=False,
    )

    # Composite index for latest-source retrieval: (drive_id, version DESC)
    op.create_index(
        "ix_drive_sources_drive_latest",
        "drive_sources",
        ["drive_id", sa.text("version DESC")],
        unique=False,
        postgresql_using="btree",
    )


def downgrade() -> None:
    """Reverse Phase 4.2 Drive Ingestion & Parsing schema additions."""

    # Drop indexes first
    op.drop_index("ix_drive_sources_drive_latest", table_name="drive_sources")
    op.drop_index("ix_drive_sources_content_hash", table_name="drive_sources")
    op.drop_index("ix_drive_sources_drive_id", table_name="drive_sources")

    # Drop table
    op.drop_table("drive_sources")

    # Drop enum types in reverse creation order
    sa.Enum(name="drivesourcevalidationstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="drivesourceprocessingstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="drivesourceformat").drop(op.get_bind(), checkfirst=True)

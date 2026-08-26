"""Pre-Phase 3.6: Add resume_type and processing_status columns to resume_files

Adds:
    - resumetype       PostgreSQL ENUM type (generic, specialized)
    - processingstatus PostgreSQL ENUM type (uploaded, processing, completed, failed)
    - resume_files.resume_type          NOT NULL, default='generic'
    - resume_files.processing_status    NOT NULL, default='uploaded'
    - UNIQUE constraint uq_student_resume_type on (student_id, resume_type)

Migration safety:
    - Both new columns have server_default values, so all existing rows receive
      valid values and the NOT NULL constraint is safe to apply.
    - Existing unique constraint uq_student_resume_hash is preserved.
    - No existing columns are dropped or modified.
    - Downgrade removes columns, constraints, and ENUM types cleanly.

Revision ID: a1b2c3d4e5f6
Revises: 3cd4b7921bf2
Create Date: 2026-08-25
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '3cd4b7921bf2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Upgrade schema:
        1. Create ENUM types (idempotent — checkfirst=True).
        2. Add resume_type column with server_default='generic'.
        3. Add processing_status column with server_default='uploaded'.
        4. Add unique constraint on (student_id, resume_type).
    """
    # 1. Create PostgreSQL ENUM types
    resumetype_enum = postgresql.ENUM(
        'generic', 'specialized',
        name='resumetype',
        create_type=False,
    )
    resumetype_enum.create(op.get_bind(), checkfirst=True)

    processingstatus_enum = postgresql.ENUM(
        'uploaded', 'processing', 'completed', 'failed',
        name='processingstatus',
        create_type=False,
    )
    processingstatus_enum.create(op.get_bind(), checkfirst=True)

    # 2. Add resume_type column — all existing rows get 'generic' via server_default
    op.add_column(
        'resume_files',
        sa.Column(
            'resume_type',
            sa.Enum('generic', 'specialized', name='resumetype'),
            nullable=False,
            server_default='generic',
        ),
    )

    # 3. Add processing_status column — all existing rows get 'uploaded' via server_default
    op.add_column(
        'resume_files',
        sa.Column(
            'processing_status',
            sa.Enum('uploaded', 'processing', 'completed', 'failed', name='processingstatus'),
            nullable=False,
            server_default='uploaded',
        ),
    )

    # 4. Add unique constraint: at most one resume per type per student
    op.create_unique_constraint(
        'uq_student_resume_type',
        'resume_files',
        ['student_id', 'resume_type'],
    )


def downgrade() -> None:
    """
    Downgrade schema:
        1. Drop unique constraint.
        2. Drop added columns.
        3. Drop ENUM types (only if no other table references them).
    """
    # 1. Drop unique constraint
    op.drop_constraint('uq_student_resume_type', 'resume_files', type_='unique')

    # 2. Drop added columns
    op.drop_column('resume_files', 'processing_status')
    op.drop_column('resume_files', 'resume_type')

    # 3. Drop ENUM types
    op.execute("DROP TYPE IF EXISTS processingstatus")
    op.execute("DROP TYPE IF EXISTS resumetype")

"""add candidate intelligence snapshots

Revision ID: 1cc54a3f84f8
Revises: 4bbe7eda418f
Create Date: 2026-08-29 17:52:49.930018

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1cc54a3f84f8'
down_revision: Union[str, Sequence[str], None] = '4bbe7eda418f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


from sqlalchemy.dialects import postgresql

def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('candidate_intelligence_snapshots',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('resume_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('profile_version', sa.String(), nullable=False),
    sa.Column('analysis_version', sa.String(), nullable=False),
    sa.Column('profile_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('generated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_candidate_intelligence_snapshots_resume_latest', 'candidate_intelligence_snapshots', ['resume_id', sa.text('generated_at DESC NULLS LAST')], unique=False, postgresql_using='btree')


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_candidate_intelligence_snapshots_resume_latest', table_name='candidate_intelligence_snapshots', postgresql_using='btree')
    op.drop_table('candidate_intelligence_snapshots')


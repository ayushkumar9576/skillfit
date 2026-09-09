"""Phase 4.4 Architecture Cleanup: Drop legacy duplicate columns from drives

Revision ID: d4e5f6a7b8c9
Revises: f17823be3884
Create Date: 2026-09-08 23:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = 'f17823be3884'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Phase 4.4 — Drop duplicate legacy JSONB columns from drives table
    # Drive Intelligence snapshots are the single authoritative source of truth.
    op.drop_column('drives', 'required_skills')
    op.drop_column('drives', 'preferred_skills')
    op.drop_column('drives', 'structured_eligibility')


def downgrade() -> None:
    op.add_column('drives', sa.Column('structured_eligibility', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('drives', sa.Column('preferred_skills', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('drives', sa.Column('required_skills', postgresql.JSONB(astext_type=sa.Text()), nullable=True))

"""Phase 4.3A Drive Intelligence Hardening: Add GIN index to drive_snapshots

Revision ID: f17823be3884
Revises: 2ab8e6915bd6
Create Date: 2026-09-05 02:32:24.520200

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f17823be3884'
down_revision: Union[str, Sequence[str], None] = '2ab8e6915bd6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # We use postgresql_using="gin" natively for this index
    op.create_index(
        "ix_drive_snapshots_intelligence",
        "drive_snapshots",
        ["intelligence_payload"],
        unique=False,
        postgresql_using="gin"
    )


def downgrade() -> None:
    op.drop_index(
        "ix_drive_snapshots_intelligence",
        table_name="drive_snapshots",
        postgresql_using="gin"
    )

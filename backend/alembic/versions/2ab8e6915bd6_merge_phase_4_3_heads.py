"""Merge Phase 4.3 heads

Revision ID: 2ab8e6915bd6
Revises: 998cfbd07c9a, a79b8dd9f9ad
Create Date: 2026-09-05 02:30:59.756791

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2ab8e6915bd6'
down_revision: Union[str, Sequence[str], None] = ('998cfbd07c9a', 'a79b8dd9f9ad')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

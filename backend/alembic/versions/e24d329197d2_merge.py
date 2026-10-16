"""merge

Revision ID: e24d329197d2
Revises: d4e5f6a7b8c9, f117d1c73ff5
Create Date: 2026-10-02 19:10:18.678561

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e24d329197d2'
down_revision: Union[str, Sequence[str], None] = ('d4e5f6a7b8c9', 'f117d1c73ff5')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

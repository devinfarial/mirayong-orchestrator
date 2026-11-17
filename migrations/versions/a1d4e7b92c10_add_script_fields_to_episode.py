"""add script fields to episode

Revision ID: a1d4e7b92c10
Revises: c30f97e5ad2a
Create Date: 2026-11-17 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1d4e7b92c10'
down_revision: Union[str, Sequence[str], None] = 'c30f97e5ad2a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('episode', sa.Column('topic', sa.String(length=255), nullable=True))
    op.add_column('episode', sa.Column('target_age_band', sa.String(length=20), nullable=True))
    op.add_column('episode', sa.Column('script_json', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('episode', 'script_json')
    op.drop_column('episode', 'target_age_band')
    op.drop_column('episode', 'topic')

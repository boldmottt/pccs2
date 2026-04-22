"""Add k_over_s column to inks table

Revision ID: db226ee0e713
Revises: 
Create Date: 2026-04-22 23:51:12.853101

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'db226ee0e713'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add k_over_s column to inks table."""
    op.add_column('inks', sa.Column('k_over_s', sa.Float(), nullable=True))


def downgrade() -> None:
    """Remove k_over_s column from inks table."""
    op.drop_column('inks', 'k_over_s')

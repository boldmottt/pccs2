"""Add unique constraint to ink_name

Revision ID: a1b2c3d4e5f6
Revises: db226ee0e713
Create Date: 2026-04-22 23:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'db226ee0e713'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint('uq_inks_ink_name', 'inks', ['ink_name'])


def downgrade() -> None:
    op.drop_constraint('uq_inks_ink_name', 'inks', type_='unique')

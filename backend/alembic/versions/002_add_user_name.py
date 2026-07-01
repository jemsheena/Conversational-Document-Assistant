"""Add user name column

Revision ID: 002
Revises: 001
Create Date: 2026-07-01

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("name", sa.String(), nullable=True))
    op.execute("UPDATE users SET name = split_part(email, '@', 1) WHERE name IS NULL")
    op.alter_column("users", "name", nullable=False)


def downgrade() -> None:
    op.drop_column("users", "name")

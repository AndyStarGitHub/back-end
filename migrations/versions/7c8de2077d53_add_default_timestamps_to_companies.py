"""Add default timestamps to companies

Revision ID: 7c8de2077d53
Revises: 3aaea7102584
Create Date: 2025-11-21 11:57:18.318808

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7c8de2077d53'
down_revision: Union[str, Sequence[str], None] = '3aaea7102584'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "UPDATE companies SET created_at = NOW() WHERE created_at IS NULL"
    )
    op.execute(
        "UPDATE companies SET updated_at = NOW() WHERE updated_at IS NULL"
    )

    op.alter_column(
        "companies",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("CURRENT_TIMESTAMP"),
    )
    op.alter_column(
        "companies",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("CURRENT_TIMESTAMP"),
    )


def downgrade() -> None:
    op.alter_column(
        "companies",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
        server_default=None,
    )
    op.alter_column(
        "companies",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
        server_default=None,
    )

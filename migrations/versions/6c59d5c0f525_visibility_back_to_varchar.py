"""visibility back to varchar

Revision ID: 6c59d5c0f525
Revises: 678a476dddb0
Create Date: 2025-11-20 13:21:10.846270

"""
from typing import Sequence, Union


from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '6c59d5c0f525'
down_revision: Union[str, Sequence[str], None] = '678a476dddb0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE companies "
        "ALTER COLUMN visibility TYPE VARCHAR(20) "
        "USING visibility::text"
    )

    company_visibility_enum = postgresql.ENUM(
        'hidden',
        'public',
        name='companyvisibilityenum',
    )
    company_visibility_enum.drop(op.get_bind(), checkfirst=True)


def downgrade() -> None:
    company_visibility_enum = postgresql.ENUM(
        'hidden',
        'public',
        name='companyvisibilityenum',
        create_type=True,
    )
    company_visibility_enum.create(op.get_bind(), checkfirst=True)

    op.execute(
        "ALTER TABLE companies "
        "ALTER COLUMN visibility TYPE companyvisibilityenum "
        "USING visibility::text::companyvisibilityenum"
    )

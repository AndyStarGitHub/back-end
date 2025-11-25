"""enum for quiz frequency

Revision ID: bd31fa14dbd1
Revises: bf98a286a34a
Create Date: 2025-11-25 18:36:16.892843

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'bd31fa14dbd1'
down_revision: Union[str, Sequence[str], None] = 'bf98a286a34a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    quiz_frequency_enum = postgresql.ENUM(
        'monthly',
        'quarterly',
        'yearly',
        'custom',
        name='quiz_frequency_enum',
        create_type=True,
    )
    quiz_frequency_enum.create(op.get_bind(), checkfirst=True)

    op.alter_column(
        'quizzes',
        'frequency',
        existing_type=sa.VARCHAR(length=20),
        type_=quiz_frequency_enum,
        existing_nullable=False,
        postgresql_using="frequency::text::quiz_frequency_enum",
    )



def downgrade() -> None:
    quiz_frequency_enum = postgresql.ENUM(
        'monthly',
        'quarterly',
        'yearly',
        'custom',
        name='quiz_frequency_enum',
    )

    op.alter_column(
        'quizzes',
        'frequency',
        existing_type=quiz_frequency_enum,
        type_=sa.VARCHAR(length=20),
        existing_nullable=False,
    )

    quiz_frequency_enum.drop(op.get_bind(), checkfirst=True)

    # ### end Alembic commands ###

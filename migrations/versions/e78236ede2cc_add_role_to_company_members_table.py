"""add role to company_members table

Revision ID: e78236ede2cc
Revises: d84797e31149
Create Date: 2025-11-22 14:43:19.687491

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e78236ede2cc'
down_revision: Union[str, Sequence[str], None] = 'd84797e31149'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        'company_join_requests',
        'status',
        existing_type=sa.VARCHAR(length=20),
        type_=sa.Enum(
            'PENDING',
            'APPROVED',
            'REJECTED',
            'CANCELED',
            name='company_join_request_status',
            native_enum=False,
        ),
        existing_nullable=False,
    )

    company_member_role = sa.Enum(
        'member',
        'admin',
        name='company_member_role',
    )

    company_member_role.create(op.get_bind(), checkfirst=True)

    op.add_column(
        'company_members',
        sa.Column(
            'role',
            company_member_role,
            nullable=False,
            server_default='member',
        ),
    )



def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('company_members', 'role')

    company_member_role = sa.Enum(
        'member',
        'admin',
        name='company_member_role',
    )
    company_member_role.drop(op.get_bind(), checkfirst=True)

    op.alter_column(
        'company_join_requests',
        'status',
        existing_type=sa.Enum(
            'PENDING',
            'APPROVED',
            'REJECTED',
            'CANCELED',
            name='company_join_request_status',
            native_enum=False,
        ),
        type_=sa.VARCHAR(length=20),
        existing_nullable=False,
    )


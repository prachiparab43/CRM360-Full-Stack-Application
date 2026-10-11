"""Add google_sub and auth_provider to employees table

Revision ID: e2f8b5c90d1a
Revises: b59ff78099cf
Create Date: 2026-10-11 19:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e2f8b5c90d1a'
down_revision: Union[str, Sequence[str], None] = 'b59ff78099cf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Add google_sub and auth_provider with nullable unique constraint on google_sub."""
    # 1. Add google_sub (nullable)
    op.add_column('employees', sa.Column('google_sub', sa.String(length=255), nullable=True))
    
    # 2. Create filtered unique index on google_sub (SQL Server allows only ONE NULL in standard unique index, so filter WHERE google_sub IS NOT NULL)
    op.create_index(
        op.f('ix_employees_google_sub'), 
        'employees', 
        ['google_sub'], 
        unique=True,
        mssql_where=sa.text('google_sub IS NOT NULL')
    )
    
    # 3. Add auth_provider (defaults to 'local' for existing users)
    op.add_column('employees', sa.Column('auth_provider', sa.String(length=50), server_default='local', nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('employees', 'auth_provider')
    op.drop_index(op.f('ix_employees_google_sub'), table_name='employees')
    op.drop_column('employees', 'google_sub')

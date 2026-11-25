"""Add is_system to roles, manager_id to employees, and migrate old stage action

Revision ID: a1c2d3e4f5a6
Revises: e2f8b5c90d1a
Create Date: 2026-10-25 18:36:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1c2d3e4f5a6'
down_revision: Union[str, Sequence[str], None] = 'e2f8b5c90d1a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add is_system to roles table
    op.add_column('roles', sa.Column('is_system', sa.Boolean(), server_default='0', nullable=False))
    
    # 2. Add manager_id to employees table
    op.add_column('employees', sa.Column('manager_id', sa.Integer(), sa.ForeignKey('employees.id'), nullable=True))
    
    # 3. Mark existing seeded admin role as is_system = 1
    op.execute("UPDATE roles SET is_system = 1 WHERE name = 'System Administrator'")
    
    # 4. Data migration: rename old action 'Change Stage' -> 'Change Opportunity Stage'
    op.execute("UPDATE role_permissions SET action = 'Change Opportunity Stage' WHERE action = 'Change Stage'")


def downgrade() -> None:
    # 1. Revert action name
    op.execute("UPDATE role_permissions SET action = 'Change Stage' WHERE action = 'Change Opportunity Stage'")
    
    # 2. Drop manager_id column
    op.drop_column('employees', 'manager_id')
    
    # 3. Drop is_system column
    op.drop_column('roles', 'is_system')

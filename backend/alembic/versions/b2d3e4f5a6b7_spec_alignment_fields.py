"""spec alignment fields

Revision ID: b2d3e4f5a6b7
Revises: a1c2d3e4f5a6
Create Date: 2026-10-25 19:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b2d3e4f5a6b7'
down_revision = 'a1c2d3e4f5a6'
branch_labels = None
depends_on = None


def upgrade():
    # Add created_date to opportunities
    op.add_column(
        'opportunities',
        sa.Column('created_date', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False)
    )

    # Add customer_id and visit_id to geo_tracking
    op.add_column('geo_tracking', sa.Column('customer_id', sa.Integer(), nullable=True))
    op.add_column('geo_tracking', sa.Column('visit_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_geo_tracking_customer_id', 'geo_tracking', 'customers', ['customer_id'], ['id'])
    op.create_foreign_key('fk_geo_tracking_visit_id', 'geo_tracking', 'customer_visits', ['visit_id'], ['id'])


def downgrade():
    op.drop_constraint('fk_geo_tracking_visit_id', 'geo_tracking', type_='foreignkey')
    op.drop_constraint('fk_geo_tracking_customer_id', 'geo_tracking', type_='foreignkey')
    op.drop_column('geo_tracking', 'visit_id')
    op.drop_column('geo_tracking', 'customer_id')
    op.drop_column('opportunities', 'created_date')

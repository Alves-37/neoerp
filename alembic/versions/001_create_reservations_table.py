"""Create reservations table

Revision ID: 001
Revises: 
Create Date: 2026-03-28 13:51:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create reservations table
    op.create_table(
        'reservations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('branch_id', sa.Integer(), nullable=False),
        sa.Column('establishment_id', sa.Integer(), nullable=True),
        sa.Column('customer_name', sa.String(length=200), nullable=False),
        sa.Column('customer_phone', sa.String(length=50), nullable=True),
        sa.Column('customer_email', sa.String(length=200), nullable=True),
        sa.Column('customer_nuit', sa.String(length=50), nullable=True),
        sa.Column('table_id', sa.Integer(), nullable=False),
        sa.Column('reservation_date', sa.DateTime(), nullable=False),
        sa.Column('time_slot', sa.String(length=50), nullable=False),
        sa.Column('people_count', sa.Integer(), nullable=False),
        sa.Column('estimated_amount', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('deposit_percentage', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('deposit_amount', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('payment_method', sa.String(length=50), nullable=True),
        sa.Column('payment_status', sa.String(length=50), nullable=False),
        sa.Column('payment_reference', sa.String(length=200), nullable=True),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('special_requests', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        sa.Column('cancelled_by', sa.Integer(), nullable=True),
        sa.Column('cancellation_reason', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_reservations_id', 'reservations', ['id'], unique=False)
    op.create_index('ix_reservations_company_id', 'reservations', ['company_id'], unique=False)
    op.create_index('ix_reservations_branch_id', 'reservations', ['branch_id'], unique=False)
    op.create_index('ix_reservations_establishment_id', 'reservations', ['establishment_id'], unique=False)
    op.create_index('ix_reservations_table_id', 'reservations', ['table_id'], unique=False)
    op.create_index('ix_reservations_reservation_date', 'reservations', ['reservation_date'], unique=False)


def downgrade():
    # Drop indexes
    op.drop_index('ix_reservations_reservation_date', table_name='reservations')
    op.drop_index('ix_reservations_table_id', table_name='reservations')
    op.drop_index('ix_reservations_establishment_id', table_name='reservations')
    op.drop_index('ix_reservations_branch_id', table_name='reservations')
    op.drop_index('ix_reservations_company_id', table_name='reservations')
    op.drop_index('ix_reservations_id', table_name='reservations')
    
    # Drop table
    op.drop_table('reservations')

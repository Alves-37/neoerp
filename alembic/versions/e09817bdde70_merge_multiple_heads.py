"""merge multiple heads

Revision ID: e09817bdde70
Revises: 001, create_reservations_table
Create Date: 2026-03-30 07:38:03.838257

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e09817bdde70'
down_revision = ('001', 'create_reservations_table')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

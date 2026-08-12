"""add_not_announced_not_available_ipo_status

Revision ID: e29b1e56c9da
Revises: 5179cb70c1da
Create Date: 2026-08-09 00:17:03.164276

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'e29b1e56c9da'
down_revision = '5179cb70c1da'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new enum values to ipostatus enum
    op.execute("ALTER TYPE ipostatus ADD VALUE IF NOT EXISTS 'not_announced'")
    op.execute("ALTER TYPE ipostatus ADD VALUE IF NOT EXISTS 'not_available'")
    op.execute("ALTER TYPE ipostatus ADD VALUE IF NOT EXISTS 'not_applicable'")


def downgrade() -> None:
    # Cannot easily remove enum values in PostgreSQL
    # Would need to create new enum, migrate data, drop old enum
    pass

"""Add tiers to users

Revision ID: 122ab8da0a64
Revises: 64224f776e0f
Create Date: 2019-03-11 13:53:41.246327

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "122ab8da0a64"
down_revision = "64224f776e0f"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "user",
        sa.Column("tier", sa.String(length=64), nullable=False, server_default="free"),
    )
    pass


def downgrade():
    op.drop_column("user", "tier")
    pass

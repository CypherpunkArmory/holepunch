"""add confirmed to user table

Revision ID: 64224f776e0f
Revises: 144e9019ab26
Create Date: 2019-02-07 11:19:14.932807

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "64224f776e0f"
down_revision = "144e9019ab26"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("user", sa.Column("confirmed", sa.BOOLEAN, nullable=False))
    pass


def downgrade():
    op.drop_column("user", "confirmed")
    pass

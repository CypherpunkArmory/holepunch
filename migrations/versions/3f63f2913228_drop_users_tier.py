"""Drop Users.tier

Revision ID: 3f63f2913228
Revises: 1e1c9c5d8e58
Create Date: 2019-06-10 19:38:58.873906

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "3f63f2913228"
down_revision = "1e1c9c5d8e58"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("user", "tier")


def downgrade():
    op.add_column(
        "user", sa.Column("tier", sa.String(), nullable=False, server_default="free")
    )

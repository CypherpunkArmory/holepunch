"""change port to array

Revision ID: 144e9019ab26
Revises: 083b261e3b0b
Create Date: 2019-01-31 15:06:29.318018

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "144e9019ab26"
down_revision = "083b261e3b0b"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "tunnel", "port", type_=sa.ARRAY(sa.String()), postgresql_using="array[port]"
    )
    pass


def downgrade():
    op.alter_column("tunnel", "port", type_=sa.String())
    pass

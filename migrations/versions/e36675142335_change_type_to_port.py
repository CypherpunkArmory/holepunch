"""change type to port

Revision ID: e36675142335
Revises: c8493c83258e
Create Date: 2018-12-13 07:20:13.507447

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e36675142335"
down_revision = "c8493c83258e"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("tunnel", "type", nullable=False, new_column_name="port")
    pass


def downgrade():
    op.alter_column("tunnel", "port", nullable=False, new_column_name="type")
    pass

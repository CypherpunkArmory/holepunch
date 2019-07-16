"""add tcp_ports to tunnel

Revision ID: 8813ddff05a2
Revises: 3f63f2913228
Create Date: 2019-05-29 15:36:44.016262

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "8813ddff05a2"
down_revision = "3f63f2913228"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("tunnel", sa.Column("allocated_tcp_ports", sa.ARRAY(sa.Integer())))
    pass


def downgrade():
    op.drop_column("tunnel", "allocated_tcp_ports", type_=sa.ARRAY(sa.Integer()))
    pass

"""add ip address to tunnel

Revision ID: bf5251abcaa2
Revises: aaea9ed1df44
Create Date: 2019-01-04 22:24:31.912116

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "bf5251abcaa2"
down_revision = "aaea9ed1df44"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "tunnel", sa.Column("ip_address", sa.String(length=32), nullable=True)
    )
    op.drop_constraint("tunnel_user_id_fkey", "tunnel", type_="foreignkey")
    op.drop_column("tunnel", "user_id")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "tunnel", sa.Column("user_id", sa.INTEGER(), autoincrement=False, nullable=True)
    )
    op.create_foreign_key("tunnel_user_id_fkey", "tunnel", "user", ["user_id"], ["id"])
    op.drop_column("tunnel", "ip_address")
    # ### end Alembic commands ###

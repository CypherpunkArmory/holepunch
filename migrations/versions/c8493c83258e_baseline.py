"""baseline

Revision ID: c8493c83258e
Revises: 
Create Date: 2018-09-05 15:53:19.622321

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "c8493c83258e"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # docker exec holepunch_db_1 createdb -U postgres holepunch_development
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=64), nullable=True),
        sa.Column("password_hash", sa.String(length=128), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_email"), "user", ["email"], unique=True)
    op.create_table(
        "subdomain",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False, unique=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("reserved", sa.BOOLEAN, nullable=False),
        sa.Column("in_use", sa.BOOLEAN, nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_subdomain_name"), "subdomain", ["name"], unique=True)
    op.create_table(
        "tunnel",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tunnel_server", sa.String(length=64), nullable=False),
        sa.Column("tunnel_ssh_port", sa.Integer(), nullable=False),
        sa.Column("tunnel_connection_port", sa.Integer(), nullable=False),
        sa.Column("subdomain_id", sa.Integer(), nullable=False, unique=True),
        sa.Column("type", sa.String(length=16), nullable=False),
        sa.Column("subdomain_id", sa.Integer(), nullable=False, unique=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["subdomain_id"], ["subdomain.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tunnel_id"), "tunnel", ["id"], unique=True)
    pass


def downgrade():
    op.drop_index(op.f("ix_user_email"), table_name="user")
    op.drop_table("user")
    op.drop_index(op.f("ix_tunnel_id"), table_name="tunnel")
    op.drop_table("tunnel")
    op.drop_index(op.f("ix_subdomain_name"), table_name="subdomain")
    op.drop_table("subdomain")
    pass

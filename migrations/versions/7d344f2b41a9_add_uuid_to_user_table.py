"""add uuid to user table

Revision ID: 7d344f2b41a9
Revises: 122ab8da0a64
Create Date: 2019-04-22 14:39:17.330526

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = "7d344f2b41a9"
down_revision = "122ab8da0a64"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute(sa.text('create extension if not exists "uuid-ossp";'))
    op.add_column(
        "user",
        sa.Column(
            "uuid",
            UUID(as_uuid=True),
            nullable=False,
            unique=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
    )
    pass


def downgrade():
    op.drop_column("user", "uuid")
    pass

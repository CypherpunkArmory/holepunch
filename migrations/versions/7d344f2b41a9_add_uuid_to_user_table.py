"""add uuid to user table

Revision ID: 7d344f2b41a9
Revises: 122ab8da0a64
Create Date: 2019-04-22 14:39:17.330526

"""
from alembic import op
import sqlalchemy as sa
import uuid


# revision identifiers, used by Alembic.
revision = "7d344f2b41a9"
down_revision = "122ab8da0a64"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "user",
        sa.Column(
            "uuid",
            sa.String(length=64),
            nullable=False,
            unique=True,
            server_default=str(uuid.uuid4()),
        ),
    )
    pass


def downgrade():
    op.drop_column("user", "uuid")
    pass

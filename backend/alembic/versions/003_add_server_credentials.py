"""add server_credentials table

Revision ID: 003_add_server_credentials
Revises: 002_add_refresh_tokens
Create Date: 2026-09-29 10:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "003_add_server_credentials"
down_revision: Union[str, None] = "002_add_refresh_tokens"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "server_credentials",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "server_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("servers.id", ondelete="CASCADE"),
            unique=True,
            nullable=False,
        ),
        sa.Column("auth_type", sa.String(length=32), nullable=False, server_default="PASSWORD"),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("encrypted_password", sa.Text(), nullable=True),
        sa.Column("encrypted_private_key", sa.Text(), nullable=True),
        sa.Column("encrypted_passphrase", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_server_credentials_server_id", "server_credentials", ["server_id"])


def downgrade() -> None:
    op.drop_table("server_credentials")

"""Add activity_logs, build_logs, knowledge_entries tables

Revision ID: 004_activity_tracking
Revises: 003_settings_audit
Create Date: 2026-06-05
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "004_activity_tracking"
down_revision: Union[str, None] = "003_settings_audit"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "activity_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=True),
        sa.Column("category", sa.String(50), nullable=False, index=True),
        sa.Column("action", sa.String(200), nullable=False),
        sa.Column("detail", sa.Text, nullable=True),
        sa.Column("metadata_json", sa.JSON, nullable=True),
        sa.Column("ip_address", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), index=True),
    )

    op.create_table(
        "build_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("agent_name", sa.String(100), nullable=False),
        sa.Column("commit_sha", sa.String(40), nullable=True),
        sa.Column("action", sa.String(200), nullable=False),
        sa.Column("files_changed", sa.JSON, nullable=True),
        sa.Column("detail", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "knowledge_entries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=True),
        sa.Column("category", sa.String(50), nullable=False, index=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("source", sa.String(200), nullable=True),
        sa.Column("tags", sa.JSON, nullable=True),
        sa.Column("version", sa.Integer, nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("knowledge_entries")
    op.drop_table("build_logs")
    op.drop_table("activity_logs")

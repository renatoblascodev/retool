"""add app_members and templates tables

Revision ID: 0003
Revises: 0002
Create Date: 2026-03-16 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── app_members ──────────────────────────────────────────────────────────
    op.create_table(
        "app_members",
        sa.Column(
            "app_id",
            sa.String(36),
            sa.ForeignKey("apps.id", ondelete="CASCADE"),
            nullable=False,
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            primary_key=True,
        ),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column(
            "joined_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("role IN ('owner', 'editor', 'viewer')", name="ck_app_members_role"),
    )
    op.create_index("ix_app_members_user_id", "app_members", ["user_id"])

    # ── templates ────────────────────────────────────────────────────────────
    op.create_table(
        "templates",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("slug", sa.String(80), nullable=False, unique=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("category", sa.String(60), nullable=False, server_default="general"),
        sa.Column(
            "layout_json",
            sa.Text,
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_templates_slug", "templates", ["slug"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_templates_slug", table_name="templates")
    op.drop_table("templates")
    op.drop_index("ix_app_members_user_id", table_name="app_members")
    op.drop_table("app_members")

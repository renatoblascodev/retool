"""add is_public and creator_id to templates

Revision ID: 0004
Revises: 0003
Create Date: 2026-03-16 12:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "templates",
        sa.Column("is_public", sa.Boolean, nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "templates",
        sa.Column(
            "creator_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_templates_creator_id", "templates", ["creator_id"])


def downgrade() -> None:
    op.drop_index("ix_templates_creator_id", table_name="templates")
    op.drop_column("templates", "creator_id")
    op.drop_column("templates", "is_public")

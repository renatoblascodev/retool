"""add publish columns to apps table

Revision ID: 0007
Revises: 0006
Create Date: 2026-03-16 14:30:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "apps",
        sa.Column("is_published", sa.Boolean, nullable=False, server_default="false"),
    )
    op.add_column(
        "apps",
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "apps",
        sa.Column("slug", sa.String(100), nullable=True),
    )
    op.create_unique_constraint("uq_apps_slug", "apps", ["slug"])


def downgrade() -> None:
    op.drop_constraint("uq_apps_slug", "apps", type_="unique")
    op.drop_column("apps", "slug")
    op.drop_column("apps", "published_at")
    op.drop_column("apps", "is_published")

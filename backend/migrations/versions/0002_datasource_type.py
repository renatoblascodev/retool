"""add ds_type to datasources

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-15 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "datasources",
        sa.Column(
            "ds_type",
            sa.String(20),
            nullable=False,
            server_default="rest",
        ),
    )
    # Make base_url nullable / allow empty string for SQL datasources that
    # don't need a base_url.  We keep the column but remove NOT NULL on the
    # server side by setting a server_default of empty string.
    op.alter_column(
        "datasources",
        "base_url",
        existing_type=sa.String(1000),
        nullable=True,
        server_default="",
    )


def downgrade() -> None:
    op.alter_column(
        "datasources",
        "base_url",
        existing_type=sa.String(1000),
        nullable=False,
        server_default=None,
    )
    op.drop_column("datasources", "ds_type")

"""add app_templates table with seeds

Revision ID: 0006
Revises: 0005
Create Date: 2026-03-16 14:00:00.000000
"""
from typing import Sequence, Union
import json

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_CRUD_LAYOUT = json.dumps({
    "widgets": [
        {
            "id": "t1", "type": "Table", "x": 0, "y": 0, "w": 12, "h": 8,
            "props": {
                "data": "{{query1.data}}",
                "columns": [{"key": "id"}, {"key": "name"}, {"key": "email"}],
            },
        },
        {
            "id": "t2", "type": "Button", "x": 0, "y": 9, "w": 2, "h": 1,
            "props": {"label": "Add Row"},
        },
    ]
})

_DASHBOARD_LAYOUT = json.dumps({
    "widgets": [
        {"id": "k1", "type": "Stat", "x": 0, "y": 0, "w": 4, "h": 2,
         "props": {"label": "Total", "value": "{{query1.data[0].total}}"}},
        {"id": "k2", "type": "Stat", "x": 4, "y": 0, "w": 4, "h": 2,
         "props": {"label": "Active", "value": "{{query1.data[0].active}}"}},
        {"id": "k3", "type": "Stat", "x": 8, "y": 0, "w": 4, "h": 2,
         "props": {"label": "New", "value": "{{query1.data[0].new_count}}"}},
        {"id": "k4", "type": "Table", "x": 0, "y": 3, "w": 12, "h": 8,
         "props": {"data": "{{query1.data}}"}},
    ]
})

_FORM_LAYOUT = json.dumps({
    "widgets": [
        {"id": "f1", "type": "TextInput", "x": 0, "y": 0, "w": 6, "h": 1,
         "props": {"label": "Name", "placeholder": "Your name"}},
        {"id": "f2", "type": "TextInput", "x": 0, "y": 2, "w": 6, "h": 1,
         "props": {"label": "Email", "placeholder": "your@email.com"}},
        {"id": "f3", "type": "Button", "x": 0, "y": 4, "w": 2, "h": 1,
         "props": {"label": "Submit"}},
    ]
})


def upgrade() -> None:
    op.create_table(
        "app_templates",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("thumbnail", sa.Text, nullable=True),
        sa.Column("layout_json", sa.dialects.postgresql.JSONB if hasattr(sa, "dialects") else sa.Text, nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.execute(f"""
        INSERT INTO app_templates (id, name, description, category, layout_json, is_active)
        VALUES
          (gen_random_uuid()::text, 'User Management', 'CRUD table for managing users', 'crud',
           '{_CRUD_LAYOUT}'::jsonb, true),
          (gen_random_uuid()::text, 'KPI Dashboard', 'Dashboard with KPI stat cards and data table', 'dashboard',
           '{_DASHBOARD_LAYOUT}'::jsonb, true),
          (gen_random_uuid()::text, 'Feedback Form', 'Simple form with Name, Email and Submit button', 'form',
           '{_FORM_LAYOUT}'::jsonb, true)
    """)


def downgrade() -> None:
    op.drop_table("app_templates")

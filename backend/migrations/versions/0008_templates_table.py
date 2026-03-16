"""create templates table with seeds

Revision ID: 0008
Revises: 0007
Create Date: 2026-03-16 15:00:00.000000
"""
from typing import Sequence, Union
import json

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: Union[str, None] = "0007"
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
    # templates table already exists (created by init_db) — add the two missing columns
    op.add_column(
        "templates",
        sa.Column("is_public", sa.Boolean, nullable=False, server_default="true"),
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

    # seed if table is empty
    crud_json = _CRUD_LAYOUT.replace("'", "''")
    dashboard_json = _DASHBOARD_LAYOUT.replace("'", "''")
    form_json = _FORM_LAYOUT.replace("'", "''")

    op.execute(f"""
        INSERT INTO templates (id, slug, name, description, category, layout_json, is_public)
        SELECT * FROM (VALUES
          (gen_random_uuid()::text, 'user-management', 'User Management',
           'CRUD table for managing users', 'crud', '{crud_json}'::text, true),
          (gen_random_uuid()::text, 'kpi-dashboard', 'KPI Dashboard',
           'Dashboard with KPI stat cards and data table', 'dashboard', '{dashboard_json}'::text, true),
          (gen_random_uuid()::text, 'feedback-form', 'Feedback Form',
           'Simple form with Name, Email and Submit button', 'form', '{form_json}'::text, true)
        ) AS v(id, slug, name, description, category, layout_json, is_public)
        WHERE NOT EXISTS (SELECT 1 FROM templates LIMIT 1)
    """)


def downgrade() -> None:
    op.drop_index("ix_templates_creator_id", table_name="templates")
    op.drop_column("templates", "creator_id")
    op.drop_column("templates", "is_public")

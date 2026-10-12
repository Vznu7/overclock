"""create_phase5_production_floor

Revision ID: 5a1b2c3d4e5f
Revises: 4e72a8190bc1
Create Date: 2026-10-12 17:35:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5a1b2c3d4e5f"
down_revision: str | None = "4e72a8190bc1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. production_lines table
    op.create_table(
        "production_lines",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("line_number", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("operator_count", sa.Integer(), nullable=False, server_default="24"),
        sa.Column("helper_count", sa.Integer(), nullable=False, server_default="4"),
        sa.Column("daily_working_hours", sa.Numeric(precision=4, scale=2), nullable=False, server_default="8.00"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_production_lines_tenant_id"),
        "production_lines",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        "ix_production_lines_tenant_line",
        "production_lines",
        ["tenant_id", "line_number"],
        unique=True,
    )

    # 2. daily_production_logs table
    op.create_table(
        "daily_production_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("order_id", sa.UUID(), nullable=False),
        sa.Column("line_id", sa.UUID(), nullable=True),
        sa.Column("stage", sa.String(length=32), nullable=False),
        sa.Column("planned_output", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("actual_output", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rejected_qty", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("operator_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("working_hours", sa.Numeric(precision=4, scale=2), nullable=False, server_default="8.00"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by_user_id", sa.UUID(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["line_id"], ["production_lines.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_daily_production_logs_tenant_id"),
        "daily_production_logs",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_daily_production_logs_date"),
        "daily_production_logs",
        ["date"],
        unique=False,
    )
    op.create_index(
        op.f("ix_daily_production_logs_order_id"),
        "daily_production_logs",
        ["order_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_daily_production_logs_line_id"),
        "daily_production_logs",
        ["line_id"],
        unique=False,
    )

    # Enable and Force Row Level Security (RLS) on both tables
    tables = ("production_lines", "daily_production_logs")
    for table in tables:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")
        op.execute(f"""
            CREATE POLICY {table}_tenant_isolation ON {table}
            FOR ALL
            USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), ''))
            WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), ''));
        """)

    # Grant permissions to unprivileged role overclock_app
    op.execute("GRANT ALL ON ALL TABLES IN SCHEMA public TO overclock_app;")
    op.execute("GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO overclock_app;")


def downgrade() -> None:
    tables = ("production_lines", "daily_production_logs")
    for table in tables:
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation ON {table};")
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")

    op.drop_table("daily_production_logs")
    op.drop_table("production_lines")

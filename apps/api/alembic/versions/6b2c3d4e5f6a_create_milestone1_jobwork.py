"""create_milestone1_jobwork

Revision ID: 6b2c3d4e5f6a
Revises: 5a1b2c3d4e5f
Create Date: 2026-10-12 18:35:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6b2c3d4e5f6a"
down_revision: str | None = "5a1b2c3d4e5f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. jobwork_processors table
    op.create_table(
        "jobwork_processors",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("process_type", sa.String(length=32), nullable=False),
        sa.Column("contact_person", sa.String(length=128), nullable=True),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
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
        op.f("ix_jobwork_processors_tenant_id"),
        "jobwork_processors",
        ["tenant_id"],
        unique=False,
    )

    # 2. jobwork_challans table
    op.create_table(
        "jobwork_challans",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("challan_number", sa.String(length=64), nullable=False),
        sa.Column("challan_type", sa.String(length=32), nullable=False, server_default="OUTWARD_ISSUE"),
        sa.Column("processor_id", sa.UUID(), nullable=False),
        sa.Column("order_id", sa.UUID(), nullable=True),
        sa.Column("process_name", sa.String(length=64), nullable=False),
        sa.Column("material_description", sa.String(length=255), nullable=False),
        sa.Column("issued_qty", sa.Numeric(precision=12, scale=3), nullable=False, server_default="0.000"),
        sa.Column("issued_weight_kg", sa.Numeric(precision=12, scale=3), nullable=False, server_default="0.000"),
        sa.Column("expected_return_date", sa.Date(), nullable=False),
        sa.Column("actual_return_date", sa.Date(), nullable=True),
        sa.Column("received_qty", sa.Numeric(precision=12, scale=3), nullable=False, server_default="0.000"),
        sa.Column("received_weight_kg", sa.Numeric(precision=12, scale=3), nullable=False, server_default="0.000"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="ISSUED"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["processor_id"], ["jobwork_processors.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_jobwork_challans_tenant_id"),
        "jobwork_challans",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_jobwork_challans_processor_id"),
        "jobwork_challans",
        ["processor_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_jobwork_challans_order_id"),
        "jobwork_challans",
        ["order_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_jobwork_challans_expected_date"),
        "jobwork_challans",
        ["expected_return_date"],
        unique=False,
    )
    op.create_index(
        "ix_jobwork_challans_tenant_number",
        "jobwork_challans",
        ["tenant_id", "challan_number"],
        unique=True,
    )

    # Enable and Force Row Level Security (RLS) on both tables
    tables = ("jobwork_processors", "jobwork_challans")
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
    tables = ("jobwork_processors", "jobwork_challans")
    for table in tables:
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation ON {table};")
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")

    op.drop_table("jobwork_challans")
    op.drop_table("jobwork_processors")

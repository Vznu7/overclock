import os

from sqlalchemy import create_engine, text

ADMIN_URL = os.getenv("DATABASE_ADMIN_URL", os.getenv("DATABASE_URL", ""))


def enable_tenants_rls():
    engine = create_engine(ADMIN_URL)
    with engine.begin() as conn:
        print("[*] Configuring RLS policies on public.tenants...")
        conn.execute(text("ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;"))
        conn.execute(text("ALTER TABLE tenants FORCE ROW LEVEL SECURITY;"))

        # Clean up any existing policies
        conn.execute(text("DROP POLICY IF EXISTS tenants_tenant_isolation ON tenants;"))
        conn.execute(text("DROP POLICY IF EXISTS tenants_select_policy ON tenants;"))
        conn.execute(text("DROP POLICY IF EXISTS tenants_insert_policy ON tenants;"))
        conn.execute(text("DROP POLICY IF EXISTS tenants_update_policy ON tenants;"))
        conn.execute(text("DROP POLICY IF EXISTS tenants_delete_policy ON tenants;"))

        # 1. Allow reading tenants (for login lookup & tenant verification)
        conn.execute(
            text("""
            CREATE POLICY tenants_select_policy ON tenants
            FOR SELECT
            USING (true);
        """)
        )

        # 2. Allow creating new tenants (for onboarding / signup)
        conn.execute(
            text("""
            CREATE POLICY tenants_insert_policy ON tenants
            FOR INSERT
            WITH CHECK (true);
        """)
        )

        # 3. Restrict updates to only the active session tenant
        conn.execute(
            text("""
            CREATE POLICY tenants_update_policy ON tenants
            FOR UPDATE
            USING (id = NULLIF(current_setting('app.tenant_id', true), ''))
            WITH CHECK (id = NULLIF(current_setting('app.tenant_id', true), ''));
        """)
        )

        # 4. Restrict deletes to only the active session tenant
        conn.execute(
            text("""
            CREATE POLICY tenants_delete_policy ON tenants
            FOR DELETE
            USING (id = NULLIF(current_setting('app.tenant_id', true), ''));
        """)
        )

        print("[OK] Row Level Security policies configured on public.tenants!")


if __name__ == "__main__":
    enable_tenants_rls()

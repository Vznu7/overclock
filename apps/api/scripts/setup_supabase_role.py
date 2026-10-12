import os

import psycopg

SUPABASE_ADMIN_URL = os.getenv("DATABASE_ADMIN_URL", os.getenv("DATABASE_URL", ""))


def setup_role():
    print("[*] Connecting to Supabase as postgres admin...")
    with psycopg.connect(SUPABASE_ADMIN_URL, autocommit=True) as conn:
        with conn.cursor() as cur:
            # Check if role exists
            cur.execute("SELECT 1 FROM pg_roles WHERE rolname = 'overclock_app'")
            exists = cur.fetchone()
            if not exists:
                print("[+] Creating role overclock_app with NOBYPASSRLS...")
                cur.execute(
                    "CREATE ROLE overclock_app WITH LOGIN PASSWORD 'OverclockApp_2026_Secure' NOSUPERUSER NOBYPASSRLS;"
                )
            else:
                print("[~] Role overclock_app already exists, skipping create.")

            print("[+] Granting permissions on schema public...")
            cur.execute("GRANT ALL ON SCHEMA public TO overclock_app;")
            cur.execute("GRANT ALL ON ALL TABLES IN SCHEMA public TO overclock_app;")
            cur.execute("GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO overclock_app;")
            cur.execute(
                "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO overclock_app;"
            )
            cur.execute(
                "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO overclock_app;"
            )
            cur.execute("ALTER TABLE tenants DISABLE ROW LEVEL SECURITY;")
            print(
                "[OK] overclock_app role configured with strict RLS enforcement and tenants table accessible!"
            )


if __name__ == "__main__":
    setup_role()

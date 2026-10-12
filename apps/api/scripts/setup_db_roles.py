import psycopg


def setup_roles():
    sql = """
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'overclock_app') THEN
            CREATE ROLE overclock_app WITH LOGIN PASSWORD 'overclock_app_password' NOSUPERUSER NOBYPASSRLS;
        ELSE
            ALTER ROLE overclock_app WITH NOSUPERUSER NOBYPASSRLS;
        END IF;
    END
    $$;

    GRANT ALL ON DATABASE overclock TO overclock_app;
    GRANT USAGE, CREATE ON SCHEMA public TO overclock_app;
    GRANT ALL ON ALL TABLES IN SCHEMA public TO overclock_app;
    GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO overclock_app;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO overclock_app;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO overclock_app;
    """
    with psycopg.connect(
        "host=localhost port=5433 user=overclock dbname=overclock", autocommit=True
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            print("Successfully configured overclock_app role with NOSUPERUSER and NOBYPASSRLS!")


if __name__ == "__main__":
    setup_roles()

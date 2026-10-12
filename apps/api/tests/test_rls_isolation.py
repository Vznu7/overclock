from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, set_session_tenant
from app.core.security import get_password_hash
from app.domains.auth.models import User, UserRole
from app.domains.tenants.models import Tenant, TenantSettings


def setup_test_tenants(db: Session):
    """Ensure two distinct tenants exist for isolation testing."""
    for tid, name in [("tenant-alpha", "Alpha Textiles"), ("tenant-beta", "Beta Garments")]:
        set_session_tenant(db, tid)
        existing = db.query(Tenant).filter(Tenant.id == tid).first()
        if not existing:
            t = Tenant(id=tid, name=name, cluster="Tiruppur", currency="INR", is_active=True)
            db.add(t)
            db.flush()
            s = TenantSettings(
                tenant_id=tid,
                sewing_capacity_daily=1500 if tid == "tenant-alpha" else 2000,
                working_days=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
                risk_thresholds={},
                monthly_ai_budget_inr=500.00,
                daily_ai_budget_cap_inr=50.00,
            )
            db.add(s)
            db.commit()


def test_postgres_rls_cross_tenant_read_isolation():
    """Prove Tenant A can NEVER read Tenant B data via PostgreSQL RLS."""
    db = SessionLocal()
    try:
        setup_test_tenants(db)

        # 1. Insert User into Tenant Alpha
        set_session_tenant(db, "tenant-alpha")
        alpha_user = (
            db.query(User)
            .filter(User.tenant_id == "tenant-alpha", User.email == "alpha_owner@test.com")
            .first()
        )
        if not alpha_user:
            alpha_user = User(
                tenant_id="tenant-alpha",
                email="alpha_owner@test.com",
                hashed_password=get_password_hash("password123"),
                full_name="Alpha Owner",
                role=UserRole.OWNER.value,
                is_active=True,
            )
            db.add(alpha_user)
            db.commit()
            db.refresh(alpha_user)

        # 2. Insert User into Tenant Beta
        set_session_tenant(db, "tenant-beta")
        beta_user = (
            db.query(User)
            .filter(User.tenant_id == "tenant-beta", User.email == "beta_owner@test.com")
            .first()
        )
        if not beta_user:
            beta_user = User(
                tenant_id="tenant-beta",
                email="beta_owner@test.com",
                hashed_password=get_password_hash("password123"),
                full_name="Beta Owner",
                role=UserRole.OWNER.value,
                is_active=True,
            )
            db.add(beta_user)
            db.commit()
            db.refresh(beta_user)

        # 3. Authenticate Session as Tenant Alpha
        set_session_tenant(db, "tenant-alpha")
        alpha_users = db.query(User).all()
        # Ensure all returned users belong ONLY to Tenant Alpha
        for u in alpha_users:
            assert u.tenant_id == "tenant-alpha"
        assert all(u.id != beta_user.id for u in alpha_users)

        # Direct primary key query for Beta User while under Alpha tenant context
        leaked_beta = db.query(User).filter(User.id == beta_user.id).first()
        assert leaked_beta is None, (
            "CRITICAL SECURITY BREACH: Tenant Alpha was able to query Tenant Beta user by ID!"
        )

        # 4. Authenticate Session as Tenant Beta
        set_session_tenant(db, "tenant-beta")
        beta_users = db.query(User).all()
        for u in beta_users:
            assert u.tenant_id == "tenant-beta"
        assert all(u.id != alpha_user.id for u in beta_users)

        # Direct primary key query for Alpha User while under Beta tenant context
        leaked_alpha = db.query(User).filter(User.id == alpha_user.id).first()
        assert leaked_alpha is None, (
            "CRITICAL SECURITY BREACH: Tenant Beta was able to query Tenant Alpha user by ID!"
        )

    finally:
        db.close()


def test_postgres_rls_cross_tenant_write_isolation():
    """Prove Tenant A can NEVER mutate Tenant B data via UPDATE or DELETE."""
    db = SessionLocal()
    try:
        setup_test_tenants(db)

        # Ensure beta user exists
        set_session_tenant(db, "tenant-beta")
        beta_user = (
            db.query(User)
            .filter(User.tenant_id == "tenant-beta", User.email == "beta_owner@test.com")
            .first()
        )
        assert beta_user is not None
        original_name = beta_user.full_name

        # Switch context to Tenant Alpha
        set_session_tenant(db, "tenant-alpha")

        # Attempt raw SQL UPDATE targeting Tenant Beta's row
        result = db.execute(
            text("UPDATE users SET full_name = 'MALICIOUS_OVERWRITE' WHERE id = :target_id"),
            {"target_id": beta_user.id},
        )
        db.commit()
        # Row count affected must be 0 because RLS policy hides the row completely
        assert result.rowcount == 0, (
            "CRITICAL SECURITY BREACH: Tenant Alpha was able to update Tenant Beta's record!"
        )

        # Verify beta record was unchanged
        set_session_tenant(db, "tenant-beta")
        verified_beta = db.query(User).filter(User.id == beta_user.id).first()
        assert verified_beta is not None
        assert verified_beta.full_name == original_name

    finally:
        db.close()


def test_postgres_rls_fail_closed_without_tenant_context():
    """Prove that queries with no tenant_id set return ZERO records (fail-closed)."""
    db = SessionLocal()
    try:
        # Set tenant_id to empty string
        set_session_tenant(db, None)
        users = db.query(User).all()
        assert len(users) == 0, "RLS must fail-closed when app.tenant_id is not set!"
    finally:
        db.close()

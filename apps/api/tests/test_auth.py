import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal, set_session_tenant
from app.core.security import get_password_hash, verify_password
from app.domains.auth.models import User, UserRole
from app.domains.tenants.models import Tenant, TenantSettings
from app.main import app

client = TestClient(app)


@pytest.fixture(scope="module")
def setup_auth_tenant():
    db = SessionLocal()
    tenant_id = "tenant-auth-test"
    try:
        t = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not t:
            t = Tenant(id=tenant_id, name="Auth Test Exports", cluster="Tiruppur", is_active=True)
            db.add(t)
            db.flush()
            set_session_tenant(db, tenant_id)
            s = TenantSettings(
                tenant_id=tenant_id, sewing_capacity_daily=1500, working_days=["Mon"]
            )
            db.add(s)
            db.commit()

        set_session_tenant(db, tenant_id)
        # Create test owner user
        owner = (
            db.query(User)
            .filter(User.tenant_id == tenant_id, User.email == "auth_owner@test.com")
            .first()
        )
        if not owner:
            owner = User(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                email="auth_owner@test.com",
                hashed_password=get_password_hash("ValidPass123!"),
                full_name="Auth Owner",
                role=UserRole.OWNER.value,
                is_active=True,
            )
            db.add(owner)
            db.commit()
    finally:
        db.close()
    return tenant_id


def test_argon2id_hashing_and_verification():
    """Verify passwords are encrypted with Argon2id and can be verified."""
    password = "SuperSecurePassword123"
    hashed = get_password_hash(password)
    assert hashed.startswith("$argon2id$")
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_login_success_and_cookie_generation(setup_auth_tenant):
    """Verify successful login returns valid JWT and sets HTTP-only secure cookie."""
    resp = client.post(
        "/api/v1/auth/login",
        json={
            "tenant_id": setup_auth_tenant,
            "email": "auth_owner@test.com",
            "password": "ValidPass123!",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["email"] == "auth_owner@test.com"
    assert data["role"] == "owner"
    assert data["tenant_id"] == setup_auth_tenant
    assert "access_token" in resp.cookies


def test_login_lockout_after_five_failed_attempts(setup_auth_tenant):
    """Verify 5 consecutive failed login attempts trigger a 15-minute account lockout."""
    db = SessionLocal()
    try:
        set_session_tenant(db, setup_auth_tenant)
        user = (
            db.query(User)
            .filter(User.tenant_id == setup_auth_tenant, User.email == "lockout_test@test.com")
            .first()
        )
        if not user:
            user = User(
                id=uuid.uuid4(),
                tenant_id=setup_auth_tenant,
                email="lockout_test@test.com",
                hashed_password=get_password_hash("CorrectPassword123"),
                full_name="Lockout Test User",
                role=UserRole.VIEWER.value,
                is_active=True,
            )
            db.add(user)
            db.commit()
        else:
            user.failed_login_attempts = 0
            user.locked_until = None
            db.commit()
    finally:
        db.close()

    # 4 consecutive failures
    for _attempt in range(1, 5):
        resp = client.post(
            "/api/v1/auth/login",
            json={
                "tenant_id": setup_auth_tenant,
                "email": "lockout_test@test.com",
                "password": "BadPassword",
            },
        )
        assert resp.status_code == 401
        assert "Invalid email or password" in resp.json()["detail"]

    # 5th failure -> triggers lockout
    resp = client.post(
        "/api/v1/auth/login",
        json={
            "tenant_id": setup_auth_tenant,
            "email": "lockout_test@test.com",
            "password": "BadPassword",
        },
    )
    assert resp.status_code == 401

    # 6th attempt with CORRECT password must now be rejected with 403 Forbidden
    resp = client.post(
        "/api/v1/auth/login",
        json={
            "tenant_id": setup_auth_tenant,
            "email": "lockout_test@test.com",
            "password": "CorrectPassword123",
        },
    )
    assert resp.status_code == 403
    assert "Account locked" in resp.json()["detail"]


def test_token_refresh(setup_auth_tenant):
    """Verify refresh token endpoint issues new access token."""
    login_resp = client.post(
        "/api/v1/auth/login",
        json={
            "tenant_id": setup_auth_tenant,
            "email": "auth_owner@test.com",
            "password": "ValidPass123!",
        },
    )
    assert login_resp.status_code == 200
    refresh_token = login_resp.json()["refresh_token"]

    refresh_resp = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_resp.status_code == 200
    assert "access_token" in refresh_resp.json()


def test_deactivated_user_cannot_login(setup_auth_tenant):
    """Verify deactivated user accounts cannot log in."""
    db = SessionLocal()
    try:
        set_session_tenant(db, setup_auth_tenant)
        user = (
            db.query(User)
            .filter(User.tenant_id == setup_auth_tenant, User.email == "deactivated@test.com")
            .first()
        )
        if not user:
            user = User(
                id=uuid.uuid4(),
                tenant_id=setup_auth_tenant,
                email="deactivated@test.com",
                hashed_password=get_password_hash("Password123"),
                full_name="Deactivated User",
                role=UserRole.VIEWER.value,
                is_active=False,
            )
            db.add(user)
            db.commit()
    finally:
        db.close()

    resp = client.post(
        "/api/v1/auth/login",
        json={
            "tenant_id": setup_auth_tenant,
            "email": "deactivated@test.com",
            "password": "Password123",
        },
    )
    assert resp.status_code == 403
    assert "deactivated" in resp.json()["detail"].lower()

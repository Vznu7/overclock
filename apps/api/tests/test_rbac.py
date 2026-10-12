import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal, set_session_tenant
from app.core.security import create_access_token, get_password_hash
from app.domains.auth.models import User, UserRole
from app.domains.tenants.models import Tenant, TenantSettings
from app.main import app

client = TestClient(app)


@pytest.fixture(scope="module")
def rbac_env():
    db = SessionLocal()
    tenant_id = "tenant-rbac-test"
    tokens: dict[str, str] = {}
    try:
        t = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not t:
            t = Tenant(id=tenant_id, name="RBAC Test Factory", cluster="Coimbatore", is_active=True)
            db.add(t)
            db.flush()
            set_session_tenant(db, tenant_id)
            s = TenantSettings(
                tenant_id=tenant_id, sewing_capacity_daily=1800, working_days=["Mon", "Tue"]
            )
            db.add(s)
            db.commit()

        set_session_tenant(db, tenant_id)

        # Create user for each of the 6 roles
        for role in UserRole:
            email = f"user_{role.value}@rbactest.com"
            set_session_tenant(db, tenant_id)
            user = db.query(User).filter(User.tenant_id == tenant_id, User.email == email).first()
            if not user:
                uid = uuid.uuid4()
                user = User(
                    id=uid,
                    tenant_id=tenant_id,
                    email=email,
                    hashed_password=get_password_hash("RbacSecret123"),
                    full_name=f"{role.value.capitalize()} User",
                    role=role.value,
                    is_active=True,
                )
                db.add(user)
                db.commit()
            else:
                uid = user.id

            token = create_access_token(
                subject=str(uid),
                tenant_id=tenant_id,
                role=role.value,
                extra_claims={"email": email},
            )
            tokens[role.value] = token

    finally:
        db.close()

    return {"tenant_id": tenant_id, "tokens": tokens}


def test_unauthenticated_request_rejected():
    """Prove unauthenticated requests to protected endpoints return 401 Unauthorized."""
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401
    assert "not provided" in resp.json()["detail"].lower()


def test_all_authenticated_roles_can_access_me(rbac_env):
    """Prove every valid role can access their own profile."""
    for role in UserRole:
        token = rbac_env["tokens"][role.value]
        resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["role"] == role.value


def test_user_creation_rbac(rbac_env):
    """Prove ONLY 'owner' role can create users. All other roles must receive 403 Forbidden."""
    payload = {
        "email": f"new_hire_{uuid.uuid4().hex[:6]}@rbactest.com",
        "password": "InitialPassword123!",
        "full_name": "New Team Member",
        "role": "supervisor",
    }

    # 1. Non-owner roles must fail with 403 Forbidden
    for role in [
        UserRole.MERCHANDISER,
        UserRole.PRODUCTION_MANAGER,
        UserRole.STORE_KEEPER,
        UserRole.SUPERVISOR,
        UserRole.VIEWER,
    ]:
        token = rbac_env["tokens"][role.value]
        resp = client.post(
            "/api/v1/users", json=payload, headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 403, f"Role {role.value} was erroneously allowed to create user!"
        assert "lacks permission" in resp.json()["detail"]

    # 2. Owner must succeed with 201 Created
    owner_token = rbac_env["tokens"][UserRole.OWNER.value]
    resp = client.post(
        "/api/v1/users", json=payload, headers={"Authorization": f"Bearer {owner_token}"}
    )
    assert resp.status_code == 201
    assert resp.json()["email"] == payload["email"]


def test_user_list_rbac(rbac_env):
    """Prove ONLY 'owner' and 'merchandiser' can list tenant users."""
    # Allowed roles
    for role in [UserRole.OWNER, UserRole.MERCHANDISER]:
        token = rbac_env["tokens"][role.value]
        resp = client.get("/api/v1/users", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    # Disallowed roles must receive 403 Forbidden
    for role in [
        UserRole.PRODUCTION_MANAGER,
        UserRole.STORE_KEEPER,
        UserRole.SUPERVISOR,
        UserRole.VIEWER,
    ]:
        token = rbac_env["tokens"][role.value]
        resp = client.get("/api/v1/users", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403, f"Role {role.value} was erroneously allowed to list users!"


def test_tenant_settings_update_rbac(rbac_env):
    """Prove ONLY 'owner' and 'merchandiser' can update tenant settings."""
    payload = {"sewing_capacity_daily": 2200}

    # Disallowed roles must receive 403 Forbidden
    for role in [
        UserRole.PRODUCTION_MANAGER,
        UserRole.STORE_KEEPER,
        UserRole.SUPERVISOR,
        UserRole.VIEWER,
    ]:
        token = rbac_env["tokens"][role.value]
        resp = client.patch(
            "/api/v1/tenants/current/settings",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403, (
            f"Role {role.value} was erroneously allowed to update settings!"
        )

    # Allowed role
    owner_token = rbac_env["tokens"][UserRole.OWNER.value]
    resp = client.patch(
        "/api/v1/tenants/current/settings",
        json=payload,
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["sewing_capacity_daily"] == 2200

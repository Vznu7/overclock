import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal, set_session_tenant
from app.core.security import create_access_token, get_password_hash
from app.domains.audit.models import AuditAction
from app.domains.auth.models import User, UserRole
from app.domains.tenants.models import Tenant, TenantSettings
from app.main import app

client = TestClient(app)


@pytest.fixture(scope="module")
def audit_fixture():
    db = SessionLocal()
    t1_id = "tenant-audit-a"
    t2_id = "tenant-audit-b"

    # Setup Tenant A
    t1 = db.query(Tenant).filter(Tenant.id == t1_id).first()
    if not t1:
        t1 = Tenant(id=t1_id, name="Audit Factory A", cluster="Tirupur", is_active=True)
        db.add(t1)
        db.flush()
        set_session_tenant(db, t1_id)
        s1 = TenantSettings(tenant_id=t1_id, sewing_capacity_daily=1000)
        db.add(s1)
        db.commit()

    # Setup Tenant B
    t2 = db.query(Tenant).filter(Tenant.id == t2_id).first()
    if not t2:
        t2 = Tenant(id=t2_id, name="Audit Factory B", cluster="Surat", is_active=True)
        db.add(t2)
        db.flush()
        set_session_tenant(db, t2_id)
        s2 = TenantSettings(tenant_id=t2_id, sewing_capacity_daily=2000)
        db.add(s2)
        db.commit()

    # Create Owner and Supervisor in Tenant A
    set_session_tenant(db, t1_id)
    u_owner_a = (
        db.query(User).filter(User.tenant_id == t1_id, User.email == "owner@audita.com").first()
    )
    if not u_owner_a:
        u_owner_a = User(
            id=uuid.uuid4(),
            tenant_id=t1_id,
            email="owner@audita.com",
            hashed_password=get_password_hash("Password123!"),
            full_name="Audit A Owner",
            role=UserRole.OWNER.value,
            is_active=True,
        )
        db.add(u_owner_a)
        db.commit()

    u_sup_a = db.query(User).filter(User.tenant_id == t1_id, User.email == "sup@audita.com").first()
    if not u_sup_a:
        u_sup_a = User(
            id=uuid.uuid4(),
            tenant_id=t1_id,
            email="sup@audita.com",
            hashed_password=get_password_hash("Password123!"),
            full_name="Audit A Supervisor",
            role=UserRole.SUPERVISOR.value,
            is_active=True,
        )
        db.add(u_sup_a)
        db.commit()

    # Create Owner in Tenant B
    set_session_tenant(db, t2_id)
    u_owner_b = (
        db.query(User).filter(User.tenant_id == t2_id, User.email == "owner@auditb.com").first()
    )
    if not u_owner_b:
        u_owner_b = User(
            id=uuid.uuid4(),
            tenant_id=t2_id,
            email="owner@auditb.com",
            hashed_password=get_password_hash("Password123!"),
            full_name="Audit B Owner",
            role=UserRole.OWNER.value,
            is_active=True,
        )
        db.add(u_owner_b)
        db.commit()

    token_owner_a = create_access_token(
        subject=str(u_owner_a.id),
        tenant_id=t1_id,
        role=UserRole.OWNER.value,
        extra_claims={"email": u_owner_a.email},
    )
    token_sup_a = create_access_token(
        subject=str(u_sup_a.id),
        tenant_id=t1_id,
        role=UserRole.SUPERVISOR.value,
        extra_claims={"email": u_sup_a.email},
    )
    token_owner_b = create_access_token(
        subject=str(u_owner_b.id),
        tenant_id=t2_id,
        role=UserRole.OWNER.value,
        extra_claims={"email": u_owner_b.email},
    )

    db.close()
    return {
        "tenant_a": t1_id,
        "tenant_b": t2_id,
        "token_owner_a": token_owner_a,
        "token_sup_a": token_sup_a,
        "token_owner_b": token_owner_b,
    }


def test_login_and_failed_login_audit_trail(audit_fixture):
    """Verify login success and login failure append immutable audit log entries."""
    # 1. Failed login
    resp_fail = client.post(
        "/api/v1/auth/login",
        json={
            "tenant_id": audit_fixture["tenant_a"],
            "email": "owner@audita.com",
            "password": "WrongPassword!",
        },
    )
    assert resp_fail.status_code == 401

    # 2. Successful login
    resp_success = client.post(
        "/api/v1/auth/login",
        json={
            "tenant_id": audit_fixture["tenant_a"],
            "email": "owner@audita.com",
            "password": "Password123!",
        },
    )
    assert resp_success.status_code == 200

    # 3. Query audit logs using Owner A token
    resp_logs = client.get(
        "/api/v1/audit-logs",
        headers={"Authorization": f"Bearer {audit_fixture['token_owner_a']}"},
    )
    assert resp_logs.status_code == 200
    logs = resp_logs.json()
    assert len(logs) >= 2

    actions = [entry["action"] for entry in logs]
    assert AuditAction.LOGIN_SUCCESS.value in actions
    assert AuditAction.LOGIN_FAILED.value in actions


def test_user_creation_audit_logging(audit_fixture):
    """Verify user creation writes an audit entry containing change metadata."""
    new_email = f"operator_{uuid.uuid4().hex[:6]}@audita.com"
    resp = client.post(
        "/api/v1/users",
        json={
            "email": new_email,
            "password": "ValidPassword123!",
            "full_name": "New Audit Operator",
            "role": "supervisor",
        },
        headers={"Authorization": f"Bearer {audit_fixture['token_owner_a']}"},
    )
    assert resp.status_code == 201

    resp_logs = client.get(
        "/api/v1/audit-logs?entity_type=user",
        headers={"Authorization": f"Bearer {audit_fixture['token_owner_a']}"},
    )
    assert resp_logs.status_code == 200
    user_logs = resp_logs.json()
    created_logs = [
        entry
        for entry in user_logs
        if entry["action"] == AuditAction.CREATE.value
        and entry.get("changes_json", {}).get("email") == new_email
    ]
    assert len(created_logs) == 1
    log_entry = created_logs[0]
    assert log_entry["tenant_id"] == audit_fixture["tenant_a"]
    assert log_entry["changes_json"]["role"] == "supervisor"


def test_tenant_settings_update_audit_logging(audit_fixture):
    """Verify settings modifications append UPDATE audit logs."""
    resp = client.patch(
        "/api/v1/tenants/current/settings",
        json={"sewing_capacity_daily": 3500},
        headers={"Authorization": f"Bearer {audit_fixture['token_owner_a']}"},
    )
    assert resp.status_code == 200

    resp_logs = client.get(
        "/api/v1/audit-logs?entity_type=tenant_settings",
        headers={"Authorization": f"Bearer {audit_fixture['token_owner_a']}"},
    )
    assert resp_logs.status_code == 200
    settings_logs = resp_logs.json()
    assert len(settings_logs) >= 1
    latest = settings_logs[0]
    assert latest["action"] == AuditAction.UPDATE.value
    assert latest["changes_json"]["sewing_capacity_daily"] == 3500


def test_audit_logs_cross_tenant_isolation_rls(audit_fixture):
    """Verify Tenant B cannot view any audit log entries belonging to Tenant A."""
    resp_b = client.get(
        "/api/v1/audit-logs",
        headers={"Authorization": f"Bearer {audit_fixture['token_owner_b']}"},
    )
    assert resp_b.status_code == 200
    logs_b = resp_b.json()
    for entry in logs_b:
        assert entry["tenant_id"] == audit_fixture["tenant_b"]
        assert entry["tenant_id"] != audit_fixture["tenant_a"]


def test_audit_logs_rbac_authorization(audit_fixture):
    """Verify only owner/viewer roles can read audit logs; supervisor is denied with 403."""
    resp = client.get(
        "/api/v1/audit-logs",
        headers={"Authorization": f"Bearer {audit_fixture['token_sup_a']}"},
    )
    assert resp.status_code == 403
    assert "lacks permission" in resp.json()["detail"]

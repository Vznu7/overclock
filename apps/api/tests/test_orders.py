import io
import uuid
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal, set_session_tenant
from app.core.security import create_access_token, get_password_hash
from app.domains.auth.models import User, UserRole
from app.domains.tenants.models import Tenant
from app.main import app

client = TestClient(app)


@pytest.fixture(scope="module")
def orders_fixture():
    db = SessionLocal()
    t_id = "tenant-orders-p3"
    other_t_id = "tenant-orders-other"

    # Setup tenant 1
    set_session_tenant(db, t_id)
    t = db.query(Tenant).filter(Tenant.id == t_id).first()
    if not t:
        t = Tenant(id=t_id, name="Phase 3 Test Factory", cluster="Tirupur", is_active=True)
        db.add(t)
        db.commit()

    # Setup other tenant
    set_session_tenant(db, other_t_id)
    other_t = db.query(Tenant).filter(Tenant.id == other_t_id).first()
    if not other_t:
        other_t = Tenant(id=other_t_id, name="Other Test Factory", cluster="Surat", is_active=True)
        db.add(other_t)
        db.commit()

    # Create users
    set_session_tenant(db, t_id)
    u_merch = (
        db.query(User).filter(User.tenant_id == t_id, User.email == "merch@p3test.com").first()
    )
    if not u_merch:
        u_merch = User(
            id=uuid.uuid4(),
            tenant_id=t_id,
            email="merch@p3test.com",
            hashed_password=get_password_hash("Secret123!"),
            full_name="P3 Merchandiser",
            role=UserRole.MERCHANDISER.value,
            is_active=True,
        )
        db.add(u_merch)
        db.commit()

    u_prod = db.query(User).filter(User.tenant_id == t_id, User.email == "prod@p3test.com").first()
    if not u_prod:
        u_prod = User(
            id=uuid.uuid4(),
            tenant_id=t_id,
            email="prod@p3test.com",
            hashed_password=get_password_hash("Secret123!"),
            full_name="P3 Production Mgr",
            role=UserRole.PRODUCTION_MANAGER.value,
            is_active=True,
        )
        db.add(u_prod)
        db.commit()

    u_viewer = (
        db.query(User).filter(User.tenant_id == t_id, User.email == "viewer@p3test.com").first()
    )
    if not u_viewer:
        u_viewer = User(
            id=uuid.uuid4(),
            tenant_id=t_id,
            email="viewer@p3test.com",
            hashed_password=get_password_hash("Secret123!"),
            full_name="P3 Viewer",
            role=UserRole.VIEWER.value,
            is_active=True,
        )
        db.add(u_viewer)
        db.commit()

    # User in other tenant
    set_session_tenant(db, other_t_id)
    u_other = (
        db.query(User)
        .filter(User.tenant_id == other_t_id, User.email == "other@othertest.com")
        .first()
    )
    if not u_other:
        u_other = User(
            id=uuid.uuid4(),
            tenant_id=other_t_id,
            email="other@othertest.com",
            hashed_password=get_password_hash("Secret123!"),
            full_name="Other Tenant Merch",
            role=UserRole.MERCHANDISER.value,
            is_active=True,
        )
        db.add(u_other)
        db.commit()

    token_merch = create_access_token(
        subject=str(u_merch.id),
        tenant_id=t_id,
        role=UserRole.MERCHANDISER.value,
        extra_claims={"email": u_merch.email},
    )
    token_prod = create_access_token(
        subject=str(u_prod.id),
        tenant_id=t_id,
        role=UserRole.PRODUCTION_MANAGER.value,
        extra_claims={"email": u_prod.email},
    )
    token_viewer = create_access_token(
        subject=str(u_viewer.id),
        tenant_id=t_id,
        role=UserRole.VIEWER.value,
        extra_claims={"email": u_viewer.email},
    )
    token_other = create_access_token(
        subject=str(u_other.id),
        tenant_id=other_t_id,
        role=UserRole.MERCHANDISER.value,
        extra_claims={"email": u_other.email},
    )

    db.close()
    return {
        "tenant_id": t_id,
        "other_tenant_id": other_t_id,
        "token_merch": token_merch,
        "token_prod": token_prod,
        "token_viewer": token_viewer,
        "token_other": token_other,
    }


def test_buyers_and_styles_creation_and_rbac(orders_fixture):
    """Test creating Buyer and Style with RBAC enforcement."""
    token_merch = orders_fixture["token_merch"]
    token_viewer = orders_fixture["token_viewer"]

    # 1. Viewer cannot create buyer (403)
    resp_v = client.post(
        "/api/v1/buyers",
        json={"name": "Next Sourcing UK", "code": "NEXT", "country": "United Kingdom"},
        headers={"Authorization": f"Bearer {token_viewer}"},
    )
    assert resp_v.status_code == 403

    # 2. Merchandiser creates buyer (201)
    resp_b = client.post(
        "/api/v1/buyers",
        json={"name": "Next Sourcing UK", "code": "NEXT", "country": "United Kingdom"},
        headers={"Authorization": f"Bearer {token_merch}"},
    )
    assert resp_b.status_code == 201
    buyer = resp_b.json()
    assert buyer["code"] == "NEXT"

    # 3. Create Style under Buyer
    resp_s = client.post(
        "/api/v1/styles",
        json={
            "buyer_id": buyer["id"],
            "style_number": "ST-TEE-001",
            "style_name": "Organic Cotton Crew Tee",
            "garment_type": "Crew Neck Tee",
            "sam": 14.50,
            "target_efficiency": 65.00,
        },
        headers={"Authorization": f"Bearer {token_merch}"},
    )
    assert resp_s.status_code == 201
    style = resp_s.json()
    assert style["style_number"] == "ST-TEE-001"


def test_order_creation_lines_and_milestones(orders_fixture):
    """Test creating an Order with color/size lines and milestones."""
    token_merch = orders_fixture["token_merch"]

    # Fetch buyer and style
    resp_b = client.get("/api/v1/buyers", headers={"Authorization": f"Bearer {token_merch}"})
    buyer = resp_b.json()[0]

    resp_s = client.get("/api/v1/styles", headers={"Authorization": f"Bearer {token_merch}"})
    style = resp_s.json()[0]

    order_payload = {
        "buyer_id": buyer["id"],
        "style_id": style["id"],
        "order_number": f"PO-{uuid.uuid4().hex[:6].upper()}",
        "total_quantity": 3000,
        "unit_price": 420.00,
        "currency": "INR",
        "ex_factory_date": str(date.today() + timedelta(days=35)),
        "planned_sewing_start": str(date.today() + timedelta(days=20)),
        "status": "CONFIRMED",
        "lines": [
            {"color": "Navy Blue", "size": "M", "quantity": 1500},
            {"color": "Navy Blue", "size": "L", "quantity": 1500},
        ],
    }

    resp = client.post(
        "/api/v1/orders", json=order_payload, headers={"Authorization": f"Bearer {token_merch}"}
    )
    assert resp.status_code == 201
    created_order = resp.json()
    assert created_order["order_number"] == order_payload["order_number"]
    assert created_order["total_quantity"] == 3000
    assert len(created_order["lines"]) == 2

    # Get single order detail
    resp_detail = client.get(
        f"/api/v1/orders/{created_order['id']}",
        headers={"Authorization": f"Bearer {token_merch}"},
    )
    assert resp_detail.status_code == 200
    assert resp_detail.json()["buyer"]["name"] == buyer["name"]


def test_order_cross_tenant_isolation_rls(orders_fixture):
    """Prove Tenant B cannot read or modify Tenant A's orders."""
    token_merch = orders_fixture["token_merch"]
    token_other = orders_fixture["token_other"]

    # 1. List orders in Tenant A
    resp_a = client.get("/api/v1/orders", headers={"Authorization": f"Bearer {token_merch}"})
    assert resp_a.status_code == 200
    orders_a = resp_a.json()
    assert len(orders_a) >= 1
    target_order_id = orders_a[0]["id"]

    # 2. Tenant B lists orders -> must NOT see Tenant A's orders
    resp_b = client.get("/api/v1/orders", headers={"Authorization": f"Bearer {token_other}"})
    assert resp_b.status_code == 200
    orders_b = resp_b.json()
    for o in orders_b:
        assert o["id"] != target_order_id

    # 3. Tenant B directly queries Tenant A's order by UUID -> 404 Not Found (RLS hidden)
    resp_direct = client.get(
        f"/api/v1/orders/{target_order_id}",
        headers={"Authorization": f"Bearer {token_other}"},
    )
    assert resp_direct.status_code == 404


def test_csv_import_and_export(orders_fixture):
    """Test importing orders via CSV and downloading CSV export."""
    token_merch = orders_fixture["token_merch"]
    uid = uuid.uuid4().hex[:6].upper()
    po1 = f"PO-CSV-{uid}-1"
    po2 = f"PO-CSV-{uid}-2"

    csv_data = f"""Order Number,Buyer,Style,Quantity,Unit Price,Ex-Factory Date,Sewing Start Date,Color,Size
{po1},H&M Global,HM-TEE-SLIM,5000,380.00,28-11-2026,14-11-2026,Black,L
{po2},Marks & Spencer,MS-POLO-PIQUE,2400,620.00,15-12-2026,01-12-2026,White,M
"""
    file_bytes = io.BytesIO(csv_data.encode("utf-8"))

    # 1. Upload CSV
    resp_import = client.post(
        "/api/v1/orders/import/csv",
        files={"file": ("orders.csv", file_bytes, "text/csv")},
        headers={"Authorization": f"Bearer {token_merch}"},
    )
    assert resp_import.status_code == 200
    summary = resp_import.json()
    assert summary["total_rows"] == 2
    assert summary["successful_rows"] == 2
    assert summary["created_orders"] >= 2
    assert summary["failed_rows"] == 0

    # 2. Export CSV
    resp_export = client.get(
        "/api/v1/orders/export/csv",
        headers={"Authorization": f"Bearer {token_merch}"},
    )
    assert resp_export.status_code == 200
    assert "text/csv" in resp_export.headers["content-type"]
    exported_text = resp_export.text
    assert "Order Number,Buyer,Style Number" in exported_text
    assert "PO-CSV-001" in exported_text
    assert "PO-CSV-002" in exported_text


def test_csv_import_validation_and_error_reporting(orders_fixture):
    """Test CSV validation with missing fields and bad date formats."""
    token_merch = orders_fixture["token_merch"]

    bad_csv = """Order Number,Buyer,Style,Quantity,Ex-Factory Date
PO-BAD-001,,ST-001,1000,20-11-2026
,Buyer A,ST-002,1000,20-11-2026
PO-BAD-003,Buyer B,ST-003,not_a_number,20-11-2026
PO-BAD-004,Buyer C,ST-004,1000,invalid_date_format
"""
    file_bytes = io.BytesIO(bad_csv.encode("utf-8"))

    resp = client.post(
        "/api/v1/orders/import/csv?strict=true",
        files={"file": ("bad_orders.csv", file_bytes, "text/csv")},
        headers={"Authorization": f"Bearer {token_merch}"},
    )
    assert resp.status_code == 200
    summary = resp.json()
    assert summary["successful_rows"] == 0
    assert summary["failed_rows"] == 4
    assert len(summary["errors"]) == 4

    # Check that clear row numbers and error fields are returned
    err_fields = [e["field"] for e in summary["errors"]]
    assert "buyer" in err_fields
    assert "order_number" in err_fields
    assert "quantity" in err_fields
    assert "ex_factory_date" in err_fields


def test_po_extraction_endpoint(orders_fixture):
    """Test extracting structured draft order via API endpoint."""
    token_merch = orders_fixture["token_merch"]

    # 1. Preset sample extraction
    resp = client.post(
        "/api/v1/orders/extract-po?sample_id=sample_decathlon",
        headers={"Authorization": f"Bearer {token_merch}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["order_number"]["value"] == "DEC-PO-2026-9041"
    assert data["total_quantity"]["value"] == 12000
    assert data["currency"]["value"] == "USD"
    assert len(data["lines"]) == 4
    assert data["order_number"]["confidence"] >= 0.95


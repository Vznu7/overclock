import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal, set_session_tenant
from app.core.security import create_access_token, get_password_hash
from app.domains.auth.models import User, UserRole
from app.domains.orders.models import Buyer, Style
from app.domains.tenants.models import Tenant
from app.main import app

client = TestClient(app)


@pytest.fixture(scope="module")
def materials_fixture():
    db = SessionLocal()
    t_id = "tenant-mat-p4"
    other_t_id = "tenant-mat-other"

    # Setup tenant 1
    set_session_tenant(db, t_id)
    t = db.query(Tenant).filter(Tenant.id == t_id).first()
    if not t:
        t = Tenant(id=t_id, name="Phase 4 Materials Factory", cluster="Tirupur", is_active=True)
        db.add(t)
        db.commit()

    # Setup tenant 2
    set_session_tenant(db, other_t_id)
    other_t = db.query(Tenant).filter(Tenant.id == other_t_id).first()
    if not other_t:
        other_t = Tenant(
            id=other_t_id, name="Other Materials Factory", cluster="Surat", is_active=True
        )
        db.add(other_t)
        db.commit()

    # Create users
    set_session_tenant(db, t_id)
    u_store = db.query(User).filter(User.tenant_id == t_id, User.email == "store@p4mat.com").first()
    if not u_store:
        u_store = User(
            id=uuid.uuid4(),
            tenant_id=t_id,
            email="store@p4mat.com",
            hashed_password=get_password_hash("Secret123!"),
            full_name="P4 Store Keeper",
            role=UserRole.STORE_KEEPER,
            is_active=True,
        )
        db.add(u_store)
        db.commit()
        db.refresh(u_store)

    u_merch = db.query(User).filter(User.tenant_id == t_id, User.email == "merch@p4mat.com").first()
    if not u_merch:
        u_merch = User(
            id=uuid.uuid4(),
            tenant_id=t_id,
            email="merch@p4mat.com",
            hashed_password=get_password_hash("Secret123!"),
            full_name="P4 Merchandiser",
            role=UserRole.MERCHANDISER,
            is_active=True,
        )
        db.add(u_merch)
        db.commit()
        db.refresh(u_merch)

    set_session_tenant(db, other_t_id)
    u_other = (
        db.query(User).filter(User.tenant_id == other_t_id, User.email == "other@p4mat.com").first()
    )
    if not u_other:
        u_other = User(
            id=uuid.uuid4(),
            tenant_id=other_t_id,
            email="other@p4mat.com",
            hashed_password=get_password_hash("Secret123!"),
            full_name="Other Store Keeper",
            role=UserRole.STORE_KEEPER,
            is_active=True,
        )
        db.add(u_other)
        db.commit()
        db.refresh(u_other)

    # Style and buyer for tenant 1
    set_session_tenant(db, t_id)
    buyer = (
        db.query(Buyer).filter(Buyer.tenant_id == t_id, Buyer.name == "Global Threads UK").first()
    )
    if not buyer:
        buyer = Buyer(
            id=uuid.uuid4(),
            tenant_id=t_id,
            name="Global Threads UK",
            code="GT-UK",
            country="United Kingdom",
            payment_terms="Net 45",
        )
        db.add(buyer)
        db.commit()
        db.refresh(buyer)

    style = (
        db.query(Style).filter(Style.tenant_id == t_id, Style.style_number == "STY-P4-TEE").first()
    )
    if not style:
        style = Style(
            id=uuid.uuid4(),
            tenant_id=t_id,
            buyer_id=buyer.id,
            style_number="STY-P4-TEE",
            style_name="Organic Bio Cotton Crew Tee",
            garment_type="T-Shirt",
            sam=Decimal("12.50"),
        )
        db.add(style)
        db.commit()
        db.refresh(style)

    db.close()

    role_store = u_store.role.value if hasattr(u_store.role, "value") else str(u_store.role)
    role_merch = u_merch.role.value if hasattr(u_merch.role, "value") else str(u_merch.role)
    role_other = u_other.role.value if hasattr(u_other.role, "value") else str(u_other.role)

    token_store = create_access_token(str(u_store.id), t_id, role_store)
    token_merch = create_access_token(str(u_merch.id), t_id, role_merch)
    token_other = create_access_token(str(u_other.id), other_t_id, role_other)

    return {
        "tenant_id": t_id,
        "other_tenant_id": other_t_id,
        "token_store": token_store,
        "token_merch": token_merch,
        "token_other": token_other,
        "style_id": str(style.id),
        "buyer_id": str(buyer.id),
    }


def test_materials_crud_and_stock_balance(materials_fixture):
    token = materials_fixture["token_store"]
    headers = {"Authorization": f"Bearer {token}"}

    unique_code = f"FAB-P4-{uuid.uuid4().hex[:6]}"
    # 1. Create material
    resp = client.post(
        "/api/v1/materials",
        headers=headers,
        json={
            "code": unique_code,
            "name": "100% Combed Cotton Single Jersey 180 GSM",
            "category": "FABRIC",
            "unit_of_measure": "KG",
            "minimum_stock_level": 200.0,
            "unit_cost": 340.0,
            "currency": "INR",
        },
    )
    assert resp.status_code == 201, resp.text
    mat = resp.json()
    mat_id = mat["id"]
    assert mat["code"] == unique_code
    assert float(mat["current_stock"]) == 0.0

    # 2. Receive stock via GRN
    resp_grn = client.post(
        "/api/v1/stock/receive",
        headers=headers,
        json={
            "material_id": mat_id,
            "quantity": 500.0,
            "unit_cost": 340.0,
            "notes": "Initial inward batch from mill",
        },
    )
    assert resp_grn.status_code == 201, resp_grn.text
    entry = resp_grn.json()
    assert float(entry["quantity"]) == 500.0

    # 3. Verify stock updated
    resp_get = client.get(f"/api/v1/materials/{mat_id}", headers=headers)
    assert resp_get.status_code == 200
    assert float(resp_get.json()["current_stock"]) == 500.0

    # 4. Issue stock to cutting
    resp_issue = client.post(
        "/api/v1/stock/issue",
        headers=headers,
        json={
            "material_id": mat_id,
            "quantity": 120.0,
            "notes": "Issued to Cutting Table 1",
        },
    )
    assert resp_issue.status_code == 201, resp_issue.text
    assert float(resp_issue.json()["quantity"]) == -120.0

    # 5. Verify net stock balance (500 - 120 = 380)
    resp_get2 = client.get(f"/api/v1/materials/{mat_id}", headers=headers)
    assert resp_get2.status_code == 200
    assert float(resp_get2.json()["current_stock"]) == 380.0


def test_style_bom_and_gross_requirement(materials_fixture):
    token = materials_fixture["token_merch"]
    headers = {"Authorization": f"Bearer {token}"}
    style_id = materials_fixture["style_id"]

    # Create fabric and rib materials
    resp_fab = client.post(
        "/api/v1/materials",
        headers=headers,
        json={
            "code": f"BOM-FAB-{uuid.uuid4().hex[:6]}",
            "name": "Single Jersey 160 GSM",
            "category": "FABRIC",
            "unit_of_measure": "KG",
            "unit_cost": 320.0,
        },
    )
    assert resp_fab.status_code == 201
    fab_id = resp_fab.json()["id"]

    resp_rib = client.post(
        "/api/v1/materials",
        headers=headers,
        json={
            "code": f"BOM-RIB-{uuid.uuid4().hex[:6]}",
            "name": "1x1 Cotton Spandex Rib",
            "category": "FABRIC",
            "unit_of_measure": "KG",
            "unit_cost": 360.0,
        },
    )
    assert resp_rib.status_code == 201
    rib_id = resp_rib.json()["id"]

    # Add BOM lines
    resp_b1 = client.post(
        f"/api/v1/styles/{style_id}/bom",
        headers=headers,
        json={
            "material_id": fab_id,
            "component_name": "Body Fabric",
            "consumption_per_piece": 0.2200,
            "wastage_percentage": 5.0,
        },
    )
    assert resp_b1.status_code == 201

    resp_b2 = client.post(
        f"/api/v1/styles/{style_id}/bom",
        headers=headers,
        json={
            "material_id": rib_id,
            "component_name": "Neck Rib",
            "consumption_per_piece": 0.0250,
            "wastage_percentage": 4.0,
        },
    )
    assert resp_b2.status_code == 201

    # Calculate gross requirement for 1,000 pieces
    # Body Fabric: 1000 * 0.2200 * 1.05 = 231.000 KG
    # Neck Rib: 1000 * 0.0250 * 1.04 = 26.000 KG
    resp_calc = client.get(
        f"/api/v1/styles/{style_id}/bom/calculate?order_qty=1000",
        headers=headers,
    )
    assert resp_calc.status_code == 200
    calc_items = resp_calc.json()
    assert len(calc_items) >= 2

    body_item = next(item for item in calc_items if item["component_name"] == "Body Fabric")
    assert float(body_item["gross_requirement"]) == 231.0
    assert float(body_item["deficit"]) == 231.0  # Currently 0 in stock


def test_supplier_and_po_grn_workflow(materials_fixture):
    token_merch = materials_fixture["token_merch"]
    token_store = materials_fixture["token_store"]

    # 1. Register supplier
    resp_sup = client.post(
        "/api/v1/suppliers",
        headers={"Authorization": f"Bearer {token_merch}"},
        json={
            "name": f"Lakshmi Spinning Mills-{uuid.uuid4().hex[:4]}",
            "code": f"LSM-{uuid.uuid4().hex[:4]}",
            "category": "FABRIC_MILL",
            "contact_email": "sales@lakshmispinning.com",
            "lead_time_days": 12,
        },
    )
    assert resp_sup.status_code == 201
    sup_id = resp_sup.json()["id"]

    # Create a trim material
    resp_trim = client.post(
        "/api/v1/materials",
        headers={"Authorization": f"Bearer {token_merch}"},
        json={
            "code": f"TRM-BTN-{uuid.uuid4().hex[:6]}",
            "name": "Natural Horn Buttons 18L",
            "category": "TRIM",
            "unit_of_measure": "PIECE",
            "unit_cost": 1.25,
        },
    )
    trim_id = resp_trim.json()["id"]

    # 2. Place supplier PO
    po_num = f"SPO-{uuid.uuid4().hex[:6]}"
    resp_po = client.post(
        "/api/v1/supplier-pos",
        headers={"Authorization": f"Bearer {token_merch}"},
        json={
            "po_number": po_num,
            "supplier_id": sup_id,
            "material_id": trim_id,
            "quantity_ordered": 10000.0,
            "unit_price": 1.25,
            "expected_delivery_date": (date.today() + timedelta(days=10)).isoformat(),
        },
    )
    assert resp_po.status_code == 201
    po = resp_po.json()
    po_id = po["id"]
    assert po["status"] == "PLACED"

    # 3. Store Keeper receives partial goods (4,000 pcs)
    resp_grn1 = client.post(
        "/api/v1/stock/receive",
        headers={"Authorization": f"Bearer {token_store}"},
        json={
            "material_id": trim_id,
            "supplier_po_id": po_id,
            "quantity": 4000.0,
            "unit_cost": 1.25,
            "notes": "First partial shipment",
        },
    )
    assert resp_grn1.status_code == 201

    # Check PO status is PARTIAL_RECEIVED
    pos = client.get(
        "/api/v1/supplier-pos", headers={"Authorization": f"Bearer {token_store}"}
    ).json()
    po_updated = next(p for p in pos if p["id"] == po_id)
    assert po_updated["status"] == "PARTIAL_RECEIVED"
    assert float(po_updated["quantity_received"]) == 4000.0

    # 4. Receive remaining 6,000 pcs -> COMPLETED
    resp_grn2 = client.post(
        "/api/v1/stock/receive",
        headers={"Authorization": f"Bearer {token_store}"},
        json={
            "material_id": trim_id,
            "supplier_po_id": po_id,
            "quantity": 6000.0,
            "unit_cost": 1.25,
            "notes": "Final balance shipment",
        },
    )
    assert resp_grn2.status_code == 201

    pos2 = client.get(
        "/api/v1/supplier-pos", headers={"Authorization": f"Bearer {token_store}"}
    ).json()
    po_completed = next(p for p in pos2 if p["id"] == po_id)
    assert po_completed["status"] == "COMPLETED"
    assert float(po_completed["quantity_received"]) == 10000.0


def test_tenant_rls_isolation_on_materials_and_ledger(materials_fixture):
    token_tenant1 = materials_fixture["token_store"]
    token_tenant2 = materials_fixture["token_other"]

    # Tenant 1 creates private material
    secret_code = f"SECRET-FAB-{uuid.uuid4().hex[:6]}"
    resp1 = client.post(
        "/api/v1/materials",
        headers={"Authorization": f"Bearer {token_tenant1}"},
        json={
            "code": secret_code,
            "name": "Secret Egyptian Giza Cotton",
            "category": "FABRIC",
            "unit_of_measure": "KG",
            "unit_cost": 850.0,
        },
    )
    assert resp1.status_code == 201
    mat1_id = resp1.json()["id"]

    # Inward stock for tenant 1
    client.post(
        "/api/v1/stock/receive",
        headers={"Authorization": f"Bearer {token_tenant1}"},
        json={
            "material_id": mat1_id,
            "quantity": 750.0,
            "unit_cost": 850.0,
        },
    )

    # Tenant 2 queries materials catalog
    resp_t2_mats = client.get(
        "/api/v1/materials",
        headers={"Authorization": f"Bearer {token_tenant2}"},
    )
    assert resp_t2_mats.status_code == 200
    t2_codes = [m["code"] for m in resp_t2_mats.json()]
    assert secret_code not in t2_codes

    # Tenant 2 cannot access material directly by ID
    resp_t2_direct = client.get(
        f"/api/v1/materials/{mat1_id}",
        headers={"Authorization": f"Bearer {token_tenant2}"},
    )
    assert resp_t2_direct.status_code == 404

    # Tenant 2 queries stock ledger
    resp_t2_ledger = client.get(
        "/api/v1/stock/ledger",
        headers={"Authorization": f"Bearer {token_tenant2}"},
    )
    assert resp_t2_ledger.status_code == 200
    t2_ledger_mat_ids = [e["material_id"] for e in resp_t2_ledger.json()]
    assert mat1_id not in t2_ledger_mat_ids


def test_order_material_risks_endpoint(materials_fixture):
    token = materials_fixture["token_merch"]
    resp = client.get(
        "/api/v1/risk/materials",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)

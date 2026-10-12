import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal, set_session_tenant
from app.core.security import create_access_token, get_password_hash
from app.domains.auth.models import User, UserRole
from app.domains.jobwork.models import JobworkProcessor
from app.domains.orders.models import Buyer, Order, Style
from app.domains.tenants.models import Tenant
from app.main import app

client = TestClient(app)


@pytest.fixture(scope="module")
def jobwork_fixture():
    db = SessionLocal()
    t_id = "tenant-jw-test"
    other_t_id = "tenant-jw-other"

    # Setup tenant 1
    set_session_tenant(db, t_id)
    t = db.query(Tenant).filter(Tenant.id == t_id).first()
    if not t:
        t = Tenant(id=t_id, name="Jobwork Test Mill", cluster="Tirupur", is_active=True)
        db.add(t)
        db.commit()

    # Setup tenant 2
    set_session_tenant(db, other_t_id)
    other_t = db.query(Tenant).filter(Tenant.id == other_t_id).first()
    if not other_t:
        other_t = Tenant(
            id=other_t_id, name="Other Jobwork Mill", cluster="Surat", is_active=True
        )
        db.add(other_t)
        db.commit()

    # Create manager and viewer users
    set_session_tenant(db, t_id)
    u_manager = db.query(User).filter(User.tenant_id == t_id, User.email == "pm@jwtest.com").first()
    if not u_manager:
        u_manager = User(
            id=uuid.uuid4(),
            tenant_id=t_id,
            email="pm@jwtest.com",
            hashed_password=get_password_hash("Secret123!"),
            full_name="JW Manager",
            role=UserRole.PRODUCTION_MANAGER,
            is_active=True,
        )
        db.add(u_manager)
        db.commit()
        db.refresh(u_manager)

    u_viewer = db.query(User).filter(User.tenant_id == t_id, User.email == "viewer@jwtest.com").first()
    if not u_viewer:
        u_viewer = User(
            id=uuid.uuid4(),
            tenant_id=t_id,
            email="viewer@jwtest.com",
            hashed_password=get_password_hash("Secret123!"),
            full_name="JW Viewer",
            role=UserRole.VIEWER,
            is_active=True,
        )
        db.add(u_viewer)
        db.commit()
        db.refresh(u_viewer)

    # Create Buyer, Style & Order for tenant 1
    buyer = db.query(Buyer).filter(Buyer.tenant_id == t_id, Buyer.code == "JW-BUYER").first()
    if not buyer:
        buyer = Buyer(
            id=uuid.uuid4(),
            tenant_id=t_id,
            name="JW Test Buyer",
            code="JW-BUYER",
            country="France",
        )
        db.add(buyer)
        db.commit()
        db.refresh(buyer)

    style = db.query(Style).filter(Style.tenant_id == t_id, Style.style_number == "JW-STYLE").first()
    if not style:
        style = Style(
            id=uuid.uuid4(),
            tenant_id=t_id,
            buyer_id=buyer.id,
            style_number="JW-STYLE",
            style_name="JW Bio Wash Tee",
            garment_type="T-Shirt",
            sam=Decimal("8.50"),
            target_efficiency=Decimal("70.0"),
        )
        db.add(style)
        db.commit()
        db.refresh(style)

    ord_num = f"ORD-JW-{uuid.uuid4().hex[:6].upper()}"
    order = Order(
        id=uuid.uuid4(),
        tenant_id=t_id,
        order_number=ord_num,
        buyer_id=buyer.id,
        style_id=style.id,
        status="IN_PRODUCTION",
        total_quantity=2000,
        currency="EUR",
        unit_price=Decimal("6.00"),
        planned_sewing_start=date.today() - timedelta(days=10),
        ex_factory_date=date.today() + timedelta(days=15),
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    # Processor in other tenant for isolation test
    set_session_tenant(db, other_t_id)
    other_proc = JobworkProcessor(
        id=uuid.uuid4(),
        tenant_id=other_t_id,
        name="Secret Dyeing Unit",
        process_type="DYEING",
        is_active=True,
    )
    db.add(other_proc)
    db.commit()

    db.close()

    manager_token = create_access_token(str(u_manager.id), t_id, str(u_manager.role))
    viewer_token = create_access_token(str(u_viewer.id), t_id, str(u_viewer.role))

    return {
        "tenant_id": t_id,
        "other_tenant_id": other_t_id,
        "manager_token": manager_token,
        "viewer_token": viewer_token,
        "order_id": str(order.id),
        "order_number": ord_num,
        "other_proc_id": str(other_proc.id),
    }


def test_create_and_list_processor(jobwork_fixture):
    headers = {"Authorization": f"Bearer {jobwork_fixture['manager_token']}"}

    # Create processor
    proc_name = f"Sri Krishna Dyeing {uuid.uuid4().hex[:4]}"
    res = client.post(
        "/api/v1/jobwork/processors",
        headers=headers,
        json={
            "name": proc_name,
            "process_type": "DYEING",
            "contact_person": "Murugan",
            "phone": "+91-9842100000",
            "address": "SIPCOT Industrial Complex, Perundurai",
            "is_active": True,
        },
    )
    assert res.status_code == 201
    proc_data = res.json()
    assert proc_data["name"] == proc_name
    assert proc_data["process_type"] == "DYEING"

    # List processors: should contain the created one, but NEVER the other tenant's processor
    list_res = client.get("/api/v1/jobwork/processors", headers=headers)
    assert list_res.status_code == 200
    processors = list_res.json()
    proc_ids = [p["id"] for p in processors]
    assert proc_data["id"] in proc_ids
    assert jobwork_fixture["other_proc_id"] not in proc_ids


def test_issue_and_receive_challan_with_loss_math(jobwork_fixture):
    headers = {"Authorization": f"Bearer {jobwork_fixture['manager_token']}"}

    # 1. Create a processor first
    p_res = client.post(
        "/api/v1/jobwork/processors",
        headers=headers,
        json={
            "name": f"Textile Printers {uuid.uuid4().hex[:4]}",
            "process_type": "PRINTING",
        },
    )
    assert p_res.status_code == 201
    proc_id = p_res.json()["id"]

    # 2. Issue outward challan
    challan_no = f"DC-OUT-{uuid.uuid4().hex[:6].upper()}"
    issue_payload = {
        "challan_number": challan_no,
        "challan_type": "OUTWARD_ISSUE",
        "processor_id": proc_id,
        "order_id": jobwork_fixture["order_id"],
        "process_name": "Chest Rotary Print",
        "material_description": "Single Jersey 160 GSM Combed Cotton",
        "issued_qty": "2000.000",
        "issued_weight_kg": "320.000",
        "expected_return_date": (date.today() + timedelta(days=3)).isoformat(),
        "notes": "Color spec Pantone 19-4052 Classic Blue",
    }
    c_res = client.post("/api/v1/jobwork/challans", headers=headers, json=issue_payload)
    assert c_res.status_code == 201
    c_data = c_res.json()
    challan_id = c_data["id"]
    assert c_data["status"] == "ISSUED"
    assert Decimal(str(c_data["issued_weight_kg"])) == Decimal("320.000")

    # 3. Inward receipt with excessive weight loss (>3.5%)
    # Issued: 320.0 kg. Received: 300.0 kg. Loss: 20.0 kg = 6.25% (> 3.5% threshold)
    rec_payload = {
        "received_qty": "1980.000",
        "received_weight_kg": "300.000",
        "actual_return_date": date.today().isoformat(),
        "notes": "Process shrinkage and edge trimming",
    }
    r_res = client.post(
        f"/api/v1/jobwork/challans/{challan_id}/receive",
        headers=headers,
        json=rec_payload,
    )
    assert r_res.status_code == 200
    rec_data = r_res.json()
    assert rec_data["status"] == "COMPLETED"
    assert Decimal(str(rec_data["received_weight_kg"])) == Decimal("300.000")
    assert Decimal(str(rec_data["weight_loss_kg"])) == Decimal("20.000")
    assert Decimal(str(rec_data["weight_loss_pct"])) == Decimal("6.25")
    assert rec_data["is_loss_anomaly"] is True


def test_jobwork_risk_rule_r4(jobwork_fixture):
    headers = {"Authorization": f"Bearer {jobwork_fixture['manager_token']}"}

    # Evaluate jobwork risks for tenant
    risk_res = client.get("/api/v1/risk/jobwork", headers=headers)
    assert risk_res.status_code == 200
    risks = risk_res.json()
    assert len(risks) >= 1
    # Check that rule is R4
    order_risk = next(r for r in risks if r["order_id"] == jobwork_fixture["order_id"])
    assert order_risk["rule"] == "R4"
    # Because we generated a 6.25% loss anomaly in the previous test, it triggers
    assert order_risk["triggered"] is True
    assert len(order_risk["evidence"].get("loss_anomalies", [])) >= 1


def test_jobwork_rbac_denies_viewer(jobwork_fixture):
    viewer_headers = {"Authorization": f"Bearer {jobwork_fixture['viewer_token']}"}

    # Viewer attempting to create processor should be 403 Forbidden
    res = client.post(
        "/api/v1/jobwork/processors",
        headers=viewer_headers,
        json={"name": "Hacked Unit", "process_type": "DYEING"},
    )
    assert res.status_code == 403

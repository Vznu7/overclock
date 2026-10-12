import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal, set_session_tenant
from app.core.security import create_access_token, get_password_hash
from app.domains.auth.models import User, UserRole
from app.domains.orders.models import Buyer, Order, Style
from app.domains.production.models import ProductionLine
from app.domains.tenants.models import Tenant
from app.main import app

client = TestClient(app)


@pytest.fixture(scope="module")
def prod_fixture():
    db = SessionLocal()
    t_id = "tenant-prod-p5"
    other_t_id = "tenant-prod-other"

    # Setup tenant 1
    set_session_tenant(db, t_id)
    t = db.query(Tenant).filter(Tenant.id == t_id).first()
    if not t:
        t = Tenant(id=t_id, name="Phase 5 Production Factory", cluster="Tirupur", is_active=True)
        db.add(t)
        db.commit()

    # Setup tenant 2
    set_session_tenant(db, other_t_id)
    other_t = db.query(Tenant).filter(Tenant.id == other_t_id).first()
    if not other_t:
        other_t = Tenant(
            id=other_t_id, name="Other Production Factory", cluster="Ludhiana", is_active=True
        )
        db.add(other_t)
        db.commit()

    # Create users in tenant 1
    set_session_tenant(db, t_id)
    u_manager = db.query(User).filter(User.tenant_id == t_id, User.email == "pm@p5prod.com").first()
    if not u_manager:
        u_manager = User(
            id=uuid.uuid4(),
            tenant_id=t_id,
            email="pm@p5prod.com",
            hashed_password=get_password_hash("Secret123!"),
            full_name="P5 Production Manager",
            role=UserRole.PRODUCTION_MANAGER,
            is_active=True,
        )
        db.add(u_manager)
        db.commit()
        db.refresh(u_manager)

    u_supervisor = (
        db.query(User).filter(User.tenant_id == t_id, User.email == "super@p5prod.com").first()
    )
    if not u_supervisor:
        u_supervisor = User(
            id=uuid.uuid4(),
            tenant_id=t_id,
            email="super@p5prod.com",
            hashed_password=get_password_hash("Secret123!"),
            full_name="P5 Floor Supervisor",
            role=UserRole.SUPERVISOR,
            is_active=True,
        )
        db.add(u_supervisor)
        db.commit()
        db.refresh(u_supervisor)

    # Buyer, Style & Order
    buyer = db.query(Buyer).filter(Buyer.tenant_id == t_id, Buyer.code == "P5-BUYER").first()
    if not buyer:
        buyer = Buyer(
            id=uuid.uuid4(),
            tenant_id=t_id,
            name="P5 Global Retail",
            code="P5-BUYER",
            country="Germany",
        )
        db.add(buyer)
        db.commit()
        db.refresh(buyer)

    style = db.query(Style).filter(Style.tenant_id == t_id, Style.style_number == "P5-POLO").first()
    if not style:
        style = Style(
            id=uuid.uuid4(),
            tenant_id=t_id,
            buyer_id=buyer.id,
            style_number="P5-POLO",
            style_name="P5 Pique Polo",
            garment_type="Polo",
            sam=Decimal("12.50"),
            target_efficiency=Decimal("65.0"),
        )
        db.add(style)
        db.commit()
        db.refresh(style)

    ord_num = f"ORD-P5-{uuid.uuid4().hex[:6].upper()}"
    order = Order(
        id=uuid.uuid4(),
        tenant_id=t_id,
        buyer_id=buyer.id,
        style_id=style.id,
        order_number=ord_num,
        total_quantity=2000,
        unit_price=Decimal("4.50"),
        currency="USD",
        ex_factory_date=date.today() + timedelta(days=20),
        planned_sewing_start=date.today() + timedelta(days=5),
        status="IN_PRODUCTION",
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    # Line in tenant 2 for RLS test
    set_session_tenant(db, other_t_id)
    other_line = (
        db.query(ProductionLine)
        .filter(ProductionLine.tenant_id == other_t_id, ProductionLine.line_number == "L-OTHER-1")
        .first()
    )
    if not other_line:
        other_line = ProductionLine(
            id=uuid.uuid4(),
            tenant_id=other_t_id,
            line_number="L-OTHER-1",
            name="Other Secret Line",
            operator_count=30,
            helper_count=5,
            daily_working_hours=Decimal("8.00"),
            is_active=True,
        )
        db.add(other_line)
        db.commit()
        db.refresh(other_line)

    db.close()

    manager_token = create_access_token(str(u_manager.id), t_id, str(u_manager.role))
    supervisor_token = create_access_token(str(u_supervisor.id), t_id, str(u_supervisor.role))

    return {
        "tenant_id": t_id,
        "other_tenant_id": other_t_id,
        "manager_token": manager_token,
        "supervisor_token": supervisor_token,
        "order_id": str(order.id),
        "order_number": ord_num,
        "style_id": str(style.id),
        "other_line_id": str(other_line.id),
    }


def test_create_and_list_production_lines(prod_fixture):
    token = prod_fixture["manager_token"]
    headers = {"Authorization": f"Bearer {token}"}
    line_num = f"Line-{uuid.uuid4().hex[:4].upper()}"

    # 1. Create Line
    create_resp = client.post(
        "/api/v1/production/lines",
        headers=headers,
        json={
            "line_number": line_num,
            "name": f"Polo Unit {line_num}",
            "operator_count": 25,
            "helper_count": 4,
            "daily_working_hours": 8.0,
            "is_active": True,
        },
    )
    assert create_resp.status_code == 201
    line_data = create_resp.json()
    assert line_data["line_number"] == line_num
    assert line_data["operator_count"] == 25

    # 2. List lines
    list_resp = client.get("/api/v1/production/lines", headers=headers)
    assert list_resp.status_code == 200
    lines = list_resp.json()
    assert any(line["line_number"] == line_num for line in lines)


def test_record_daily_production_and_efficiency_math(prod_fixture):
    token = prod_fixture["supervisor_token"]
    headers = {"Authorization": f"Bearer {token}"}
    order_id = prod_fixture["order_id"]

    # Post a daily log for cutting
    cut_resp = client.post(
        "/api/v1/production/logs",
        headers=headers,
        json={
            "date": date.today().isoformat(),
            "order_id": order_id,
            "stage": "CUTTING",
            "planned_output": 600,
            "actual_output": 650,
            "rejected_qty": 5,
            "operator_count": 6,
            "working_hours": 8.0,
            "notes": "Spreading and cutting completed smoothly",
        },
    )
    assert cut_resp.status_code == 201
    cut_data = cut_resp.json()
    assert cut_data["actual_output"] == 650
    assert cut_data["rejected_qty"] == 5

    # Post a daily log for sewing
    sew_resp = client.post(
        "/api/v1/production/logs",
        headers=headers,
        json={
            "date": date.today().isoformat(),
            "order_id": order_id,
            "stage": "SEWING",
            "planned_output": 400,
            "actual_output": 420,
            "rejected_qty": 8,
            "operator_count": 24,
            "working_hours": 8.0,
            "notes": "Front placket and collar attachment",
        },
    )
    assert sew_resp.status_code == 201
    sew_data = sew_resp.json()
    assert sew_data["actual_output"] == 420

    # SAM Math Verification:
    # Produced minutes = 420 pcs * 12.5 SAM = 5,250 minutes
    # Available minutes = 24 operators * 8 hours * 60 = 11,520 minutes
    # Efficiency % = (5250 / 11520) * 100 = ~45.57%
    assert float(sew_data["produced_minutes"]) == 5250.0
    assert float(sew_data["available_minutes"]) == 11520.0
    assert float(sew_data["efficiency_pct"]) == 45.57
    assert float(sew_data["rejection_rate_pct"]) == 1.90  # 8 / 420 * 100 = 1.90%


def test_order_production_summary_and_forecasting(prod_fixture):
    token = prod_fixture["manager_token"]
    headers = {"Authorization": f"Bearer {token}"}
    order_id = prod_fixture["order_id"]

    summary_resp = client.get(
        f"/api/v1/production/orders/{order_id}/summary",
        headers=headers,
    )
    assert summary_resp.status_code == 200
    summary = summary_resp.json()
    assert summary["order_number"] == prod_fixture["order_number"]
    assert summary["total_quantity"] == 2000
    assert summary["cumulative_cutting"] == 650
    assert summary["cumulative_sewing"] == 420
    assert summary["remaining_sewing_qty"] == 1580
    assert float(summary["rolling_daily_rate"]) == 420.0
    assert summary["is_on_track"] is True


def test_production_risk_r3_endpoint(prod_fixture):
    token = prod_fixture["manager_token"]
    headers = {"Authorization": f"Bearer {token}"}

    risk_resp = client.get("/api/v1/risk/production", headers=headers)
    assert risk_resp.status_code == 200
    risks = risk_resp.json()
    assert isinstance(risks, list)
    assert len(risks) >= 1
    r3 = next((r for r in risks if r["rule"] == "R3"), None)
    assert r3 is not None
    assert "evidence" in r3


def test_production_rls_isolation(prod_fixture):
    token = prod_fixture["manager_token"]
    headers = {"Authorization": f"Bearer {token}"}
    other_line_id = prod_fixture["other_line_id"]

    # 1. Tenant 1 must never see Tenant 2's production lines
    list_resp = client.get("/api/v1/production/lines", headers=headers)
    assert list_resp.status_code == 200
    lines = list_resp.json()
    line_ids = [line["id"] for line in lines]
    assert other_line_id not in line_ids

    # 2. Direct database RLS check
    db = SessionLocal()
    set_session_tenant(db, prod_fixture["tenant_id"])
    query_line = db.query(ProductionLine).filter(ProductionLine.id == uuid.UUID(other_line_id)).first()
    assert query_line is None  # PostgreSQL RLS policy blocks visibility completely!
    db.close()

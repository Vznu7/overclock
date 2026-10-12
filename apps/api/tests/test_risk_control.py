import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal, set_session_tenant
from app.core.security import create_access_token, get_password_hash
from app.domains.auth.models import User, UserRole
from app.domains.orders.models import Buyer, Order, OrderMilestone, Style
from app.domains.tenants.models import Tenant
from app.main import app

client = TestClient(app)


@pytest.fixture(scope="module")
def risk_fixture():
    db = SessionLocal()
    t_id = "tenant-risk-test"

    # Setup tenant
    set_session_tenant(db, t_id)
    t = db.query(Tenant).filter(Tenant.id == t_id).first()
    if not t:
        t = Tenant(id=t_id, name="Risk Tower Mill", cluster="Tirupur", is_active=True)
        db.add(t)
        db.commit()

    u_owner = db.query(User).filter(User.tenant_id == t_id, User.email == "owner@risktower.com").first()
    if not u_owner:
        u_owner = User(
            id=uuid.uuid4(),
            tenant_id=t_id,
            email="owner@risktower.com",
            hashed_password=get_password_hash("Secret123!"),
            full_name="Risk Owner",
            role=UserRole.OWNER,
            is_active=True,
        )
        db.add(u_owner)
        db.commit()
        db.refresh(u_owner)

    buyer = db.query(Buyer).filter(Buyer.tenant_id == t_id, Buyer.code == "RT-BUYER").first()
    if not buyer:
        buyer = Buyer(
            id=uuid.uuid4(),
            tenant_id=t_id,
            name="Risk Tower Buyer",
            code="RT-BUYER",
            country="UK",
        )
        db.add(buyer)
        db.commit()
        db.refresh(buyer)

    style = db.query(Style).filter(Style.tenant_id == t_id, Style.style_number == "RT-STYLE").first()
    if not style:
        style = Style(
            id=uuid.uuid4(),
            tenant_id=t_id,
            buyer_id=buyer.id,
            style_number="RT-STYLE",
            style_name="Organic Crew",
            garment_type="T-Shirt",
            sam=Decimal("9.00"),
            target_efficiency=Decimal("65.0"),
        )
        db.add(style)
        db.commit()
        db.refresh(style)

    ord_num = f"ORD-RT-{uuid.uuid4().hex[:6].upper()}"
    order = Order(
        id=uuid.uuid4(),
        tenant_id=t_id,
        order_number=ord_num,
        buyer_id=buyer.id,
        style_id=style.id,
        status="IN_PRODUCTION",
        total_quantity=5000,
        currency="USD",
        unit_price=Decimal("7.00"),
        planned_sewing_start=date.today() - timedelta(days=15),
        ex_factory_date=date.today() + timedelta(days=10),
    )
    db.add(order)
    db.flush()

    # Add an overdue milestone to test Rule R5
    m_overdue = OrderMilestone(
        id=uuid.uuid4(),
        tenant_id=t_id,
        order_id=order.id,
        name="PP Sample Approval",
        planned_date=date.today() - timedelta(days=7),
        status="PENDING",
    )
    db.add(m_overdue)
    db.commit()
    db.close()

    owner_token = create_access_token(str(u_owner.id), t_id, str(u_owner.role))

    return {
        "tenant_id": t_id,
        "token": owner_token,
        "order_id": str(order.id),
        "order_number": ord_num,
    }


def test_evaluate_all_risks(risk_fixture):
    headers = {"Authorization": f"Bearer {risk_fixture['token']}"}

    res = client.get("/api/v1/risk/evaluate", headers=headers)
    assert res.status_code == 200
    summaries = res.json()
    assert len(summaries) >= 1

    target_summary = next(s for s in summaries if s["order_id"] == risk_fixture["order_id"])
    assert target_summary["order_number"] == risk_fixture["order_number"]
    assert len(target_summary["risks"]) >= 3  # Contains evaluations for R3, R4, R5, R6

    # Verify R5 Milestone Gate Slippage triggered due to overdue PP sample
    r5_risk = next(r for r in target_summary["risks"] if r["rule"] == "R5")
    assert r5_risk["triggered"] is True
    assert r5_risk["severity"] in ("HIGH", "CRITICAL")
    assert "overdue" in r5_risk["headline"].lower()


def test_evaluate_order_risk(risk_fixture):
    headers = {"Authorization": f"Bearer {risk_fixture['token']}"}

    res = client.get(f"/api/v1/risk/orders/{risk_fixture['order_id']}", headers=headers)
    assert res.status_code == 200
    summary = res.json()
    assert summary["order_id"] == risk_fixture["order_id"]
    assert summary["max_severity"] in ("HIGH", "CRITICAL")

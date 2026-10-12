import uuid
from datetime import date
from decimal import Decimal

from app.domains.risk.rules import (
    evaluate_rule_r1,
    evaluate_rule_r2,
    evaluate_rule_r3,
    evaluate_rule_r4,
    evaluate_rule_r5,
    evaluate_rule_r6,
)
from app.domains.risk.schemas import (
    InboundPoInput,
    RiskSeverity,
    TrimRequirementInput,
)


def test_r1_fabric_fully_satisfied_by_current_stock():
    order_id = str(uuid.uuid4())
    today = date(2026, 10, 15)
    target_date = date(2026, 10, 25)

    result = evaluate_rule_r1(
        order_id=order_id,
        target_fabric_date=target_date,
        required_qty=Decimal("500.000"),
        current_stock=Decimal("550.000"),
        inbound_pos=[],
        today=today,
    )

    assert result.rule == "R1"
    assert result.triggered is False
    assert result.severity == RiskSeverity.NORMAL
    assert result.deficit_qty == Decimal("0.000")
    assert result.days_delayed == 0


def test_r1_fabric_satisfied_by_on_time_inbound_po():
    order_id = str(uuid.uuid4())
    today = date(2026, 10, 15)
    target_date = date(2026, 10, 25)

    inbound = [
        InboundPoInput(
            po_number="SPO-001",
            material_id=uuid.uuid4(),
            quantity=Decimal("300.000"),
            expected_date=date(2026, 10, 20),
            status="PLACED",
        ),
        InboundPoInput(
            po_number="SPO-002",
            material_id=uuid.uuid4(),
            quantity=Decimal("200.000"),
            expected_date=date(2026, 10, 25),
            status="PARTIAL_RECEIVED",
        ),
    ]

    result = evaluate_rule_r1(
        order_id=order_id,
        target_fabric_date=target_date,
        required_qty=Decimal("450.000"),
        current_stock=Decimal("50.000"),
        inbound_pos=inbound,
        today=today,
    )

    assert result.triggered is False
    assert result.severity == RiskSeverity.NORMAL
    assert result.evidence["total_available"] == 550.0


def test_r1_fabric_ignores_cancelled_or_unapproved_pos():
    order_id = str(uuid.uuid4())
    today = date(2026, 10, 15)
    target_date = date(2026, 10, 25)

    inbound = [
        InboundPoInput(
            po_number="SPO-CANCELLED",
            material_id=uuid.uuid4(),
            quantity=Decimal("500.000"),
            expected_date=date(2026, 10, 20),
            status="CANCELLED",
        ),
    ]

    result = evaluate_rule_r1(
        order_id=order_id,
        target_fabric_date=target_date,
        required_qty=Decimal("400.000"),
        current_stock=Decimal("100.000"),
        inbound_pos=inbound,
        today=today,
    )

    assert result.triggered is True
    assert result.severity == RiskSeverity.CRITICAL
    assert result.deficit_qty == Decimal("300.000")
    assert result.days_delayed == 0


def test_r1_fabric_delayed_po_small_delay():
    order_id = str(uuid.uuid4())
    today = date(2026, 10, 15)
    target_date = date(2026, 10, 25)

    # Required 100 kg, stock 85 kg (deficit 15 kg = 15%, <= 25%), delayed PO arrives 3 days late (<= 5 days)
    inbound = [
        InboundPoInput(
            po_number="SPO-LATE-1",
            material_id=uuid.uuid4(),
            quantity=Decimal("50.000"),
            expected_date=date(2026, 10, 28),
            status="PLACED",
        )
    ]

    result = evaluate_rule_r1(
        order_id=order_id,
        target_fabric_date=target_date,
        required_qty=Decimal("100.000"),
        current_stock=Decimal("85.000"),
        inbound_pos=inbound,
        today=today,
    )

    assert result.triggered is True
    assert result.severity == RiskSeverity.HIGH
    assert result.deficit_qty == Decimal("15.000")
    assert result.days_delayed == 3


def test_r1_fabric_delayed_po_severe_delay_and_high_deficit():
    order_id = str(uuid.uuid4())
    today = date(2026, 10, 15)
    target_date = date(2026, 10, 25)

    # Required 1000 kg, stock 0, delayed PO arrives 12 days late (> 5 days)
    inbound = [
        InboundPoInput(
            po_number="SPO-LATE-2",
            material_id=uuid.uuid4(),
            quantity=Decimal("1000.000"),
            expected_date=date(2026, 11, 6),
            status="PLACED",
        )
    ]

    result = evaluate_rule_r1(
        order_id=order_id,
        target_fabric_date=target_date,
        required_qty=Decimal("1000.000"),
        current_stock=Decimal("0.000"),
        inbound_pos=inbound,
        today=today,
    )

    assert result.triggered is True
    assert result.severity == RiskSeverity.CRITICAL
    assert result.days_delayed == 12
    assert result.evidence["deficit_percentage"] == 100.0


def test_r1_fabric_zero_required_qty():
    order_id = str(uuid.uuid4())
    result = evaluate_rule_r1(
        order_id=order_id,
        target_fabric_date=date(2026, 10, 25),
        required_qty=Decimal("0.000"),
        current_stock=Decimal("0.000"),
        inbound_pos=[],
    )
    assert result.triggered is False
    assert result.severity == RiskSeverity.NORMAL


# --- Rule R2 Unit Tests ---
def test_r2_trims_all_in_stock():
    order_id = str(uuid.uuid4())
    today = date(2026, 10, 10)
    sewing_date = date(2026, 10, 25)  # Cutoff is 2026-10-18

    trims = [
        TrimRequirementInput(
            material_id=uuid.uuid4(),
            material_code="BTN-01",
            material_name="Horn Button 18L",
            component_name="Front Buttons",
            required_qty=Decimal("5000.000"),
            current_stock=Decimal("6000.000"),
        ),
        TrimRequirementInput(
            material_id=uuid.uuid4(),
            material_code="THRD-01",
            material_name="Spun Poly Thread",
            component_name="Sewing Thread",
            required_qty=Decimal("120.000"),
            current_stock=Decimal("150.000"),
        ),
    ]

    result = evaluate_rule_r2(
        order_id=order_id,
        sewing_start_date=sewing_date,
        trim_requirements=trims,
        today=today,
    )

    assert result.rule == "R2"
    assert result.triggered is False
    assert result.severity == RiskSeverity.NORMAL
    assert result.deficit_qty == Decimal("0.000")


def test_r2_trims_satisfied_by_inbound_before_cutoff():
    order_id = str(uuid.uuid4())
    today = date(2026, 10, 10)
    sewing_date = date(2026, 10, 25)  # Cutoff: 2026-10-18

    m_id = uuid.uuid4()
    inbound = [
        InboundPoInput(
            po_number="SPO-ZIP-1",
            material_id=m_id,
            quantity=Decimal("3000.000"),
            expected_date=date(2026, 10, 16),  # Arrives 2 days before cutoff
            status="PLACED",
        )
    ]

    trims = [
        TrimRequirementInput(
            material_id=m_id,
            material_code="ZIP-YKK-01",
            material_name="YKK Metal Zipper",
            component_name="Front Zipper",
            required_qty=Decimal("2500.000"),
            current_stock=Decimal("0.000"),
            inbound_pos=inbound,
        )
    ]

    result = evaluate_rule_r2(
        order_id=order_id,
        sewing_start_date=sewing_date,
        trim_requirements=trims,
        today=today,
    )

    assert result.triggered is False
    assert result.severity == RiskSeverity.NORMAL


def test_r2_trims_shortage_past_cutoff_is_critical():
    order_id = str(uuid.uuid4())
    today = date(2026, 10, 20)  # Today is AFTER cutoff (cutoff was 2026-10-18)
    sewing_date = date(2026, 10, 25)

    trims = [
        TrimRequirementInput(
            material_id=uuid.uuid4(),
            material_code="LBL-CARE-01",
            material_name="Printed Satin Care Label",
            component_name="Care Label",
            required_qty=Decimal("3000.000"),
            current_stock=Decimal("1000.000"),
            inbound_pos=[],
        )
    ]

    result = evaluate_rule_r2(
        order_id=order_id,
        sewing_start_date=sewing_date,
        trim_requirements=trims,
        today=today,
    )

    assert result.triggered is True
    assert result.severity == RiskSeverity.CRITICAL
    assert result.deficit_qty == Decimal("2000.000")
    assert result.days_delayed == 2  # 2 days past cutoff


def test_r2_trims_shortage_before_cutoff_moderate_deficit():
    order_id = str(uuid.uuid4())
    today = date(2026, 10, 10)  # Before cutoff (cutoff 2026-10-18)
    sewing_date = date(2026, 10, 25)

    # Required 1000, stock 700, deficit 300 (30% <= 50%) -> HIGH
    trims = [
        TrimRequirementInput(
            material_id=uuid.uuid4(),
            material_code="TAG-HANG-01",
            material_name="Recycled Paper Hangtag",
            component_name="Hangtag",
            required_qty=Decimal("1000.000"),
            current_stock=Decimal("700.000"),
            inbound_pos=[],
        )
    ]

    result = evaluate_rule_r2(
        order_id=order_id,
        sewing_start_date=sewing_date,
        trim_requirements=trims,
        today=today,
    )

    assert result.triggered is True
    assert result.severity == RiskSeverity.HIGH
    assert result.deficit_qty == Decimal("300.000")


def test_r2_empty_requirements():
    order_id = str(uuid.uuid4())
    result = evaluate_rule_r2(
        order_id=order_id,
        sewing_start_date=date(2026, 10, 25),
        trim_requirements=[],
    )
    assert result.triggered is False
    assert result.severity == RiskSeverity.NORMAL


def test_r2_trims_more_than_three_shortages():
    order_id = str(uuid.uuid4())
    today = date(2026, 10, 10)
    sewing_date = date(2026, 10, 25)

    trims = [
        TrimRequirementInput(
            material_id=uuid.uuid4(),
            material_code=f"TRIM-{i}",
            material_name=f"Trim Item {i}",
            component_name=f"Component {i}",
            required_qty=Decimal("100.000"),
            current_stock=Decimal("0.000"),
        )
        for i in range(5)
    ]

    result = evaluate_rule_r2(
        order_id=order_id,
        sewing_start_date=sewing_date,
        trim_requirements=trims,
        today=today,
    )

    assert result.triggered is True
    assert result.severity == RiskSeverity.CRITICAL
    assert "and 2 others" in result.headline


def test_r3_completed_order_returns_normal():
    order_id = str(uuid.uuid4())
    today = date(2026, 10, 15)
    target_date = date(2026, 10, 25)

    result = evaluate_rule_r3(
        order_id=order_id,
        total_quantity=5000,
        cumulative_sewn=5000,
        recent_daily_outputs=[500, 500, 500],
        target_sewing_end_date=target_date,
        today=today,
    )

    assert result.rule == "R3"
    assert result.triggered is False
    assert result.severity == RiskSeverity.NORMAL
    assert result.deficit_qty == Decimal("0.0")
    assert result.days_delayed == 0
    assert "100% of order quantity produced" in result.headline


def test_r3_past_deadline_uncompleted_triggers_critical():
    order_id = str(uuid.uuid4())
    today = date(2026, 10, 26)
    target_date = date(2026, 10, 20)  # 6 days ago

    result = evaluate_rule_r3(
        order_id=order_id,
        total_quantity=5000,
        cumulative_sewn=3500,  # 1500 remaining
        recent_daily_outputs=[200, 250, 200],
        target_sewing_end_date=target_date,
        today=today,
    )

    assert result.triggered is True
    assert result.severity == RiskSeverity.CRITICAL
    assert result.days_delayed == 6
    assert result.deficit_qty == Decimal("1500")
    assert "Critical sewing overrun" in result.headline


def test_r3_pacing_on_track_returns_normal():
    order_id = str(uuid.uuid4())
    today = date(2026, 10, 15)
    target_date = date(2026, 10, 25)  # 10 days remaining

    # remaining: 2000 pcs, days: 10 -> required: 200 pcs/day. Rolling pace: 250 pcs/day
    result = evaluate_rule_r3(
        order_id=order_id,
        total_quantity=5000,
        cumulative_sewn=3000,
        recent_daily_outputs=[240, 260, 250],
        target_sewing_end_date=target_date,
        today=today,
    )

    assert result.triggered is False
    assert result.severity == RiskSeverity.NORMAL
    assert result.days_delayed == 0
    assert "pacing on target" in result.headline


def test_r3_pacing_moderate_delay_triggers_high():
    order_id = str(uuid.uuid4())
    today = date(2026, 10, 15)
    target_date = date(2026, 10, 25)  # 10 days remaining

    # remaining: 2000 pcs, days: 10 -> required: 200 pcs/day.
    # Rolling pace: 170 pcs/day -> days needed: ceil(2000 / 170) = 12 days -> delayed by 2 days (<= 3 days)
    # 170 >= 200 * 0.85 (170 >= 170) -> delayed by 2 days -> triggers HIGH
    result = evaluate_rule_r3(
        order_id=order_id,
        total_quantity=5000,
        cumulative_sewn=3000,
        recent_daily_outputs=[170, 170, 170],
        target_sewing_end_date=target_date,
        today=today,
    )

    assert result.triggered is True
    assert result.severity == RiskSeverity.HIGH
    assert result.days_delayed == 2
    assert "Sewing run-rate warning" in result.headline


def test_r3_pacing_severe_delay_triggers_critical():
    order_id = str(uuid.uuid4())
    today = date(2026, 10, 15)
    target_date = date(2026, 10, 25)  # 10 days remaining

    # remaining: 3000 pcs, days: 10 -> required: 300 pcs/day.
    # Rolling pace: 100 pcs/day (33% of required, < 60%) -> days needed: 30 days -> delayed by 20 days -> CRITICAL
    result = evaluate_rule_r3(
        order_id=order_id,
        total_quantity=5000,
        cumulative_sewn=2000,
        recent_daily_outputs=[100, 95, 105],
        target_sewing_end_date=target_date,
        today=today,
    )

    assert result.triggered is True
    assert result.severity == RiskSeverity.CRITICAL
    assert result.days_delayed == 20
    assert "Critical sewing pace slippage" in result.headline


def test_r3_zero_output_triggers_critical_indefinite():
    order_id = str(uuid.uuid4())
    today = date(2026, 10, 15)
    target_date = date(2026, 10, 25)

    result = evaluate_rule_r3(
        order_id=order_id,
        total_quantity=5000,
        cumulative_sewn=0,
        recent_daily_outputs=[],
        target_sewing_end_date=target_date,
        today=today,
    )

    assert result.triggered is True
    assert result.severity == RiskSeverity.CRITICAL
    assert result.days_delayed == 999
    assert result.evidence["projected_completion_date"] is None


def test_r3_default_today_branch():
    order_id = str(uuid.uuid4())
    # Test with today=None
    result = evaluate_rule_r3(
        order_id=order_id,
        total_quantity=5000,
        cumulative_sewn=5000,
        recent_daily_outputs=[500],
        target_sewing_end_date=date(2099, 1, 1),
    )
    assert result.triggered is False


# --- Rule R4 Tests (Outside Job-Work Delay & Loss Anomaly) ---
def test_r4_no_challans_returns_normal():
    result = evaluate_rule_r4(
        order_id=str(uuid.uuid4()),
        challans=[],
        today=date(2026, 10, 15),
    )
    assert result.rule == "R4"
    assert result.triggered is False
    assert result.severity == RiskSeverity.NORMAL


def test_r4_all_on_time_under_loss_limit_returns_normal():
    challans = [
        {
            "challan_number": "DC-001",
            "process_name": "Dyeing",
            "status": "COMPLETED",
            "expected_return_date": date(2026, 10, 10),
            "actual_return_date": date(2026, 10, 9),
            "issued_weight_kg": 1000.0,
            "received_weight_kg": 980.0,  # 2% loss (< 3.5%)
        }
    ]
    result = evaluate_rule_r4(
        order_id=str(uuid.uuid4()),
        challans=challans,
        today=date(2026, 10, 15),
    )
    assert result.triggered is False
    assert result.severity == RiskSeverity.NORMAL


def test_r4_overdue_challan_triggers_high_and_critical():
    today = date(2026, 10, 15)
    # 2 days overdue -> HIGH
    c_high = [
        {
            "challan_number": "DC-002",
            "process_name": "Printing",
            "status": "ISSUED",
            "expected_return_date": date(2026, 10, 13),
            "actual_return_date": None,
        }
    ]
    res_high = evaluate_rule_r4(str(uuid.uuid4()), c_high, today=today)
    assert res_high.triggered is True
    assert res_high.severity == RiskSeverity.HIGH
    assert res_high.days_delayed == 2

    # 7 days overdue -> CRITICAL
    c_crit = [
        {
            "challan_number": "DC-003",
            "process_name": "Dyeing",
            "status": "ISSUED",
            "expected_return_date": date(2026, 10, 8),
            "actual_return_date": None,
        }
    ]
    res_crit = evaluate_rule_r4(str(uuid.uuid4()), c_crit, today=today)
    assert res_crit.triggered is True
    assert res_crit.severity == RiskSeverity.CRITICAL
    assert res_crit.days_delayed == 7


def test_r4_weight_loss_anomaly_triggers_high_and_critical():
    today = date(2026, 10, 15)
    # 4% loss (> 3.5%, <= 5%) -> HIGH
    c_high = [
        {
            "challan_number": "DC-004",
            "process_name": "Dyeing",
            "status": "COMPLETED",
            "expected_return_date": date(2026, 10, 10),
            "actual_return_date": date(2026, 10, 10),
            "issued_weight_kg": 1000.0,
            "received_weight_kg": 960.0,  # 4.0% loss
        }
    ]
    res_high = evaluate_rule_r4(str(uuid.uuid4()), c_high, today=today)
    assert res_high.triggered is True
    assert res_high.severity == RiskSeverity.HIGH

    # 6% loss (> 5.0%) -> CRITICAL
    c_crit = [
        {
            "challan_number": "DC-005",
            "process_name": "Dyeing",
            "status": "COMPLETED",
            "expected_return_date": date(2026, 10, 10),
            "actual_return_date": date(2026, 10, 10),
            "issued_weight_kg": 1000.0,
            "received_weight_kg": 940.0,  # 6.0% loss
        }
    ]
    res_crit = evaluate_rule_r4(str(uuid.uuid4()), c_crit, today=today)
    assert res_crit.triggered is True
    assert res_crit.severity == RiskSeverity.CRITICAL


def test_r4_default_today_branch():
    res = evaluate_rule_r4(str(uuid.uuid4()), [])
    assert res.triggered is False


# --- Rule R5 Tests (Critical Path Milestone Gate Slippage) ---
def test_r5_all_completed_returns_normal():
    milestones = [
        {"name": "Fabric In-House", "status": "COMPLETED", "planned_date": date(2026, 10, 5)},
        {"name": "PP Sample", "status": "COMPLETED", "planned_date": date(2026, 10, 8)},
    ]
    result = evaluate_rule_r5(str(uuid.uuid4()), milestones, today=date(2026, 10, 15))
    assert result.rule == "R5"
    assert result.triggered is False
    assert result.severity == RiskSeverity.NORMAL


def test_r5_overdue_gate_triggers_high_and_critical():
    today = date(2026, 10, 15)
    # 2 days overdue -> HIGH
    m_high = [
        {"name": "PP Sample Approved", "status": "PENDING", "planned_date": date(2026, 10, 13)},
    ]
    res_high = evaluate_rule_r5(str(uuid.uuid4()), m_high, today=today)
    assert res_high.triggered is True
    assert res_high.severity == RiskSeverity.HIGH
    assert res_high.days_delayed == 2

    # 7 days overdue -> CRITICAL
    m_crit = [
        {"name": "Fabric In-House", "status": "PENDING", "planned_date": "2026-10-08"},
    ]
    res_crit = evaluate_rule_r5(str(uuid.uuid4()), m_crit, today=today)
    assert res_crit.triggered is True
    assert res_crit.severity == RiskSeverity.CRITICAL
    assert res_crit.days_delayed == 7


def test_r5_approaching_gate_triggers_medium():
    today = date(2026, 10, 15)
    # due in 2 days -> MEDIUM
    m_med = [
        {"name": "Cutting Start", "status": "PENDING", "planned_date": date(2026, 10, 17)},
    ]
    res_med = evaluate_rule_r5(str(uuid.uuid4()), m_med, today=today)
    assert res_med.triggered is True
    assert res_med.severity == RiskSeverity.MEDIUM
    assert "due in 2 day(s)" in res_med.headline


def test_r5_default_today_branch():
    res = evaluate_rule_r5(str(uuid.uuid4()), [])
    assert res.triggered is False


# --- Rule R6 Tests (Order Inactivity / Stagnation) ---
def test_r6_non_active_order_returns_normal():
    result = evaluate_rule_r6(
        order_id=str(uuid.uuid4()),
        order_status="DRAFT",
        last_activity_date=date(2026, 9, 1),
        today=date(2026, 10, 15),
    )
    assert result.rule == "R6"
    assert result.triggered is False
    assert result.severity == RiskSeverity.NORMAL


def test_r6_active_recent_activity_returns_normal():
    result = evaluate_rule_r6(
        order_id=str(uuid.uuid4()),
        order_status="IN_PRODUCTION",
        last_activity_date=date(2026, 10, 14),  # 1 day ago
        today=date(2026, 10, 15),
    )
    assert result.triggered is False
    assert result.severity == RiskSeverity.NORMAL


def test_r6_inactive_5_days_triggers_high():
    result = evaluate_rule_r6(
        order_id=str(uuid.uuid4()),
        order_status="IN_PRODUCTION",
        last_activity_date=date(2026, 10, 10),  # 5 days ago
        today=date(2026, 10, 15),
    )
    assert result.triggered is True
    assert result.severity == RiskSeverity.HIGH
    assert result.days_delayed == 5


def test_r6_inactive_7_days_or_none_triggers_critical():
    today = date(2026, 10, 15)
    # 8 days ago
    res_8 = evaluate_rule_r6(
        order_id=str(uuid.uuid4()),
        order_status="CONFIRMED",
        last_activity_date=date(2026, 10, 7),
        today=today,
    )
    assert res_8.triggered is True
    assert res_8.severity == RiskSeverity.CRITICAL

    # Never touched (None)
    res_none = evaluate_rule_r6(
        order_id=str(uuid.uuid4()),
        order_status="IN_PRODUCTION",
        last_activity_date=None,
        today=today,
    )
    assert res_none.triggered is True
    assert res_none.severity == RiskSeverity.CRITICAL


def test_r6_default_today_branch():
    res = evaluate_rule_r6(str(uuid.uuid4()), "DRAFT", None)
    assert res.triggered is False


def test_r4_open_challan_on_time():
    challans = [
        {
            "challan_number": "DC-FUTURE",
            "process_name": "Washing",
            "status": "ISSUED",
            "expected_return_date": date(2026, 10, 25),
            "actual_return_date": None,
            "issued_weight_kg": 500.0,
            "received_weight_kg": 0.0,
        }
    ]
    res = evaluate_rule_r4(str(uuid.uuid4()), challans, today=date(2026, 10, 15))
    assert res.triggered is False
    assert res.severity == RiskSeverity.NORMAL


def test_r5_future_milestone_not_approaching():
    milestones = [
        {"name": "Final Inspection", "status": "PENDING", "planned_date": date(2026, 10, 30)},
    ]
    res = evaluate_rule_r5(str(uuid.uuid4()), milestones, today=date(2026, 10, 15))
    assert res.triggered is False
    assert res.severity == RiskSeverity.NORMAL

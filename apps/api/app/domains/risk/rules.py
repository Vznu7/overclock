import math
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from app.domains.risk.schemas import (
    InboundPoInput,
    RiskAssessment,
    RiskSeverity,
    TrimRequirementInput,
)


def evaluate_rule_r1(
    order_id: str,
    target_fabric_date: date,
    required_qty: Decimal,
    current_stock: Decimal,
    inbound_pos: list[InboundPoInput],
    order_number: str | None = None,
    buyer_name: str | None = None,
    today: date | None = None,
) -> RiskAssessment:
    """Evaluate Rule R1: Fabric Arrival Deficit.

    Deterministic logic:
    1. Filter verified inbound POs arriving on or before target fabric date.
    2. Sum current on-hand stock and on-time inbound POs.
    3. If total available >= required quantity, rule does not trigger.
    4. Otherwise, compute deficit and delay. If delay > 5 days or deficit > 25%, flag CRITICAL.
    """
    if today is None:
        today = date.today()

    active_statuses = {"PLACED", "PARTIAL_RECEIVED"}

    on_time_inbound = sum(
        (
            po.quantity
            for po in inbound_pos
            if po.expected_date <= target_fabric_date and po.status in active_statuses
        ),
        Decimal("0.000"),
    )
    total_available = current_stock + on_time_inbound

    if total_available >= required_qty:
        return RiskAssessment(
            rule="R1",
            rule_name="Fabric Arrival Deficit",
            order_id=order_id,
            order_number=order_number,
            buyer_name=buyer_name,
            triggered=False,
            severity=RiskSeverity.NORMAL,
            deficit_qty=Decimal("0.000"),
            days_delayed=0,
            headline="Fabric supply fully satisfied for production timeline",
            explanation=(
                f"Available fabric ({total_available:.2f} kg) meets or exceeds requirement ({required_qty:.2f} kg). "
                f"Stock on hand: {current_stock:.2f} kg, scheduled on-time inbound: {on_time_inbound:.2f} kg."
            ),
            evidence={
                "required_qty": float(required_qty),
                "current_stock": float(current_stock),
                "on_time_inbound": float(on_time_inbound),
                "total_available": float(total_available),
                "target_fabric_date": target_fabric_date.isoformat(),
                "days_delayed": 0,
            },
        )

    deficit = required_qty - total_available
    deficit_pct = (
        (deficit / required_qty * Decimal("100.0")) if required_qty > 0 else Decimal("100.0")
    )

    delayed_pos = [
        po
        for po in inbound_pos
        if po.expected_date > target_fabric_date and po.status in active_statuses
    ]

    if delayed_pos:
        earliest_delay = min(po.expected_date for po in delayed_pos)
        days_delayed = (earliest_delay - target_fabric_date).days
    else:
        days_delayed = 999  # No inbound PO covers the balance

    if days_delayed > 5 or deficit_pct > Decimal("25.0") or days_delayed == 999:
        severity = RiskSeverity.CRITICAL
    else:
        severity = RiskSeverity.HIGH

    headline = (
        f"Critical fabric deficit: {deficit:.2f} kg short ({deficit_pct:.1f}% deficit)"
        if severity == RiskSeverity.CRITICAL
        else f"High fabric deficit: {deficit:.2f} kg short ({deficit_pct:.1f}% deficit)"
    )

    if days_delayed == 999:
        delay_msg = "No supplier PO has been placed to cover the outstanding balance."
    else:
        delay_msg = f"Earliest inbound fabric PO arrives on {earliest_delay.isoformat()}, {days_delayed} day(s) after target milestone date {target_fabric_date.isoformat()}."

    explanation = (
        f"Required fabric: {required_qty:.2f} kg, but only {total_available:.2f} kg is available on or before {target_fabric_date.isoformat()} "
        f"(On-hand: {current_stock:.2f} kg, on-time inbound: {on_time_inbound:.2f} kg). {delay_msg}"
    )

    return RiskAssessment(
        rule="R1",
        rule_name="Fabric Arrival Deficit",
        order_id=order_id,
        order_number=order_number,
        buyer_name=buyer_name,
        triggered=True,
        severity=severity,
        deficit_qty=deficit,
        days_delayed=days_delayed if days_delayed != 999 else 0,
        headline=headline,
        explanation=explanation,
        evidence={
            "required_qty": float(required_qty),
            "current_stock": float(current_stock),
            "on_time_inbound": float(on_time_inbound),
            "total_available": float(total_available),
            "deficit_qty": float(deficit),
            "deficit_percentage": float(deficit_pct),
            "target_fabric_date": target_fabric_date.isoformat(),
            "days_delayed": days_delayed,
        },
    )


def evaluate_rule_r2(
    order_id: str,
    sewing_start_date: date,
    trim_requirements: list[TrimRequirementInput],
    order_number: str | None = None,
    buyer_name: str | None = None,
    today: date | None = None,
    buffer_days: int = 7,
) -> RiskAssessment:
    """Evaluate Rule R2: Trims & Accessories Shortage.

    Deterministic logic:
    1. Trims must be in-house or arriving at least buffer_days (default 7) prior to sewing start.
    2. Check each required trim item against current stock + verified inbound orders before cutoff.
    3. If any item is short, flag HIGH or CRITICAL.
    """
    if today is None:
        today = date.today()

    cutoff_date = sewing_start_date - timedelta(days=buffer_days)
    active_statuses = {"PLACED", "PARTIAL_RECEIVED"}

    shortages: list[dict[str, object]] = []

    for trim in trim_requirements:
        on_time_inbound = sum(
            (
                po.quantity
                for po in trim.inbound_pos
                if po.expected_date <= cutoff_date and po.status in active_statuses
            ),
            Decimal("0.000"),
        )
        available = trim.current_stock + on_time_inbound
        if available < trim.required_qty:
            deficit = trim.required_qty - available
            deficit_pct = (
                (deficit / trim.required_qty * Decimal("100.0"))
                if trim.required_qty > 0
                else Decimal("100.0")
            )
            shortages.append(
                {
                    "material_id": str(trim.material_id),
                    "material_code": trim.material_code,
                    "material_name": trim.material_name,
                    "component_name": trim.component_name,
                    "required_qty": float(trim.required_qty),
                    "available_qty": float(available),
                    "deficit_qty": float(deficit),
                    "deficit_percentage": float(deficit_pct),
                }
            )

    if not shortages:
        return RiskAssessment(
            rule="R2",
            rule_name="Trim & Accessory Shortage",
            order_id=order_id,
            order_number=order_number,
            buyer_name=buyer_name,
            triggered=False,
            severity=RiskSeverity.NORMAL,
            deficit_qty=Decimal("0.000"),
            days_delayed=0,
            headline="All trims and accessories verified ready for sewing floor",
            explanation=(
                f"All required trims/accessories are on hand or scheduled for delivery before "
                f"cutoff date {cutoff_date.isoformat()} (7 days before sewing start on {sewing_start_date.isoformat()})."
            ),
            evidence={
                "cutoff_date": cutoff_date.isoformat(),
                "sewing_start_date": sewing_start_date.isoformat(),
                "total_trims_checked": len(trim_requirements),
                "shortages_count": 0,
            },
        )

    # Determine severity
    is_critical = False
    total_deficit = Decimal("0.000")
    for s in shortages:
        total_deficit += Decimal(str(s["deficit_qty"]))
        if today > cutoff_date or (float(str(s["deficit_percentage"])) > 50.0):
            is_critical = True

    severity = RiskSeverity.CRITICAL if is_critical else RiskSeverity.HIGH
    shortage_names = ", ".join(str(s["component_name"]) for s in shortages[:3])
    if len(shortages) > 3:
        shortage_names += f" and {len(shortages) - 3} others"

    headline = (
        f"Critical trim shortage: {len(shortages)} component(s) missing before sewing cutoff ({shortage_names})"
        if severity == RiskSeverity.CRITICAL
        else f"Trim shortage warning: {len(shortages)} component(s) delayed ({shortage_names})"
    )

    explanation = (
        f"{len(shortages)} trim component(s) do not have sufficient stock arriving before the cutoff date "
        f"{cutoff_date.isoformat()} (7 days prior to sewing start {sewing_start_date.isoformat()}). "
        f"Missing: {shortage_names}."
    )

    return RiskAssessment(
        rule="R2",
        rule_name="Trim & Accessory Shortage",
        order_id=order_id,
        order_number=order_number,
        buyer_name=buyer_name,
        triggered=True,
        severity=severity,
        deficit_qty=total_deficit,
        days_delayed=max(0, (today - cutoff_date).days) if today > cutoff_date else 0,
        headline=headline,
        explanation=explanation,
        evidence={
            "cutoff_date": cutoff_date.isoformat(),
            "sewing_start_date": sewing_start_date.isoformat(),
            "total_trims_checked": len(trim_requirements),
            "shortages_count": len(shortages),
            "shortages": shortages,
        },
    )


def evaluate_rule_r3(
    order_id: str,
    total_quantity: int,
    cumulative_sewn: int,
    recent_daily_outputs: list[int],
    target_sewing_end_date: date,
    order_number: str | None = None,
    buyer_name: str | None = None,
    today: date | None = None,
) -> RiskAssessment:
    """Evaluate Rule R3: Sewing Run-Rate Slippage.

    Deterministic logic:
    1. Calculate remaining garments: max(0, total_quantity - cumulative_sewn).
    2. If remaining == 0, order is completed (NORMAL).
    3. Calculate rolling daily output rate from recent days (average).
    4. Calculate calendar days remaining until target sewing completion.
    5. If past deadline and remaining > 0, trigger CRITICAL with past deadline evidence.
    6. If actual rate < required rate to finish on time, calculate projected completion date
       and trigger HIGH or CRITICAL based on projected overrun days.
    """
    if today is None:
        today = date.today()

    remaining_qty = max(0, total_quantity - cumulative_sewn)

    if remaining_qty == 0:
        return RiskAssessment(
            rule="R3",
            rule_name="Sewing Run-Rate Slippage",
            order_id=order_id,
            order_number=order_number,
            buyer_name=buyer_name,
            triggered=False,
            severity=RiskSeverity.NORMAL,
            deficit_qty=Decimal("0.0"),
            days_delayed=0,
            headline="Sewing stage completed: 100% of order quantity produced",
            explanation=f"Cumulative sewn output ({cumulative_sewn:,} pcs) satisfies total order volume ({total_quantity:,} pcs).",
            evidence={
                "total_quantity": total_quantity,
                "cumulative_sewn": cumulative_sewn,
                "remaining_qty": 0,
                "actual_daily_rate": 0.0,
                "required_daily_rate": 0.0,
                "target_sewing_end_date": target_sewing_end_date.isoformat(),
                "days_delayed": 0,
            },
        )

    # Days remaining until target
    days_remaining = (target_sewing_end_date - today).days

    # Calculate actual rolling daily rate
    if recent_daily_outputs:
        actual_daily_rate = sum(recent_daily_outputs) / len(recent_daily_outputs)
    else:
        actual_daily_rate = 0.0

    # Case A: Already past deadline with remaining unfinished quantity
    if days_remaining <= 0:
        days_delayed = abs(days_remaining)
        return RiskAssessment(
            rule="R3",
            rule_name="Sewing Run-Rate Slippage",
            order_id=order_id,
            order_number=order_number,
            buyer_name=buyer_name,
            triggered=True,
            severity=RiskSeverity.CRITICAL,
            deficit_qty=Decimal(str(remaining_qty)),
            days_delayed=days_delayed,
            headline=f"Critical sewing overrun: {remaining_qty:,} pcs unfinished past deadline",
            explanation=(
                f"Target sewing completion date was {target_sewing_end_date.isoformat()} ({days_delayed} days ago). "
                f"Still {remaining_qty:,} pcs remaining out of {total_quantity:,} pcs. Current rolling pace is {actual_daily_rate:.0f} pcs/day."
            ),
            evidence={
                "total_quantity": total_quantity,
                "cumulative_sewn": cumulative_sewn,
                "remaining_qty": remaining_qty,
                "actual_daily_rate": round(actual_daily_rate, 2),
                "required_daily_rate": float(remaining_qty),
                "target_sewing_end_date": target_sewing_end_date.isoformat(),
                "projected_completion_date": None,
                "days_delayed": days_delayed,
            },
        )

    # Case B: Future target date
    required_daily_rate = remaining_qty / days_remaining

    if actual_daily_rate > 0:
        projected_days_needed = math.ceil(remaining_qty / actual_daily_rate)
        projected_completion_date = today + timedelta(days=projected_days_needed)
        days_delayed = max(0, (projected_completion_date - target_sewing_end_date).days)
    else:
        projected_days_needed = 999
        projected_completion_date = None
        days_delayed = 999

    # Trigger threshold evaluation
    if days_delayed > 0 or (actual_daily_rate < required_daily_rate * 0.85):
        if days_delayed > 3 or actual_daily_rate < (required_daily_rate * 0.60) or days_delayed == 999:
            severity = RiskSeverity.CRITICAL
        else:
            severity = RiskSeverity.HIGH

        proj_str = (
            projected_completion_date.isoformat()
            if projected_completion_date
            else "Indefinite (Zero production output logged)"
        )
        headline = (
            f"Critical sewing pace slippage: projected completion {proj_str} ({days_delayed}d late)"
            if severity == RiskSeverity.CRITICAL
            else f"Sewing run-rate warning: pacing {actual_daily_rate:.0f} pcs/day vs {required_daily_rate:.0f} required"
        )
        explanation = (
            f"At current 3-day rolling run rate ({actual_daily_rate:.0f} pcs/day), order will complete on {proj_str}. "
            f"Target deadline is {target_sewing_end_date.isoformat()} ({days_remaining} days remaining). "
            f"A minimum pace of {required_daily_rate:.1f} pcs/day is strictly required to finish on schedule."
        )

        return RiskAssessment(
            rule="R3",
            rule_name="Sewing Run-Rate Slippage",
            order_id=order_id,
            order_number=order_number,
            buyer_name=buyer_name,
            triggered=True,
            severity=severity,
            deficit_qty=Decimal(str(remaining_qty)),
            days_delayed=days_delayed,
            headline=headline,
            explanation=explanation,
            evidence={
                "total_quantity": total_quantity,
                "cumulative_sewn": cumulative_sewn,
                "remaining_qty": remaining_qty,
                "days_remaining": days_remaining,
                "actual_daily_rate": round(actual_daily_rate, 2),
                "required_daily_rate": round(required_daily_rate, 2),
                "target_sewing_end_date": target_sewing_end_date.isoformat(),
                "projected_completion_date": projected_completion_date.isoformat() if projected_completion_date else None,
                "days_delayed": days_delayed,
            },
        )

    # Pacing is on schedule
    return RiskAssessment(
        rule="R3",
        rule_name="Sewing Run-Rate Slippage",
        order_id=order_id,
        order_number=order_number,
        buyer_name=buyer_name,
        triggered=False,
        severity=RiskSeverity.NORMAL,
        deficit_qty=Decimal("0.0"),
        days_delayed=0,
        headline=f"Sewing line pacing on target ({actual_daily_rate:.0f} pcs/day vs {required_daily_rate:.0f} required)",
        explanation=(
            f"Sewing pace ({actual_daily_rate:.0f} pcs/day) is sufficient to fulfill remaining {remaining_qty:,} pcs "
            f"before {target_sewing_end_date.isoformat()} ({days_remaining} days remaining)."
        ),
        evidence={
            "total_quantity": total_quantity,
            "cumulative_sewn": cumulative_sewn,
            "remaining_qty": remaining_qty,
            "days_remaining": days_remaining,
            "actual_daily_rate": round(actual_daily_rate, 2),
            "required_daily_rate": round(required_daily_rate, 2),
            "target_sewing_end_date": target_sewing_end_date.isoformat(),
            "projected_completion_date": projected_completion_date.isoformat() if projected_completion_date else None,
            "days_delayed": 0,
        },
    )


def evaluate_rule_r4(
    order_id: str,
    challans: list[dict[str, Any]],
    order_number: str | None = None,
    buyer_name: str | None = None,
    today: date | None = None,
) -> RiskAssessment:
    """Evaluate Rule R4: Outside Job-Work Delay & Loss Anomaly.

    Deterministic logic:
    1. Filter outward challans.
    2. Check open challans against expected return date. If overdue > 5 days -> CRITICAL; 1-5 days -> HIGH.
    3. Check received challans for process weight loss. If loss % > 3.5% (Tiruppur standard) -> trigger anomaly.
    """
    if today is None:
        today = date.today()

    if not challans:
        return RiskAssessment(
            rule="R4",
            rule_name="Job-Work Delay & Loss Anomaly",
            order_id=order_id,
            order_number=order_number,
            buyer_name=buyer_name,
            triggered=False,
            severity=RiskSeverity.NORMAL,
            deficit_qty=Decimal("0.0"),
            days_delayed=0,
            headline="No outside job-work dependencies or all lots in-house",
            explanation="All outside processing (dyeing, printing, washing) is reconciled with zero overdue challans.",
            evidence={"challans_count": 0, "overdue_count": 0, "anomalies_count": 0},
        )

    overdue_challans: list[dict[str, Any]] = []
    loss_anomalies: list[dict[str, Any]] = []

    for c in challans:
        status = c.get("status", "ISSUED")
        exp_date = c.get("expected_return_date")
        act_date = c.get("actual_return_date")

        # Check overdue open lot
        if status in ("ISSUED", "PARTIAL_RECEIVED") and not act_date and exp_date:
            if today > exp_date:
                delay = (today - exp_date).days
                overdue_challans.append({
                    "challan_number": c.get("challan_number"),
                    "process_name": c.get("process_name"),
                    "processor_name": c.get("processor_name"),
                    "expected_date": exp_date.isoformat() if isinstance(exp_date, date) else str(exp_date),
                    "days_overdue": delay,
                })

        # Check process weight loss
        issued_w = Decimal(str(c.get("issued_weight_kg", 0)))
        rec_w = Decimal(str(c.get("received_weight_kg", 0)))
        if issued_w > Decimal("0.0") and rec_w > Decimal("0.0"):
            loss_kg = issued_w - rec_w
            loss_pct = round((loss_kg / issued_w) * Decimal("100.0"), 2)
            if loss_pct > Decimal("3.50"):  # 3.5% threshold
                loss_anomalies.append({
                    "challan_number": c.get("challan_number"),
                    "process_name": c.get("process_name"),
                    "issued_kg": float(issued_w),
                    "received_kg": float(rec_w),
                    "loss_kg": float(loss_kg),
                    "loss_pct": float(loss_pct),
                })

    if not overdue_challans and not loss_anomalies:
        return RiskAssessment(
            rule="R4",
            rule_name="Job-Work Delay & Loss Anomaly",
            order_id=order_id,
            order_number=order_number,
            buyer_name=buyer_name,
            triggered=False,
            severity=RiskSeverity.NORMAL,
            deficit_qty=Decimal("0.0"),
            days_delayed=0,
            headline="Outside job-work operating within normal turnaround & loss thresholds",
            explanation=f"All {len(challans)} delivery challans are on schedule with process loss within allowable 3.5% limit.",
            evidence={"challans_count": len(challans), "overdue_count": 0, "anomalies_count": 0},
        )

    max_delay = max([c["days_overdue"] for c in overdue_challans], default=0)
    max_loss = max([c["loss_pct"] for c in loss_anomalies], default=0.0)

    if max_delay > 5 or max_loss > 5.0:
        severity = RiskSeverity.CRITICAL
    else:
        severity = RiskSeverity.HIGH

    reasons: list[str] = []
    if overdue_challans:
        reasons.append(f"{len(overdue_challans)} challan(s) overdue (up to {max_delay}d late)")
    if loss_anomalies:
        reasons.append(f"{len(loss_anomalies)} lot(s) exceeding normal weight loss (up to {max_loss:.1f}%)")

    headline = f"Job-work alert: {', '.join(reasons)}"
    explanation = (
        f"Outside vendor processing has flagged issues: {len(overdue_challans)} lot(s) past expected delivery date "
        f"and {len(loss_anomalies)} lot(s) showing unexplained weight shrinkage above standard 3.5% tolerance."
    )

    return RiskAssessment(
        rule="R4",
        rule_name="Job-Work Delay & Loss Anomaly",
        order_id=order_id,
        order_number=order_number,
        buyer_name=buyer_name,
        triggered=True,
        severity=severity,
        deficit_qty=Decimal(str(max_loss)),
        days_delayed=max_delay,
        headline=headline,
        explanation=explanation,
        evidence={
            "challans_count": len(challans),
            "overdue_count": len(overdue_challans),
            "overdue_challans": overdue_challans,
            "anomalies_count": len(loss_anomalies),
            "loss_anomalies": loss_anomalies,
        },
    )


def evaluate_rule_r5(
    order_id: str,
    milestones: list[dict[str, Any]],
    order_number: str | None = None,
    buyer_name: str | None = None,
    today: date | None = None,
) -> RiskAssessment:
    """Evaluate Rule R5: Critical Path Milestone Gate Slippage.

    Deterministic logic:
    1. Filter uncompleted milestones.
    2. Check planned dates vs today. If overdue > 5 days -> CRITICAL; 1-5 days -> HIGH; within 3 days approaching -> MEDIUM.
    """
    if today is None:
        today = date.today()

    overdue_gates: list[dict[str, Any]] = []
    approaching_gates: list[dict[str, Any]] = []

    for m in milestones:
        status = m.get("status", "PENDING")
        planned = m.get("planned_date")
        if status != "COMPLETED" and planned:
            if isinstance(planned, str):
                planned = date.fromisoformat(planned)
            diff = (today - planned).days
            if diff > 0:
                overdue_gates.append({
                    "name": m.get("name"),
                    "planned_date": planned.isoformat(),
                    "days_overdue": diff,
                    "status": status,
                })
            elif diff >= -3:
                approaching_gates.append({
                    "name": m.get("name"),
                    "planned_date": planned.isoformat(),
                    "days_remaining": abs(diff),
                })

    if not overdue_gates and not approaching_gates:
        return RiskAssessment(
            rule="R5",
            rule_name="Milestone Gate Slippage",
            order_id=order_id,
            order_number=order_number,
            buyer_name=buyer_name,
            triggered=False,
            severity=RiskSeverity.NORMAL,
            deficit_qty=Decimal("0.0"),
            days_delayed=0,
            headline="All critical path TNA milestone gates completed or on track",
            explanation="Pre-production approval gates (Fabric In-House, PP Sample, Cutting Start) are progressing on schedule.",
            evidence={"overdue_count": 0, "approaching_count": 0},
        )

    if overdue_gates:
        max_overdue = max(g["days_overdue"] for g in overdue_gates)
        critical_names = [g["name"] for g in overdue_gates]
        if max_overdue > 5:
            severity = RiskSeverity.CRITICAL
        else:
            severity = RiskSeverity.HIGH

        headline = f"Milestone gate breached: {critical_names[0]} overdue by {max_overdue} day(s)"
        explanation = (
            f"{len(overdue_gates)} TNA approval gate(s) have passed their scheduled calendar dates without completion. "
            f"Overdue gates: {', '.join(critical_names)}."
        )

        return RiskAssessment(
            rule="R5",
            rule_name="Milestone Gate Slippage",
            order_id=order_id,
            order_number=order_number,
            buyer_name=buyer_name,
            triggered=True,
            severity=severity,
            deficit_qty=Decimal(str(len(overdue_gates))),
            days_delayed=max_overdue,
            headline=headline,
            explanation=explanation,
            evidence={
                "overdue_count": len(overdue_gates),
                "overdue_gates": overdue_gates,
            },
        )

    # Approaching gate warning
    first_app = approaching_gates[0]
    return RiskAssessment(
        rule="R5",
        rule_name="Milestone Gate Slippage",
        order_id=order_id,
        order_number=order_number,
        buyer_name=buyer_name,
        triggered=True,
        severity=RiskSeverity.MEDIUM,
        deficit_qty=Decimal("0.0"),
        days_delayed=0,
        headline=f"Gate deadline approaching: {first_app['name']} due in {first_app['days_remaining']} day(s)",
        explanation=f"Critical path gate {first_app['name']} is scheduled for completion in {first_app['days_remaining']} day(s). Action required to prevent blockage.",
        evidence={
            "approaching_count": len(approaching_gates),
            "approaching_gates": approaching_gates,
        },
    )


def evaluate_rule_r6(
    order_id: str,
    order_status: str,
    last_activity_date: date | None,
    order_number: str | None = None,
    buyer_name: str | None = None,
    today: date | None = None,
) -> RiskAssessment:
    """Evaluate Rule R6: Order Inactivity / Stagnation.

    Deterministic logic:
    1. If order not active in production/confirmed, return NORMAL.
    2. If no floor logs, stock movements or challans logged for > 5 working days -> flag stagnation.
    """
    if today is None:
        today = date.today()

    if order_status not in ("CONFIRMED", "IN_PRODUCTION"):
        return RiskAssessment(
            rule="R6",
            rule_name="Order Stagnation / Inactivity",
            order_id=order_id,
            order_number=order_number,
            buyer_name=buyer_name,
            triggered=False,
            severity=RiskSeverity.NORMAL,
            deficit_qty=Decimal("0.0"),
            days_delayed=0,
            headline=f"Order in {order_status} state: inactivity rule inactive",
            explanation="Order is not in an active production state.",
            evidence={"order_status": order_status, "days_inactive": 0},
        )

    if last_activity_date is None:
        days_inactive = 10  # Never touched
    else:
        days_inactive = max(0, (today - last_activity_date).days)

    if days_inactive < 5:
        return RiskAssessment(
            rule="R6",
            rule_name="Order Stagnation / Inactivity",
            order_id=order_id,
            order_number=order_number,
            buyer_name=buyer_name,
            triggered=False,
            severity=RiskSeverity.NORMAL,
            deficit_qty=Decimal("0.0"),
            days_delayed=0,
            headline=f"Order actively updated (last touch {days_inactive}d ago)",
            explanation="Recent floor outputs or movement records indicate regular manufacturing progress.",
            evidence={"order_status": order_status, "days_inactive": days_inactive},
        )

    if days_inactive >= 7:
        severity = RiskSeverity.CRITICAL
    else:
        severity = RiskSeverity.HIGH

    headline = f"Order stagnation alert: zero recorded activity for {days_inactive} consecutive days"
    explanation = (
        f"Order is marked {order_status} but has had no floor outputs, stock issues, or challans logged for {days_inactive} days. "
        f"Immediate merchandiser audit required to verify line allocation."
    )

    return RiskAssessment(
        rule="R6",
        rule_name="Order Stagnation / Inactivity",
        order_id=order_id,
        order_number=order_number,
        buyer_name=buyer_name,
        triggered=True,
        severity=severity,
        deficit_qty=Decimal(str(days_inactive)),
        days_delayed=days_inactive,
        headline=headline,
        explanation=explanation,
        evidence={
            "order_status": order_status,
            "days_inactive": days_inactive,
            "last_activity_date": last_activity_date.isoformat() if last_activity_date else None,
        },
    )

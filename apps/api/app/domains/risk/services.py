import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.domains.jobwork.models import JobworkChallan
from app.domains.jobwork.services import JobworkService
from app.domains.materials.models import StockLedgerEntry
from app.domains.materials.services import MaterialService
from app.domains.orders.models import Order
from app.domains.production.models import DailyProductionLog
from app.domains.production.services import ProductionService
from app.domains.risk.rules import evaluate_rule_r5, evaluate_rule_r6
from app.domains.risk.schemas import OrderRiskSummary, RiskAssessment, RiskSeverity

SEVERITY_ORDER = {
    RiskSeverity.NORMAL: 0,
    RiskSeverity.LOW: 1,
    RiskSeverity.MEDIUM: 2,
    RiskSeverity.HIGH: 3,
    RiskSeverity.CRITICAL: 4,
}


class RiskControlService:
    """Unified Deterministic Risk Engine coordinating Rules R1 through R6."""

    @classmethod
    def evaluate_order_risk(
        cls, session: Session, tenant_id: str, order_id: uuid.UUID
    ) -> OrderRiskSummary:
        order = (
            session.execute(
                select(Order)
                .options(joinedload(Order.buyer), joinedload(Order.milestones))
                .where(Order.tenant_id == tenant_id, Order.id == order_id)
            )
            .unique()
            .scalar_one_or_none()
        )
        if not order:
            raise ValueError(f"Order {order_id} not found")

        buyer_name = order.buyer.name if order.buyer else "Direct Buyer"
        all_assessments: list[RiskAssessment] = []

        # 1 & 2. Material Risks (R1 & R2)
        try:
            mat_summaries = MaterialService.evaluate_order_material_risks(session, tenant_id)
            for ms in mat_summaries:
                if ms.order_id == str(order.id):
                    all_assessments.extend(ms.risks)
        except Exception:
            pass

        # 3. Production Pacing Risk (R3)
        try:
            r3 = ProductionService.evaluate_order_production_risk(session, tenant_id, order.id)
            all_assessments.append(r3)
        except Exception:
            pass

        # 4. Job-Work Anomaly Risk (R4)
        try:
            r4 = JobworkService.evaluate_order_jobwork_risk(session, tenant_id, order.id)
            all_assessments.append(r4)
        except Exception:
            pass

        # 5. Milestone Gate Slippage (R5)
        milestones_data = [
            {
                "name": m.name,
                "status": m.status,
                "planned_date": m.planned_date,
            }
            for m in order.milestones
        ]
        r5 = evaluate_rule_r5(
            order_id=str(order.id),
            milestones=milestones_data,
            order_number=order.order_number,
            buyer_name=buyer_name,
            today=date.today(),
        )
        all_assessments.append(r5)

        # 6. Order Stagnation (R6)
        last_activity = cls._get_latest_order_activity(session, tenant_id, order.id)
        if not last_activity and order.created_at:
            last_activity = order.created_at.date()

        r6 = evaluate_rule_r6(
            order_id=str(order.id),
            order_status=order.status,
            last_activity_date=last_activity,
            order_number=order.order_number,
            buyer_name=buyer_name,
            today=date.today(),
        )
        all_assessments.append(r6)

        # Compute max severity across all triggered assessments
        triggered_risks = [a for a in all_assessments if a.triggered]
        if triggered_risks:
            max_sev = max(
                (a.severity for a in triggered_risks),
                key=lambda s: SEVERITY_ORDER.get(s, 0),
            )
        else:
            max_sev = RiskSeverity.NORMAL

        return OrderRiskSummary(
            order_id=str(order.id),
            order_number=order.order_number,
            buyer_name=buyer_name,
            max_severity=max_sev,
            risks=all_assessments,
        )

    @classmethod
    def evaluate_all_risks(
        cls, session: Session, tenant_id: str
    ) -> list[OrderRiskSummary]:
        orders = (
            session.execute(
                select(Order)
                .options(joinedload(Order.buyer), joinedload(Order.milestones))
                .where(
                    Order.tenant_id == tenant_id,
                    Order.status.in_(["CONFIRMED", "IN_PRODUCTION"]),
                )
                .order_by(Order.ex_factory_date)
            )
            .unique()
            .scalars()
            .all()
        )

        summaries = []
        for order in orders:
            try:
                summary = cls.evaluate_order_risk(session, tenant_id, order.id)
                summaries.append(summary)
            except Exception:
                continue

        # Sort with most critical first
        summaries.sort(
            key=lambda s: SEVERITY_ORDER.get(s.max_severity, 0),
            reverse=True,
        )
        return summaries

    @staticmethod
    def _get_latest_order_activity(
        session: Session, tenant_id: str, order_id: uuid.UUID
    ) -> date | None:
        dates: list[date] = []

        # Latest floor log
        max_log = session.execute(
            select(func.max(DailyProductionLog.date)).where(
                DailyProductionLog.tenant_id == tenant_id,
                DailyProductionLog.order_id == order_id,
            )
        ).scalar()
        if max_log:
            dates.append(max_log)

        # Latest stock ledger entry
        max_stock = session.execute(
            select(func.max(StockLedgerEntry.created_at)).where(
                StockLedgerEntry.tenant_id == tenant_id,
                StockLedgerEntry.reference_id == str(order_id),
            )
        ).scalar()
        if max_stock:
            dates.append(max_stock.date())

        # Latest jobwork challan
        max_challan = session.execute(
            select(func.max(JobworkChallan.created_at)).where(
                JobworkChallan.tenant_id == tenant_id,
                JobworkChallan.order_id == order_id,
            )
        ).scalar()
        if max_challan:
            dates.append(max_challan.date())

        return max(dates) if dates else None

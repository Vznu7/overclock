import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, joinedload

from app.domains.audit.models import AuditAction, AuditLog
from app.domains.orders.models import Order
from app.domains.production.models import DailyProductionLog, ProductionLine
from app.domains.production.schemas import (
    DailyProductionLogCreate,
    DailyProductionLogResponse,
    OrderProductionSummary,
    ProductionLineCreate,
    ProductionLineResponse,
)
from app.domains.risk.rules import evaluate_rule_r3
from app.domains.risk.schemas import RiskAssessment


class ProductionService:
    @staticmethod
    def list_lines(session: Session, tenant_id: str) -> list[ProductionLineResponse]:
        stmt = (
            select(ProductionLine)
            .where(ProductionLine.tenant_id == tenant_id)
            .order_by(ProductionLine.line_number)
        )
        lines = session.execute(stmt).scalars().all()
        return [ProductionLineResponse.model_validate(line) for line in lines]

    @staticmethod
    def create_line(
        session: Session,
        tenant_id: str,
        data: ProductionLineCreate,
    ) -> ProductionLineResponse:
        line = ProductionLine(
            tenant_id=tenant_id,
            line_number=data.line_number,
            name=data.name,
            operator_count=data.operator_count,
            helper_count=data.helper_count,
            daily_working_hours=data.daily_working_hours,
            is_active=data.is_active,
        )
        session.add(line)
        session.commit()
        session.refresh(line)
        return ProductionLineResponse.model_validate(line)

    @classmethod
    def list_daily_logs(
        cls,
        session: Session,
        tenant_id: str,
        order_id: uuid.UUID | None = None,
        line_id: uuid.UUID | None = None,
        stage: str | None = None,
        limit: int = 100,
    ) -> list[DailyProductionLogResponse]:
        stmt = (
            select(DailyProductionLog)
            .where(DailyProductionLog.tenant_id == tenant_id)
            .order_by(desc(DailyProductionLog.date), desc(DailyProductionLog.created_at))
            .limit(limit)
        )
        if order_id:
            stmt = stmt.where(DailyProductionLog.order_id == order_id)
        if line_id:
            stmt = stmt.where(DailyProductionLog.line_id == line_id)
        if stage:
            stmt = stmt.where(DailyProductionLog.stage == stage)

        logs = session.execute(stmt).scalars().all()
        result = []
        for log in logs:
            resp = cls._build_log_response(session, log)
            result.append(resp)
        return result

    @classmethod
    def record_daily_log(
        cls,
        session: Session,
        tenant_id: str,
        user_id: uuid.UUID | None,
        data: DailyProductionLogCreate,
    ) -> DailyProductionLogResponse:
        order = session.execute(
            select(Order)
            .options(joinedload(Order.style))
            .where(Order.tenant_id == tenant_id, Order.id == data.order_id)
        ).scalar_one_or_none()
        if not order:
            raise ValueError(f"Order {data.order_id} not found")

        # Determine operators & hours defaults from line if not provided
        op_count = data.operator_count
        hours = data.working_hours
        if (op_count is None or hours is None) and data.line_id:
            line = session.execute(
                select(ProductionLine).where(
                    ProductionLine.tenant_id == tenant_id,
                    ProductionLine.id == data.line_id,
                )
            ).scalar_one_or_none()
            if line:
                if op_count is None:
                    op_count = line.operator_count
                if hours is None:
                    hours = line.daily_working_hours

        if op_count is None:
            op_count = 24
        if hours is None:
            hours = Decimal("8.00")

        log = DailyProductionLog(
            tenant_id=tenant_id,
            date=data.date,
            order_id=data.order_id,
            line_id=data.line_id,
            stage=data.stage.value,
            planned_output=data.planned_output,
            actual_output=data.actual_output,
            rejected_qty=data.rejected_qty,
            operator_count=op_count,
            working_hours=hours,
            notes=data.notes,
            created_by_user_id=user_id,
        )
        session.add(log)
        session.flush()

        # Audit log entry
        audit = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action=AuditAction.CREATE.value,
            entity_type="DAILY_PRODUCTION_LOG",
            entity_id=str(log.id),
            changes_json={
                "order_number": order.order_number,
                "stage": log.stage,
                "actual_output": log.actual_output,
                "date": log.date.isoformat(),
            },
        )
        session.add(audit)
        session.commit()
        session.refresh(log)

        return cls._build_log_response(session, log)

    @classmethod
    def _build_log_response(
        cls, session: Session, log: DailyProductionLog
    ) -> DailyProductionLogResponse:
        resp = DailyProductionLogResponse.model_validate(log)
        # Fetch Style SAM
        style_sam = Decimal("15.0")
        order = session.execute(
            select(Order)
            .options(joinedload(Order.style))
            .where(Order.id == log.order_id)
        ).scalar_one_or_none()
        if order and order.style and order.style.sam:
            style_sam = Decimal(str(order.style.sam))

        produced_min = Decimal(str(log.actual_output)) * style_sam
        available_min = Decimal(str(log.operator_count)) * Decimal(str(log.working_hours)) * Decimal("60.0")

        resp.produced_minutes = produced_min
        resp.available_minutes = available_min

        if available_min > Decimal("0.0"):
            resp.efficiency_pct = round((produced_min / available_min) * Decimal("100.0"), 2)
        else:
            resp.efficiency_pct = Decimal("0.0")

        if log.actual_output > 0:
            resp.rejection_rate_pct = round(
                (Decimal(str(log.rejected_qty)) / Decimal(str(log.actual_output))) * Decimal("100.0"),
                2,
            )
        else:
            resp.rejection_rate_pct = Decimal("0.0")

        return resp

    @classmethod
    def get_order_production_summary(
        cls, session: Session, tenant_id: str, order_id: uuid.UUID
    ) -> OrderProductionSummary:
        order = session.execute(
            select(Order).where(Order.tenant_id == tenant_id, Order.id == order_id)
        ).scalar_one_or_none()
        if not order:
            raise ValueError(f"Order {order_id} not found")

        # Sum cumulative output per stage
        stmt = (
            select(
                DailyProductionLog.stage,
                func.coalesce(func.sum(DailyProductionLog.actual_output), 0),
                func.coalesce(func.sum(DailyProductionLog.rejected_qty), 0),
            )
            .where(DailyProductionLog.tenant_id == tenant_id, DailyProductionLog.order_id == order_id)
            .group_by(DailyProductionLog.stage)
        )
        stage_sums = session.execute(stmt).all()
        stage_map = {row[0]: row[1] for row in stage_sums}
        total_rejected = sum(row[2] for row in stage_sums)

        cum_cutting = stage_map.get("CUTTING", 0)
        cum_sewing = stage_map.get("SEWING", 0)
        cum_finishing = stage_map.get("FINISHING", 0)
        remaining_sewing = max(0, order.total_quantity - cum_sewing)

        # Get recent daily sewing outputs for rolling rate
        recent_logs = (
            session.execute(
                select(DailyProductionLog.actual_output)
                .where(
                    DailyProductionLog.tenant_id == tenant_id,
                    DailyProductionLog.order_id == order_id,
                    DailyProductionLog.stage == "SEWING",
                )
                .order_by(desc(DailyProductionLog.date))
                .limit(5)
            )
            .scalars()
            .all()
        )
        if recent_logs:
            rolling_rate = round(Decimal(str(sum(recent_logs))) / Decimal(str(len(recent_logs))), 1)
        else:
            rolling_rate = Decimal("0.0")

        # Average efficiency across all logs
        logs = cls.list_daily_logs(session, tenant_id, order_id=order_id)
        if logs:
            eff_values = [log.efficiency_pct for log in logs if log.efficiency_pct > 0]
            avg_eff = round(sum(eff_values) / Decimal(str(len(eff_values))), 1) if eff_values else Decimal("0.0")
        else:
            avg_eff = Decimal("0.0")

        # Projected finish date
        if rolling_rate > Decimal("0.0") and remaining_sewing > 0:
            import math
            from datetime import timedelta
            days_needed = math.ceil(remaining_sewing / float(rolling_rate))
            proj_date = date.today() + timedelta(days=days_needed)
            is_on_track = proj_date <= order.ex_factory_date
        elif remaining_sewing == 0:
            proj_date = None
            is_on_track = True
        else:
            proj_date = None
            is_on_track = False

        return OrderProductionSummary(
            order_id=order.id,
            order_number=order.order_number,
            total_quantity=order.total_quantity,
            ex_factory_date=order.ex_factory_date,
            cumulative_cutting=cum_cutting,
            cumulative_sewing=cum_sewing,
            cumulative_finishing=cum_finishing,
            cumulative_rejected=total_rejected,
            remaining_sewing_qty=remaining_sewing,
            rolling_daily_rate=rolling_rate,
            avg_efficiency_pct=avg_eff,
            projected_finish_date=proj_date,
            is_on_track=is_on_track,
        )

    @classmethod
    def evaluate_order_production_risk(
        cls, session: Session, tenant_id: str, order_id: uuid.UUID
    ) -> RiskAssessment:
        order = session.execute(
            select(Order)
            .options(joinedload(Order.buyer), joinedload(Order.milestones))
            .where(Order.tenant_id == tenant_id, Order.id == order_id)
        ).unique().scalar_one_or_none()
        if not order:
            raise ValueError(f"Order {order_id} not found")

        # Find sewing target completion date from milestones or fallback to ex_factory - 3 days
        from datetime import timedelta
        sewing_target_date = order.ex_factory_date - timedelta(days=3)
        for m in order.milestones:
            if "sew" in m.name.lower() or "cutting" in m.name.lower():
                pass
            if "final" in m.name.lower() or "pack" in m.name.lower():
                sewing_target_date = m.planned_date - timedelta(days=2)
                break

        # Calculate cumulative sewn and recent outputs
        cum_sewn = (
            session.execute(
                select(func.coalesce(func.sum(DailyProductionLog.actual_output), 0)).where(
                    DailyProductionLog.tenant_id == tenant_id,
                    DailyProductionLog.order_id == order_id,
                    DailyProductionLog.stage == "SEWING",
                )
            ).scalar_one()
        )

        recent_outputs = (
            session.execute(
                select(DailyProductionLog.actual_output)
                .where(
                    DailyProductionLog.tenant_id == tenant_id,
                    DailyProductionLog.order_id == order_id,
                    DailyProductionLog.stage == "SEWING",
                )
                .order_by(desc(DailyProductionLog.date))
                .limit(5)
            )
            .scalars()
            .all()
        )

        buyer_name = order.buyer.name if order.buyer else "Direct Buyer"

        return evaluate_rule_r3(
            order_id=str(order.id),
            total_quantity=order.total_quantity,
            cumulative_sewn=int(cum_sewn),
            recent_daily_outputs=list(recent_outputs),
            target_sewing_end_date=sewing_target_date,
            order_number=order.order_number,
            buyer_name=buyer_name,
            today=date.today(),
        )

    @classmethod
    def evaluate_all_production_risks(
        cls, session: Session, tenant_id: str
    ) -> list[RiskAssessment]:
        orders = (
            session.execute(
                select(Order)
                .options(joinedload(Order.buyer), joinedload(Order.milestones))
                .where(
                    Order.tenant_id == tenant_id,
                    Order.status.in_(["IN_PRODUCTION", "CONFIRMED"]),
                )
            )
            .unique()
            .scalars()
            .all()
        )

        assessments = []
        for order in orders:
            ass = cls.evaluate_order_production_risk(session, tenant_id, order.id)
            assessments.append(ass)
        return assessments

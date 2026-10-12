import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, joinedload

from app.domains.audit.models import AuditAction, AuditLog
from app.domains.jobwork.models import (
    ChallanStatus,
    JobworkChallan,
    JobworkProcessor,
)
from app.domains.jobwork.schemas import (
    JobworkChallanCreate,
    JobworkChallanReceive,
    JobworkChallanResponse,
    JobworkProcessorCreate,
    JobworkProcessorResponse,
)
from app.domains.orders.models import Order
from app.domains.risk.rules import evaluate_rule_r4
from app.domains.risk.schemas import RiskAssessment


class JobworkService:
    @staticmethod
    def list_processors(session: Session, tenant_id: str) -> list[JobworkProcessorResponse]:
        stmt = (
            select(JobworkProcessor)
            .where(JobworkProcessor.tenant_id == tenant_id)
            .order_by(JobworkProcessor.name)
        )
        procs = session.execute(stmt).scalars().all()
        return [JobworkProcessorResponse.model_validate(p) for p in procs]

    @staticmethod
    def create_processor(
        session: Session,
        tenant_id: str,
        data: JobworkProcessorCreate,
    ) -> JobworkProcessorResponse:
        proc = JobworkProcessor(
            tenant_id=tenant_id,
            name=data.name,
            process_type=data.process_type.value,
            contact_person=data.contact_person,
            phone=data.phone,
            address=data.address,
            is_active=data.is_active,
        )
        session.add(proc)
        session.commit()
        session.refresh(proc)
        return JobworkProcessorResponse.model_validate(proc)

    @classmethod
    def list_challans(
        cls,
        session: Session,
        tenant_id: str,
        order_id: uuid.UUID | None = None,
        processor_id: uuid.UUID | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[JobworkChallanResponse]:
        stmt = (
            select(JobworkChallan)
            .options(joinedload(JobworkChallan.processor))
            .where(JobworkChallan.tenant_id == tenant_id)
            .order_by(desc(JobworkChallan.created_at))
            .limit(limit)
        )
        if order_id:
            stmt = stmt.where(JobworkChallan.order_id == order_id)
        if processor_id:
            stmt = stmt.where(JobworkChallan.processor_id == processor_id)
        if status:
            stmt = stmt.where(JobworkChallan.status == status)

        challans = session.execute(stmt).scalars().all()
        return [cls._build_challan_response(c) for c in challans]

    @classmethod
    def issue_challan(
        cls,
        session: Session,
        tenant_id: str,
        user_id: uuid.UUID | None,
        data: JobworkChallanCreate,
    ) -> JobworkChallanResponse:
        proc = session.execute(
            select(JobworkProcessor).where(
                JobworkProcessor.tenant_id == tenant_id,
                JobworkProcessor.id == data.processor_id,
            )
        ).scalar_one_or_none()
        if not proc:
            raise ValueError(f"Processor {data.processor_id} not found")

        challan = JobworkChallan(
            tenant_id=tenant_id,
            challan_number=data.challan_number,
            challan_type=data.challan_type.value,
            processor_id=data.processor_id,
            order_id=data.order_id,
            process_name=data.process_name,
            material_description=data.material_description,
            issued_qty=data.issued_qty,
            issued_weight_kg=data.issued_weight_kg,
            expected_return_date=data.expected_return_date,
            status=ChallanStatus.ISSUED.value,
            notes=data.notes,
        )
        session.add(challan)
        session.flush()

        audit = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action=AuditAction.CREATE.value,
            entity_type="JOBWORK_CHALLAN",
            entity_id=str(challan.id),
            changes_json={
                "challan_number": challan.challan_number,
                "processor": proc.name,
                "weight_kg": str(challan.issued_weight_kg),
            },
        )
        session.add(audit)
        session.commit()
        session.refresh(challan)

        return cls._build_challan_response(challan)

    @classmethod
    def receive_challan(
        cls,
        session: Session,
        tenant_id: str,
        user_id: uuid.UUID | None,
        challan_id: uuid.UUID,
        data: JobworkChallanReceive,
    ) -> JobworkChallanResponse:
        challan = session.execute(
            select(JobworkChallan)
            .options(joinedload(JobworkChallan.processor))
            .where(JobworkChallan.tenant_id == tenant_id, JobworkChallan.id == challan_id)
        ).scalar_one_or_none()
        if not challan:
            raise ValueError(f"Challan {challan_id} not found")

        challan.received_qty = data.received_qty
        challan.received_weight_kg = data.received_weight_kg
        challan.actual_return_date = data.actual_return_date or date.today()
        if data.notes:
            challan.notes = f"{challan.notes or ''} | {data.notes}".strip(" |")

        # Update status
        if challan.received_weight_kg >= (challan.issued_weight_kg * Decimal("0.90")):
            challan.status = ChallanStatus.COMPLETED.value
        else:
            challan.status = ChallanStatus.PARTIAL_RECEIVED.value

        audit = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action=AuditAction.UPDATE.value,
            entity_type="JOBWORK_CHALLAN",
            entity_id=str(challan.id),
            changes_json={
                "received_qty": str(challan.received_qty),
                "received_weight_kg": str(challan.received_weight_kg),
                "status": challan.status,
            },
        )
        session.add(audit)
        session.commit()
        session.refresh(challan)

        return cls._build_challan_response(challan)

    @classmethod
    def _build_challan_response(cls, c: JobworkChallan) -> JobworkChallanResponse:
        resp = JobworkChallanResponse.model_validate(c)
        resp.processor_name = c.processor.name if c.processor else "Unknown Vendor"

        issued_w = Decimal(str(c.issued_weight_kg))
        rec_w = Decimal(str(c.received_weight_kg))
        if issued_w > Decimal("0.0") and rec_w > Decimal("0.0"):
            loss_kg = max(Decimal("0.000"), issued_w - rec_w)
            loss_pct = round((loss_kg / issued_w) * Decimal("100.0"), 2)
            resp.weight_loss_kg = loss_kg
            resp.weight_loss_pct = loss_pct
            resp.is_loss_anomaly = loss_pct > Decimal("3.50")
        return resp

    @classmethod
    def evaluate_order_jobwork_risk(
        cls, session: Session, tenant_id: str, order_id: uuid.UUID
    ) -> RiskAssessment:
        order = session.execute(
            select(Order)
            .options(joinedload(Order.buyer))
            .where(Order.tenant_id == tenant_id, Order.id == order_id)
        ).scalar_one_or_none()
        if not order:
            raise ValueError(f"Order {order_id} not found")

        challans = session.execute(
            select(JobworkChallan)
            .options(joinedload(JobworkChallan.processor))
            .where(JobworkChallan.tenant_id == tenant_id, JobworkChallan.order_id == order_id)
        ).scalars().all()

        challans_data = [
            {
                "challan_number": c.challan_number,
                "process_name": c.process_name,
                "processor_name": c.processor.name if c.processor else "External Vendor",
                "status": c.status,
                "expected_return_date": c.expected_return_date,
                "actual_return_date": c.actual_return_date,
                "issued_weight_kg": float(c.issued_weight_kg),
                "received_weight_kg": float(c.received_weight_kg),
            }
            for c in challans
        ]

        buyer_name = order.buyer.name if order.buyer else "Direct Buyer"

        return evaluate_rule_r4(
            order_id=str(order.id),
            challans=challans_data,
            order_number=order.order_number,
            buyer_name=buyer_name,
            today=date.today(),
        )

    @classmethod
    def evaluate_all_jobwork_risks(
        cls, session: Session, tenant_id: str
    ) -> list[RiskAssessment]:
        orders = (
            session.execute(
                select(Order)
                .options(joinedload(Order.buyer))
                .where(
                    Order.tenant_id == tenant_id,
                    Order.status.in_(["IN_PRODUCTION", "CONFIRMED"]),
                )
            )
            .scalars()
            .all()
        )

        assessments = []
        for order in orders:
            ass = cls.evaluate_order_jobwork_risk(session, tenant_id, order.id)
            assessments.append(ass)
        return assessments

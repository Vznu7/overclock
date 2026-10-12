import uuid
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.domains.audit.models import AuditAction, AuditLog
from app.domains.materials.models import (
    Material,
    MaterialCategory,
    StockLedgerEntry,
    StockMovementType,
    StyleBom,
    Supplier,
    SupplierPo,
    SupplierPoStatus,
)
from app.domains.materials.schemas import (
    MaterialCreate,
    MaterialRead,
    MaterialUpdate,
    StockIssueCreate,
    StockReceiptCreate,
    StyleBomCreate,
    StyleBomRead,
    StyleBomRequirement,
    SupplierCreate,
    SupplierPoCreate,
    SupplierPoRead,
    SupplierRead,
)
from app.domains.orders.models import Order
from app.domains.risk.rules import evaluate_rule_r1, evaluate_rule_r2
from app.domains.risk.schemas import (
    InboundPoInput,
    OrderRiskSummary,
    RiskAssessment,
    RiskSeverity,
    TrimRequirementInput,
)


class MaterialService:
    @staticmethod
    def get_material_stock(session: Session, tenant_id: str, material_id: uuid.UUID) -> Decimal:
        """Calculate current available stock from immutable ledger."""
        stmt = select(func.coalesce(func.sum(StockLedgerEntry.quantity), Decimal("0.000"))).where(
            StockLedgerEntry.tenant_id == tenant_id,
            StockLedgerEntry.material_id == material_id,
        )
        result = session.execute(stmt).scalar_one_or_none()
        return Decimal(str(result)) if result is not None else Decimal("0.000")

    @classmethod
    def list_materials(
        cls,
        session: Session,
        tenant_id: str,
        category: MaterialCategory | None = None,
    ) -> list[MaterialRead]:
        """List materials with computed on-hand stock."""
        stmt = select(Material).where(Material.tenant_id == tenant_id)
        if category:
            stmt = stmt.where(Material.category == category)
        stmt = stmt.order_by(Material.code.asc())
        materials = session.execute(stmt).scalars().all()

        # Batch compute stock levels
        stock_stmt = (
            select(
                StockLedgerEntry.material_id,
                func.coalesce(func.sum(StockLedgerEntry.quantity), Decimal("0.000")).label("stock"),
            )
            .where(StockLedgerEntry.tenant_id == tenant_id)
            .group_by(StockLedgerEntry.material_id)
        )
        stock_map = {
            row.material_id: Decimal(str(row.stock)) for row in session.execute(stock_stmt)
        }

        result: list[MaterialRead] = []
        for m in materials:
            m_read = MaterialRead.model_validate(m)
            m_read.current_stock = stock_map.get(m.id, Decimal("0.000"))
            result.append(m_read)
        return result

    @classmethod
    def get_material(
        cls, session: Session, tenant_id: str, material_id: uuid.UUID
    ) -> MaterialRead | None:
        material = session.execute(
            select(Material).where(Material.tenant_id == tenant_id, Material.id == material_id)
        ).scalar_one_or_none()
        if not material:
            return None
        m_read = MaterialRead.model_validate(material)
        m_read.current_stock = cls.get_material_stock(session, tenant_id, material_id)
        return m_read

    @classmethod
    def create_material(
        cls,
        session: Session,
        tenant_id: str,
        data: MaterialCreate,
        user_id: uuid.UUID | None = None,
    ) -> MaterialRead:
        material = Material(
            tenant_id=tenant_id,
            code=data.code,
            name=data.name,
            category=data.category,
            unit_of_measure=data.unit_of_measure,
            minimum_stock_level=data.minimum_stock_level,
            unit_cost=data.unit_cost,
            currency=data.currency,
        )
        session.add(material)
        session.flush()

        audit = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action=AuditAction.CREATE.value,
            entity_type="MATERIAL",
            entity_id=str(material.id),
            changes_json={"code": material.code, "name": material.name},
        )
        session.add(audit)
        session.commit()
        session.refresh(material)

        m_read = MaterialRead.model_validate(material)
        m_read.current_stock = Decimal("0.000")
        return m_read

    @classmethod
    def update_material(
        cls,
        session: Session,
        tenant_id: str,
        material_id: uuid.UUID,
        data: MaterialUpdate,
        user_id: uuid.UUID | None = None,
    ) -> MaterialRead | None:
        material = session.execute(
            select(Material).where(Material.tenant_id == tenant_id, Material.id == material_id)
        ).scalar_one_or_none()
        if not material:
            return None

        update_dict = data.model_dump(exclude_unset=True)
        for k, v in update_dict.items():
            setattr(material, k, v)

        audit = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action=AuditAction.UPDATE.value,
            entity_type="MATERIAL",
            entity_id=str(material.id),
            changes_json=update_dict,
        )
        session.add(audit)
        session.commit()
        session.refresh(material)

        m_read = MaterialRead.model_validate(material)
        m_read.current_stock = cls.get_material_stock(session, tenant_id, material_id)
        return m_read

    # --- Style BOM Services ---
    @classmethod
    def list_style_bom(
        cls, session: Session, tenant_id: str, style_id: uuid.UUID
    ) -> list[StyleBomRead]:
        stmt = (
            select(StyleBom)
            .options(joinedload(StyleBom.material))
            .where(StyleBom.tenant_id == tenant_id, StyleBom.style_id == style_id)
            .order_by(StyleBom.component_name.asc())
        )
        boms = session.execute(stmt).scalars().all()
        return [StyleBomRead.model_validate(b) for b in boms]

    @classmethod
    def create_style_bom_item(
        cls,
        session: Session,
        tenant_id: str,
        style_id: uuid.UUID,
        data: StyleBomCreate,
        user_id: uuid.UUID | None = None,
    ) -> StyleBomRead:
        bom = StyleBom(
            tenant_id=tenant_id,
            style_id=style_id,
            material_id=data.material_id,
            component_name=data.component_name,
            consumption_per_piece=data.consumption_per_piece,
            wastage_percentage=data.wastage_percentage,
        )
        session.add(bom)
        session.flush()

        audit = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action=AuditAction.CREATE.value,
            entity_type="STYLE_BOM",
            entity_id=str(bom.id),
            changes_json={"style_id": str(style_id), "component": data.component_name},
        )
        session.add(audit)
        session.commit()
        session.refresh(bom)
        return StyleBomRead.model_validate(bom)

    @classmethod
    def calculate_order_bom_requirements(
        cls,
        session: Session,
        tenant_id: str,
        style_id: uuid.UUID,
        order_qty: int,
    ) -> list[StyleBomRequirement]:
        """Pure deterministic gross requirement calculator:

        gross_requirement = order_qty * consumption_per_piece * (1 + wastage_pct / 100)
        """
        stmt = (
            select(StyleBom)
            .options(joinedload(StyleBom.material))
            .where(StyleBom.tenant_id == tenant_id, StyleBom.style_id == style_id)
        )
        boms = session.execute(stmt).scalars().all()

        results: list[StyleBomRequirement] = []
        for bom in boms:
            mat = bom.material
            current_stock = cls.get_material_stock(session, tenant_id, mat.id)
            wastage_multiplier = Decimal("1.0") + (bom.wastage_percentage / Decimal("100.0"))
            gross = Decimal(str(order_qty)) * bom.consumption_per_piece * wastage_multiplier
            gross = gross.quantize(Decimal("0.001"))
            deficit = max(Decimal("0.000"), gross - current_stock)

            results.append(
                StyleBomRequirement(
                    component_name=bom.component_name,
                    material_id=mat.id,
                    material_code=mat.code,
                    material_name=mat.name,
                    unit_of_measure=mat.unit_of_measure.value
                    if hasattr(mat.unit_of_measure, "value")
                    else str(mat.unit_of_measure),
                    consumption_per_piece=bom.consumption_per_piece,
                    wastage_percentage=bom.wastage_percentage,
                    gross_requirement=gross,
                    available_stock=current_stock,
                    deficit=deficit,
                )
            )
        return results

    # --- Supplier Services ---
    @classmethod
    def list_suppliers(cls, session: Session, tenant_id: str) -> list[SupplierRead]:
        stmt = select(Supplier).where(Supplier.tenant_id == tenant_id).order_by(Supplier.name.asc())
        suppliers = session.execute(stmt).scalars().all()
        return [SupplierRead.model_validate(s) for s in suppliers]

    @classmethod
    def create_supplier(
        cls,
        session: Session,
        tenant_id: str,
        data: SupplierCreate,
        user_id: uuid.UUID | None = None,
    ) -> SupplierRead:
        supplier = Supplier(
            tenant_id=tenant_id,
            name=data.name,
            code=data.code,
            category=data.category,
            contact_email=data.contact_email,
            contact_phone=data.contact_phone,
            lead_time_days=data.lead_time_days,
        )
        session.add(supplier)
        session.flush()

        audit = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action=AuditAction.CREATE.value,
            entity_type="SUPPLIER",
            entity_id=str(supplier.id),
            changes_json={"name": supplier.name, "code": supplier.code},
        )
        session.add(audit)
        session.commit()
        session.refresh(supplier)
        return SupplierRead.model_validate(supplier)

    # --- Supplier Purchase Orders ---
    @classmethod
    def list_supplier_pos(cls, session: Session, tenant_id: str) -> list[SupplierPoRead]:
        stmt = (
            select(SupplierPo)
            .options(joinedload(SupplierPo.supplier), joinedload(SupplierPo.material))
            .where(SupplierPo.tenant_id == tenant_id)
            .order_by(SupplierPo.created_at.desc())
        )
        pos = session.execute(stmt).scalars().all()
        out: list[SupplierPoRead] = []
        for p in pos:
            read_item = SupplierPoRead.model_validate(p)
            read_item.supplier_name = p.supplier.name if p.supplier else None
            read_item.material_name = p.material.name if p.material else None
            out.append(read_item)
        return out

    @classmethod
    def create_supplier_po(
        cls,
        session: Session,
        tenant_id: str,
        data: SupplierPoCreate,
        user_id: uuid.UUID | None = None,
    ) -> SupplierPoRead:
        po = SupplierPo(
            tenant_id=tenant_id,
            po_number=data.po_number,
            supplier_id=data.supplier_id,
            material_id=data.material_id,
            order_id=data.order_id,
            quantity_ordered=data.quantity_ordered,
            quantity_received=Decimal("0.000"),
            unit_price=data.unit_price,
            expected_delivery_date=data.expected_delivery_date,
            status=SupplierPoStatus.PLACED,
        )
        session.add(po)
        session.flush()

        audit = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action=AuditAction.CREATE.value,
            entity_type="SUPPLIER_PO",
            entity_id=str(po.id),
            changes_json={"po_number": po.po_number, "quantity": str(po.quantity_ordered)},
        )
        session.add(audit)
        session.commit()
        session.refresh(po)
        return SupplierPoRead.model_validate(po)

    # --- Stock Movement Ledger Operations ---
    @classmethod
    def record_grn_receipt(
        cls,
        session: Session,
        tenant_id: str,
        data: StockReceiptCreate,
        user_id: uuid.UUID | None = None,
    ) -> StockLedgerEntry:
        """Store Keeper Goods Receipt Note (GRN):

        Atomic append to immutable ledger, updates Supplier PO if linked.
        """
        ref_type = "SUPPLIER_PO" if data.supplier_po_id else "DIRECT_INWARD"
        ref_id = str(data.supplier_po_id) if data.supplier_po_id else data.reference_id

        # Update supplier PO if present
        if data.supplier_po_id:
            po = session.execute(
                select(SupplierPo).where(
                    SupplierPo.tenant_id == tenant_id,
                    SupplierPo.id == data.supplier_po_id,
                )
            ).scalar_one_or_none()
            if po:
                po.quantity_received += data.quantity
                if po.quantity_received >= po.quantity_ordered:
                    po.status = SupplierPoStatus.COMPLETED
                else:
                    po.status = SupplierPoStatus.PARTIAL_RECEIVED

        entry = StockLedgerEntry(
            tenant_id=tenant_id,
            material_id=data.material_id,
            movement_type=StockMovementType.GRN_RECEIPT,
            quantity=data.quantity,
            unit_cost=data.unit_cost,
            reference_type=ref_type,
            reference_id=ref_id,
            notes=data.notes,
            created_by_user_id=user_id,
        )
        session.add(entry)
        session.flush()

        audit = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action=AuditAction.CREATE.value,
            entity_type="STOCK_LEDGER",
            entity_id=str(entry.id),
            changes_json={
                "type": "GRN_RECEIPT",
                "material_id": str(data.material_id),
                "quantity": str(data.quantity),
            },
        )
        session.add(audit)
        session.commit()
        session.refresh(entry)
        return entry

    @classmethod
    def record_stock_issue(
        cls,
        session: Session,
        tenant_id: str,
        data: StockIssueCreate,
        user_id: uuid.UUID | None = None,
    ) -> StockLedgerEntry:
        """Material Issue to Cutting Floor:

        Appends a negative quantity to the immutable stock ledger.
        """
        material = session.execute(
            select(Material).where(Material.tenant_id == tenant_id, Material.id == data.material_id)
        ).scalar_one_or_none()
        unit_cost = material.unit_cost if material else Decimal("0.00")

        entry = StockLedgerEntry(
            tenant_id=tenant_id,
            material_id=data.material_id,
            movement_type=StockMovementType.ISSUE_TO_CUTTING,
            quantity=-data.quantity,  # Negative for issue
            unit_cost=unit_cost,
            reference_type="ORDER" if data.order_id else "CUTTING_FLOOR",
            reference_id=str(data.order_id) if data.order_id else None,
            notes=data.notes,
            created_by_user_id=user_id,
        )
        session.add(entry)
        session.flush()

        audit = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action=AuditAction.CREATE.value,
            entity_type="STOCK_LEDGER",
            entity_id=str(entry.id),
            changes_json={
                "type": "ISSUE_TO_CUTTING",
                "material_id": str(data.material_id),
                "quantity": str(-data.quantity),
            },
        )
        session.add(audit)
        session.commit()
        session.refresh(entry)
        return entry

    @classmethod
    def list_stock_ledger(
        cls,
        session: Session,
        tenant_id: str,
        material_id: uuid.UUID | None = None,
        limit: int = 50,
    ) -> list[StockLedgerEntry]:
        stmt = (
            select(StockLedgerEntry)
            .where(StockLedgerEntry.tenant_id == tenant_id)
            .order_by(StockLedgerEntry.created_at.desc())
            .limit(limit)
        )
        if material_id:
            stmt = stmt.where(StockLedgerEntry.material_id == material_id)
        return list(session.execute(stmt).scalars().all())

    # --- Pure Deterministic Risk Evaluation for Active Orders ---
    @classmethod
    def evaluate_order_material_risks(
        cls,
        session: Session,
        tenant_id: str,
        today: date | None = None,
    ) -> list[OrderRiskSummary]:
        """Evaluates Rules R1 & R2 for all active orders in the tenant."""
        if today is None:
            today = date.today()

        # Load active orders
        order_stmt = (
            select(Order)
            .options(
                joinedload(Order.buyer),
                joinedload(Order.style),
                joinedload(Order.milestones),
            )
            .where(Order.tenant_id == tenant_id, Order.status.in_(["CONFIRMED", "IN_PRODUCTION"]))
        )
        orders = session.execute(order_stmt).scalars().unique().all()

        # Load all materials and current stocks
        all_materials = cls.list_materials(session, tenant_id)
        stock_lookup = {m.id: m.current_stock for m in all_materials}
        material_lookup = {m.id: m for m in all_materials}

        # Load all active supplier POs
        po_stmt = select(SupplierPo).where(
            SupplierPo.tenant_id == tenant_id,
            SupplierPo.status.in_(["PLACED", "PARTIAL_RECEIVED"]),
        )
        all_pos = session.execute(po_stmt).scalars().all()

        summaries: list[OrderRiskSummary] = []

        for order in orders:
            style_id = order.style_id
            buyer_name = order.buyer.name if order.buyer else "Unknown Buyer"

            # Get milestones: Fabric In-House and Sewing Start
            fabric_milestone = next(
                (m for m in order.milestones if "fabric" in m.name.lower()),
                None,
            )
            sewing_milestone = next(
                (m for m in order.milestones if "sewing" in m.name.lower()),
                None,
            )

            target_fabric_date = (
                fabric_milestone.planned_date
                if fabric_milestone
                else (order.ex_factory_date - timedelta(days=25))
            )
            sewing_start_date = (
                sewing_milestone.planned_date
                if sewing_milestone
                else (order.ex_factory_date - timedelta(days=15))
            )

            # Get BOM for style
            bom_items = (
                session.execute(
                    select(StyleBom).where(
                        StyleBom.tenant_id == tenant_id, StyleBom.style_id == style_id
                    )
                )
                .scalars()
                .all()
            )

            risks: list[RiskAssessment] = []

            # 1. Evaluate R1 for Fabric components
            fabric_boms = [
                b
                for b in bom_items
                if material_lookup.get(b.material_id)
                and material_lookup[b.material_id].category == MaterialCategory.FABRIC
            ]
            for f_bom in fabric_boms:
                mat = material_lookup[f_bom.material_id]
                wastage_mult = Decimal("1.0") + (f_bom.wastage_percentage / Decimal("100.0"))
                req_qty = (
                    Decimal(str(order.total_quantity)) * f_bom.consumption_per_piece * wastage_mult
                )
                cur_stock = stock_lookup.get(mat.id, Decimal("0.000"))

                # Inbound POs matching this material
                inbound_inputs = [
                    InboundPoInput(
                        po_number=p.po_number,
                        material_id=p.material_id,
                        quantity=(p.quantity_ordered - p.quantity_received),
                        expected_date=p.expected_delivery_date,
                        status=p.status.value if hasattr(p.status, "value") else str(p.status),
                    )
                    for p in all_pos
                    if p.material_id == mat.id
                ]

                r1_result = evaluate_rule_r1(
                    order_id=str(order.id),
                    order_number=order.order_number,
                    buyer_name=buyer_name,
                    target_fabric_date=target_fabric_date,
                    required_qty=req_qty,
                    current_stock=cur_stock,
                    inbound_pos=inbound_inputs,
                    today=today,
                )
                if r1_result.triggered:
                    risks.append(r1_result)

            # 2. Evaluate R2 for Trim components
            trim_boms = [
                b
                for b in bom_items
                if material_lookup.get(b.material_id)
                and material_lookup[b.material_id].category == MaterialCategory.TRIM
            ]
            trim_inputs: list[TrimRequirementInput] = []
            for t_bom in trim_boms:
                mat = material_lookup[t_bom.material_id]
                wastage_mult = Decimal("1.0") + (t_bom.wastage_percentage / Decimal("100.0"))
                req_qty = (
                    Decimal(str(order.total_quantity)) * t_bom.consumption_per_piece * wastage_mult
                )
                cur_stock = stock_lookup.get(mat.id, Decimal("0.000"))

                t_pos = [
                    InboundPoInput(
                        po_number=p.po_number,
                        material_id=p.material_id,
                        quantity=(p.quantity_ordered - p.quantity_received),
                        expected_date=p.expected_delivery_date,
                        status=p.status.value if hasattr(p.status, "value") else str(p.status),
                    )
                    for p in all_pos
                    if p.material_id == mat.id
                ]

                trim_inputs.append(
                    TrimRequirementInput(
                        material_id=mat.id,
                        material_code=mat.code,
                        material_name=mat.name,
                        component_name=t_bom.component_name,
                        required_qty=req_qty,
                        current_stock=cur_stock,
                        inbound_pos=t_pos,
                    )
                )

            if trim_inputs:
                r2_result = evaluate_rule_r2(
                    order_id=str(order.id),
                    order_number=order.order_number,
                    buyer_name=buyer_name,
                    sewing_start_date=sewing_start_date,
                    trim_requirements=trim_inputs,
                    today=today,
                )
                if r2_result.triggered:
                    risks.append(r2_result)

            max_sev = RiskSeverity.NORMAL
            for r in risks:
                if r.severity == RiskSeverity.CRITICAL:
                    max_sev = RiskSeverity.CRITICAL
                    break
                elif r.severity == RiskSeverity.HIGH and max_sev != RiskSeverity.CRITICAL:
                    max_sev = RiskSeverity.HIGH

            summaries.append(
                OrderRiskSummary(
                    order_id=str(order.id),
                    order_number=order.order_number,
                    buyer_name=buyer_name,
                    max_severity=max_sev,
                    risks=risks,
                )
            )

        return summaries

import uuid
from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, log_audit_event, require_roles
from app.domains.audit.models import AuditAction
from app.domains.auth.models import User, UserRole
from app.domains.orders.extractor import parse_po_document
from app.domains.orders.importer import export_orders_to_csv, import_orders_csv
from app.domains.orders.models import Buyer, Order, OrderLine, OrderMilestone, Style
from app.domains.orders.schemas import (
    BuyerCreate,
    BuyerRead,
    CsvImportSummary,
    OrderCreate,
    OrderMilestoneRead,
    OrderMilestoneUpdate,
    OrderRead,
    OrderUpdate,
    PoExtractionResult,
    StyleCreate,
    StyleRead,
)

router = APIRouter(tags=["Orders & Merchandising"])


# --- Buyers ---
@router.get("/buyers", response_model=list[BuyerRead], summary="List Buyers")
def list_buyers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Buyer]:
    return (
        db.query(Buyer)
        .filter(Buyer.tenant_id == current_user.tenant_id)
        .order_by(Buyer.name.asc())
        .all()
    )


@router.post(
    "/buyers",
    response_model=BuyerRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create Buyer",
    dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.MERCHANDISER))],
)
def create_buyer(
    payload: BuyerCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Buyer:
    buyer = Buyer(
        id=uuid.uuid4(),
        tenant_id=current_user.tenant_id,
        name=payload.name,
        code=payload.code.upper(),
        country=payload.country,
        contact_email=payload.contact_email,
        payment_terms=payload.payment_terms,
    )
    db.add(buyer)
    db.flush()

    log_audit_event(
        db=db,
        tenant_id=current_user.tenant_id,
        entity_type="buyer",
        entity_id=str(buyer.id),
        action=AuditAction.CREATE,
        user_id=current_user.id,
        changes={"name": buyer.name, "code": buyer.code},
        request=request,
    )
    db.commit()
    db.refresh(buyer)
    return buyer


# --- Styles ---
@router.get("/styles", response_model=list[StyleRead], summary="List Styles")
def list_styles(
    buyer_id: uuid.UUID | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Style]:
    query = db.query(Style).filter(Style.tenant_id == current_user.tenant_id)
    if buyer_id:
        query = query.filter(Style.buyer_id == buyer_id)
    return query.order_by(Style.style_number.asc()).all()


@router.post(
    "/styles",
    response_model=StyleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create Style",
    dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.MERCHANDISER))],
)
def create_style(
    payload: StyleCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Style:
    # Verify buyer exists under tenant
    buyer = (
        db.query(Buyer)
        .filter(Buyer.tenant_id == current_user.tenant_id, Buyer.id == payload.buyer_id)
        .first()
    )
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")

    style = Style(
        id=uuid.uuid4(),
        tenant_id=current_user.tenant_id,
        buyer_id=buyer.id,
        style_number=payload.style_number,
        style_name=payload.style_name,
        garment_type=payload.garment_type,
        sam=payload.sam,
        target_efficiency=payload.target_efficiency,
    )
    db.add(style)
    db.flush()

    log_audit_event(
        db=db,
        tenant_id=current_user.tenant_id,
        entity_type="style",
        entity_id=str(style.id),
        action=AuditAction.CREATE,
        user_id=current_user.id,
        changes={"style_number": style.style_number, "sam": float(style.sam)},
        request=request,
    )
    db.commit()
    db.refresh(style)
    return style


# --- Orders ---
@router.get("/orders", response_model=list[OrderRead], summary="List Orders")
def list_orders(
    buyer_id: uuid.UUID | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    search: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Order]:
    query = db.query(Order).filter(Order.tenant_id == current_user.tenant_id)
    if buyer_id:
        query = query.filter(Order.buyer_id == buyer_id)
    if status_filter:
        query = query.filter(Order.status == status_filter)
    if search:
        query = query.filter(Order.order_number.ilike(f"%{search}%"))

    return query.order_by(Order.ex_factory_date.asc()).offset(offset).limit(limit).all()


@router.post(
    "/orders",
    response_model=OrderRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create Order",
    dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.MERCHANDISER))],
)
def create_order(
    payload: OrderCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Order:
    # Check duplicate order number in tenant
    existing = (
        db.query(Order)
        .filter(
            Order.tenant_id == current_user.tenant_id, Order.order_number == payload.order_number
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=409, detail=f"Order '{payload.order_number}' already exists"
        )

    order = Order(
        id=uuid.uuid4(),
        tenant_id=current_user.tenant_id,
        buyer_id=payload.buyer_id,
        style_id=payload.style_id,
        order_number=payload.order_number,
        total_quantity=payload.total_quantity,
        unit_price=payload.unit_price,
        currency=payload.currency,
        ex_factory_date=payload.ex_factory_date,
        planned_sewing_start=payload.planned_sewing_start,
        status=payload.status.value,
        notes=payload.notes,
    )
    db.add(order)
    db.flush()

    for line_in in payload.lines:
        line = OrderLine(
            id=uuid.uuid4(),
            tenant_id=current_user.tenant_id,
            order_id=order.id,
            color=line_in.color,
            size=line_in.size,
            quantity=line_in.quantity,
        )
        db.add(line)

    log_audit_event(
        db=db,
        tenant_id=current_user.tenant_id,
        entity_type="order",
        entity_id=str(order.id),
        action=AuditAction.CREATE,
        user_id=current_user.id,
        changes={"order_number": order.order_number, "qty": order.total_quantity},
        request=request,
    )
    db.commit()
    db.refresh(order)
    return order


@router.get("/orders/{order_id}", response_model=OrderRead, summary="Get Order by ID")
def get_order(
    order_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Order:
    order = (
        db.query(Order)
        .filter(Order.tenant_id == current_user.tenant_id, Order.id == order_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.patch(
    "/orders/{order_id}",
    response_model=OrderRead,
    summary="Update Order",
    dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.MERCHANDISER))],
)
def update_order(
    order_id: uuid.UUID,
    payload: OrderUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Order:
    order = (
        db.query(Order)
        .filter(Order.tenant_id == current_user.tenant_id, Order.id == order_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    changes: dict[str, Any] = {}
    if payload.total_quantity is not None:
        changes["total_quantity"] = payload.total_quantity
        order.total_quantity = payload.total_quantity
    if payload.unit_price is not None:
        changes["unit_price"] = float(payload.unit_price)
        order.unit_price = payload.unit_price
    if payload.ex_factory_date is not None:
        changes["ex_factory_date"] = str(payload.ex_factory_date)
        order.ex_factory_date = payload.ex_factory_date
    if payload.planned_sewing_start is not None:
        changes["planned_sewing_start"] = str(payload.planned_sewing_start)
        order.planned_sewing_start = payload.planned_sewing_start
    if payload.status is not None:
        changes["status"] = payload.status.value
        order.status = payload.status.value
    if payload.notes is not None:
        order.notes = payload.notes

    if changes:
        log_audit_event(
            db=db,
            tenant_id=current_user.tenant_id,
            entity_type="order",
            entity_id=str(order.id),
            action=AuditAction.UPDATE,
            user_id=current_user.id,
            changes=changes,
            request=request,
        )
        db.commit()
        db.refresh(order)

    return order


# --- Milestone Updates ---
@router.patch(
    "/orders/{order_id}/milestones/{milestone_id}",
    response_model=OrderMilestoneRead,
    summary="Update Order Milestone",
    dependencies=[
        Depends(require_roles(UserRole.OWNER, UserRole.MERCHANDISER, UserRole.PRODUCTION_MANAGER))
    ],
)
def update_milestone(
    order_id: uuid.UUID,
    milestone_id: uuid.UUID,
    payload: OrderMilestoneUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrderMilestone:
    milestone = (
        db.query(OrderMilestone)
        .filter(
            OrderMilestone.tenant_id == current_user.tenant_id,
            OrderMilestone.order_id == order_id,
            OrderMilestone.id == milestone_id,
        )
        .first()
    )
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")

    changes: dict[str, Any] = {}
    if payload.planned_date is not None:
        changes["planned_date"] = str(payload.planned_date)
        milestone.planned_date = payload.planned_date
    if payload.actual_date is not None:
        changes["actual_date"] = str(payload.actual_date)
        milestone.actual_date = payload.actual_date
    if payload.status is not None:
        changes["status"] = payload.status.value
        milestone.status = payload.status.value
    if payload.notes is not None:
        milestone.notes = payload.notes

    if changes:
        log_audit_event(
            db=db,
            tenant_id=current_user.tenant_id,
            entity_type="order_milestone",
            entity_id=str(milestone.id),
            action=AuditAction.UPDATE,
            user_id=current_user.id,
            changes=changes,
            request=request,
        )
        db.commit()
        db.refresh(milestone)

    return milestone


# --- CSV Import & Export ---
@router.post(
    "/orders/import/csv",
    response_model=CsvImportSummary,
    summary="Bulk Import Orders from CSV",
    dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.MERCHANDISER))],
)
async def import_orders(
    file: UploadFile = File(...),
    strict: bool = Query(False, description="Fail entire import if any row is invalid"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CsvImportSummary:
    content = await file.read()
    if len(content) > 15 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File exceeds 15 MB limit")

    summary = import_orders_csv(
        db=db, tenant_id=current_user.tenant_id, content_bytes=content, strict=strict
    )
    return summary


@router.get("/orders/export/csv", summary="Export All Orders to CSV")
def export_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    csv_text = export_orders_to_csv(db=db, tenant_id=current_user.tenant_id)
    filename = f"orders_{current_user.tenant_id}.csv"
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# --- AI / Layout PO Extraction ---
@router.post(
    "/orders/extract-po",
    response_model=PoExtractionResult,
    summary="Extract Draft Order from Buyer Purchase Order",
    dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.MERCHANDISER))],
)
async def extract_po(
    file: UploadFile | None = File(None),
    sample_id: str | None = Query(None, description="Preset sample PO ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PoExtractionResult:
    pdf_bytes: bytes | None = None
    if file:
        pdf_bytes = await file.read()
        if len(pdf_bytes) > 15 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File exceeds 15 MB limit")

    return parse_po_document(
        db=db,
        tenant_id=current_user.tenant_id,
        pdf_bytes=pdf_bytes,
        sample_id=sample_id,
    )


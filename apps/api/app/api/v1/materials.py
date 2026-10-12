import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.domains.auth.models import User, UserRole
from app.domains.materials.models import MaterialCategory
from app.domains.materials.schemas import (
    MaterialCreate,
    MaterialRead,
    MaterialUpdate,
    StockIssueCreate,
    StockLedgerEntryRead,
    StockReceiptCreate,
    StyleBomCreate,
    StyleBomRead,
    StyleBomRequirement,
    SupplierCreate,
    SupplierPoCreate,
    SupplierPoRead,
    SupplierRead,
)
from app.domains.materials.services import MaterialService
from app.domains.risk.schemas import OrderRiskSummary

router = APIRouter(tags=["Materials, Stock & Risk Rules"])


# --- Materials Catalog ---
@router.get(
    "/materials", response_model=list[MaterialRead], summary="List materials with on-hand stock"
)
def list_materials(
    category: MaterialCategory | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[MaterialRead]:
    return MaterialService.list_materials(db, current_user.tenant_id, category=category)


@router.post(
    "/materials",
    response_model=MaterialRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create new material",
)
def create_material(
    payload: MaterialCreate,
    current_user: User = Depends(
        require_roles(UserRole.OWNER, UserRole.MERCHANDISER, UserRole.STORE_KEEPER)
    ),
    db: Session = Depends(get_db),
) -> MaterialRead:
    return MaterialService.create_material(
        db, current_user.tenant_id, payload, user_id=current_user.id
    )


@router.get("/materials/{material_id}", response_model=MaterialRead, summary="Get material details")
def get_material(
    material_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MaterialRead:
    mat = MaterialService.get_material(db, current_user.tenant_id, material_id)
    if not mat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material not found")
    return mat


@router.put("/materials/{material_id}", response_model=MaterialRead, summary="Update material")
def update_material(
    material_id: uuid.UUID,
    payload: MaterialUpdate,
    current_user: User = Depends(
        require_roles(UserRole.OWNER, UserRole.MERCHANDISER, UserRole.STORE_KEEPER)
    ),
    db: Session = Depends(get_db),
) -> MaterialRead:
    mat = MaterialService.update_material(
        db, current_user.tenant_id, material_id, payload, user_id=current_user.id
    )
    if not mat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material not found")
    return mat


# --- Style BOM Formulas ---
@router.get(
    "/styles/{style_id}/bom", response_model=list[StyleBomRead], summary="List Style BOM formulas"
)
def list_style_bom(
    style_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[StyleBomRead]:
    return MaterialService.list_style_bom(db, current_user.tenant_id, style_id)


@router.post(
    "/styles/{style_id}/bom",
    response_model=StyleBomRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add BOM formula item to style",
)
def create_style_bom(
    style_id: uuid.UUID,
    payload: StyleBomCreate,
    current_user: User = Depends(require_roles(UserRole.OWNER, UserRole.MERCHANDISER)),
    db: Session = Depends(get_db),
) -> StyleBomRead:
    return MaterialService.create_style_bom_item(
        db, current_user.tenant_id, style_id, payload, user_id=current_user.id
    )


@router.get(
    "/styles/{style_id}/bom/calculate",
    response_model=list[StyleBomRequirement],
    summary="Calculate gross BOM requirement for an order quantity",
)
def calculate_bom_requirement(
    style_id: uuid.UUID,
    order_qty: int = Query(..., gt=0, description="Order quantity in pieces"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[StyleBomRequirement]:
    return MaterialService.calculate_order_bom_requirements(
        db, current_user.tenant_id, style_id, order_qty
    )


# --- Suppliers ---
@router.get("/suppliers", response_model=list[SupplierRead], summary="List suppliers")
def list_suppliers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[SupplierRead]:
    return MaterialService.list_suppliers(db, current_user.tenant_id)


@router.post(
    "/suppliers",
    response_model=SupplierRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register new supplier",
)
def create_supplier(
    payload: SupplierCreate,
    current_user: User = Depends(
        require_roles(UserRole.OWNER, UserRole.MERCHANDISER, UserRole.STORE_KEEPER)
    ),
    db: Session = Depends(get_db),
) -> SupplierRead:
    return MaterialService.create_supplier(
        db, current_user.tenant_id, payload, user_id=current_user.id
    )


# --- Supplier Inbound Purchase Orders ---
@router.get(
    "/supplier-pos", response_model=list[SupplierPoRead], summary="List inbound supplier POs"
)
def list_supplier_pos(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[SupplierPoRead]:
    return MaterialService.list_supplier_pos(db, current_user.tenant_id)


@router.post(
    "/supplier-pos",
    response_model=SupplierPoRead,
    status_code=status.HTTP_201_CREATED,
    summary="Place new supplier PO",
)
def create_supplier_po(
    payload: SupplierPoCreate,
    current_user: User = Depends(require_roles(UserRole.OWNER, UserRole.MERCHANDISER)),
    db: Session = Depends(get_db),
) -> SupplierPoRead:
    return MaterialService.create_supplier_po(
        db, current_user.tenant_id, payload, user_id=current_user.id
    )


# --- Stock Movement Ledger Operations ---
@router.post(
    "/stock/receive",
    response_model=StockLedgerEntryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Goods Receipt Note (GRN) posting to stock ledger",
)
def receive_stock_grn(
    payload: StockReceiptCreate,
    current_user: User = Depends(
        require_roles(UserRole.OWNER, UserRole.STORE_KEEPER, UserRole.MERCHANDISER)
    ),
    db: Session = Depends(get_db),
) -> Any:
    return MaterialService.record_grn_receipt(
        db, current_user.tenant_id, payload, user_id=current_user.id
    )


@router.post(
    "/stock/issue",
    response_model=StockLedgerEntryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Issue materials to cutting floor",
)
def issue_stock_to_cutting(
    payload: StockIssueCreate,
    current_user: User = Depends(
        require_roles(UserRole.OWNER, UserRole.STORE_KEEPER, UserRole.PRODUCTION_MANAGER)
    ),
    db: Session = Depends(get_db),
) -> Any:
    return MaterialService.record_stock_issue(
        db, current_user.tenant_id, payload, user_id=current_user.id
    )


@router.get(
    "/stock/ledger",
    response_model=list[StockLedgerEntryRead],
    summary="Get immutable stock ledger movements",
)
def list_stock_ledger(
    material_id: uuid.UUID | None = None,
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[StockLedgerEntryRead]:
    entries = MaterialService.list_stock_ledger(
        db, current_user.tenant_id, material_id=material_id, limit=limit
    )
    return [StockLedgerEntryRead.model_validate(e) for e in entries]


# --- Deterministic Risk Rules R1 & R2 ---
@router.get(
    "/risk/materials",
    response_model=list[OrderRiskSummary],
    summary="Deterministic risk evaluation (R1 fabric deficit & R2 trim shortage) for active orders",
)
def evaluate_order_risks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[OrderRiskSummary]:
    return MaterialService.evaluate_order_material_risks(db, current_user.tenant_id)

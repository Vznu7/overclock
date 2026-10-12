import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.domains.materials.models import (
    MaterialCategory,
    StockMovementType,
    SupplierCategory,
    SupplierPoStatus,
    UnitOfMeasure,
)


# --- Material Schemas ---
class MaterialBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=64)
    name: str = Field(..., min_length=2, max_length=255)
    category: MaterialCategory = Field(default=MaterialCategory.FABRIC)
    unit_of_measure: UnitOfMeasure = Field(default=UnitOfMeasure.KG)
    minimum_stock_level: Decimal = Field(default=Decimal("0.000"), ge=0)
    unit_cost: Decimal = Field(default=Decimal("0.00"), ge=0)
    currency: str = Field(default="INR", max_length=8)


class MaterialCreate(MaterialBase):
    pass


class MaterialUpdate(BaseModel):
    name: str | None = None
    category: MaterialCategory | None = None
    unit_of_measure: UnitOfMeasure | None = None
    minimum_stock_level: Decimal | None = None
    unit_cost: Decimal | None = None
    currency: str | None = None


class MaterialRead(MaterialBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: str
    current_stock: Decimal = Decimal("0.000")
    created_at: datetime
    updated_at: datetime


# --- Style BOM Schemas ---
class StyleBomBase(BaseModel):
    component_name: str = Field(..., min_length=2, max_length=64)
    consumption_per_piece: Decimal = Field(..., gt=0)
    wastage_percentage: Decimal = Field(default=Decimal("5.00"), ge=0, le=100)


class StyleBomCreate(StyleBomBase):
    material_id: uuid.UUID


class StyleBomRead(StyleBomBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: str
    style_id: uuid.UUID
    material_id: uuid.UUID
    material: MaterialRead | None = None
    created_at: datetime
    updated_at: datetime


class StyleBomRequirement(BaseModel):
    component_name: str
    material_id: uuid.UUID
    material_code: str
    material_name: str
    unit_of_measure: str
    consumption_per_piece: Decimal
    wastage_percentage: Decimal
    gross_requirement: Decimal
    available_stock: Decimal
    deficit: Decimal


# --- Supplier Schemas ---
class SupplierBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    code: str = Field(..., min_length=2, max_length=32)
    category: SupplierCategory = Field(default=SupplierCategory.FABRIC_MILL)
    contact_email: str | None = None
    contact_phone: str | None = None
    lead_time_days: int = Field(default=14, ge=1)


class SupplierCreate(SupplierBase):
    pass


class SupplierRead(SupplierBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: str
    created_at: datetime
    updated_at: datetime


# --- Supplier Purchase Orders (Inbound) ---
class SupplierPoCreate(BaseModel):
    po_number: str = Field(..., min_length=2, max_length=64)
    supplier_id: uuid.UUID
    material_id: uuid.UUID
    order_id: uuid.UUID | None = None
    quantity_ordered: Decimal = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=0)
    expected_delivery_date: date


class SupplierPoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: str
    po_number: str
    supplier_id: uuid.UUID
    material_id: uuid.UUID
    order_id: uuid.UUID | None = None
    quantity_ordered: Decimal
    quantity_received: Decimal
    unit_price: Decimal
    expected_delivery_date: date
    status: SupplierPoStatus
    supplier_name: str | None = None
    material_name: str | None = None
    created_at: datetime
    updated_at: datetime


# --- Stock Movement Ledger ---
class StockReceiptCreate(BaseModel):
    """Store Keeper GRN receiving against a Supplier PO or direct."""

    material_id: uuid.UUID
    supplier_po_id: uuid.UUID | None = None
    quantity: Decimal = Field(..., gt=0)
    unit_cost: Decimal = Field(default=Decimal("0.00"), ge=0)
    reference_id: str | None = None
    notes: str | None = None


class StockIssueCreate(BaseModel):
    """Store issue to cutting floor for an order."""

    material_id: uuid.UUID
    order_id: uuid.UUID | None = None
    quantity: Decimal = Field(..., gt=0)
    notes: str | None = None


class StockLedgerEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: str
    material_id: uuid.UUID
    movement_type: StockMovementType
    quantity: Decimal
    unit_cost: Decimal
    reference_type: str
    reference_id: str | None = None
    notes: str | None = None
    created_at: datetime

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.domains.orders.models import MilestoneStatus, OrderStatus


# --- Buyers ---
class BuyerCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    code: str = Field(..., min_length=2, max_length=32)
    country: str | None = Field(default=None, max_length=64)
    contact_email: EmailStr | None = None
    payment_terms: str | None = Field(default="LC 60 Days", max_length=64)


class BuyerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: str
    name: str
    code: str
    country: str | None = None
    contact_email: str | None = None
    payment_terms: str | None = None
    created_at: datetime


# --- Styles ---
class StyleCreate(BaseModel):
    buyer_id: uuid.UUID
    style_number: str = Field(..., min_length=1, max_length=64)
    style_name: str = Field(..., min_length=1, max_length=255)
    garment_type: str = Field(default="Crew Neck Tee", max_length=64)
    sam: Decimal = Field(default=Decimal("15.00"), ge=Decimal("1.00"), le=Decimal("200.00"))
    target_efficiency: Decimal = Field(
        default=Decimal("65.00"), ge=Decimal("10.00"), le=Decimal("100.00")
    )


class StyleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: str
    buyer_id: uuid.UUID
    style_number: str
    style_name: str
    garment_type: str
    sam: Decimal
    target_efficiency: Decimal
    created_at: datetime


# --- Order Lines ---
class OrderLineCreate(BaseModel):
    color: str = Field(..., min_length=1, max_length=64)
    size: str = Field(..., min_length=1, max_length=32)
    quantity: int = Field(..., gt=0)


class OrderLineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    color: str
    size: str
    quantity: int


# --- Milestones (TNA) ---
class OrderMilestoneCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=128)
    planned_date: date
    notes: str | None = None


class OrderMilestoneUpdate(BaseModel):
    planned_date: date | None = None
    actual_date: date | None = None
    status: MilestoneStatus | None = None
    notes: str | None = None


class OrderMilestoneRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    planned_date: date
    actual_date: date | None = None
    status: MilestoneStatus
    notes: str | None = None


# --- Orders ---
class OrderCreate(BaseModel):
    buyer_id: uuid.UUID
    style_id: uuid.UUID
    order_number: str = Field(..., min_length=2, max_length=64)
    total_quantity: int = Field(..., gt=0)
    unit_price: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    currency: str = Field(default="INR", max_length=8)
    ex_factory_date: date
    planned_sewing_start: date
    status: OrderStatus = Field(default=OrderStatus.CONFIRMED)
    notes: str | None = None
    lines: list[OrderLineCreate] = Field(default_factory=list)


class OrderUpdate(BaseModel):
    total_quantity: int | None = Field(default=None, gt=0)
    unit_price: Decimal | None = Field(default=None, ge=Decimal("0.00"))
    ex_factory_date: date | None = None
    planned_sewing_start: date | None = None
    status: OrderStatus | None = None
    notes: str | None = None


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: str
    buyer_id: uuid.UUID
    style_id: uuid.UUID
    order_number: str
    total_quantity: int
    unit_price: Decimal
    currency: str
    ex_factory_date: date
    planned_sewing_start: date
    status: OrderStatus
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    buyer: BuyerRead | None = None
    style: StyleRead | None = None
    lines: list[OrderLineRead] = Field(default_factory=list)
    milestones: list[OrderMilestoneRead] = Field(default_factory=list)


# --- Bulk Import Schemas ---
class CsvRowError(BaseModel):
    row_number: int
    field: str
    message: str
    raw_data: dict[str, Any] | None = None


class CsvImportSummary(BaseModel):
    total_rows: int
    successful_rows: int
    failed_rows: int
    created_buyers: int
    created_styles: int
    created_orders: int
    errors: list[CsvRowError] = Field(default_factory=list)


# --- AI PO Extraction Schemas ---
class ExtractedField(BaseModel):
    value: Any
    confidence: float = Field(..., ge=0.0, le=1.0)
    source: str = "layout_rules"


class ExtractedLineItem(BaseModel):
    color: str
    size: str
    quantity: int
    confidence: float = 0.95


class PoExtractionResult(BaseModel):
    order_number: ExtractedField
    buyer_name: ExtractedField
    buyer_id: uuid.UUID | None = None
    buyer_code: str | None = None
    style_number: ExtractedField
    style_name: str | None = None
    style_id: uuid.UUID | None = None
    total_quantity: ExtractedField
    unit_price: ExtractedField
    currency: ExtractedField
    ex_factory_date: ExtractedField
    planned_sewing_start: ExtractedField
    lines: list[ExtractedLineItem] = Field(default_factory=list)
    raw_preview_text: str = ""
    warnings: list[str] = Field(default_factory=list)
    extraction_source: str = "cascade_rules"


import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.domains.production.models import ProductionStage


class ProductionLineBase(BaseModel):
    line_number: str = Field(..., max_length=32)
    name: str = Field(..., max_length=128)
    operator_count: int = Field(default=24, ge=1)
    helper_count: int = Field(default=4, ge=0)
    daily_working_hours: Decimal = Field(default=Decimal("8.00"), ge=Decimal("1.0"), le=Decimal("24.0"))
    is_active: bool = True


class ProductionLineCreate(ProductionLineBase):
    pass


class ProductionLineResponse(ProductionLineBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: str
    created_at: datetime


class DailyProductionLogCreate(BaseModel):
    date: date
    order_id: uuid.UUID
    line_id: uuid.UUID | None = None
    stage: ProductionStage = ProductionStage.SEWING
    planned_output: int = Field(default=0, ge=0)
    actual_output: int = Field(..., ge=0)
    rejected_qty: int = Field(default=0, ge=0)
    operator_count: int | None = Field(default=None, ge=0)
    working_hours: Decimal | None = Field(default=None, ge=Decimal("0.5"), le=Decimal("24.0"))
    notes: str | None = None


class DailyProductionLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: str
    date: date
    order_id: uuid.UUID
    line_id: uuid.UUID | None
    stage: str
    planned_output: int
    actual_output: int
    rejected_qty: int
    operator_count: int
    working_hours: Decimal
    notes: str | None
    created_by_user_id: uuid.UUID | None
    created_at: datetime
    # Calculated efficiency fields
    produced_minutes: Decimal = Decimal("0.0")
    available_minutes: Decimal = Decimal("0.0")
    efficiency_pct: Decimal = Decimal("0.0")
    rejection_rate_pct: Decimal = Decimal("0.0")


class OrderProductionSummary(BaseModel):
    order_id: uuid.UUID
    order_number: str
    total_quantity: int
    ex_factory_date: date
    cumulative_cutting: int
    cumulative_sewing: int
    cumulative_finishing: int
    cumulative_rejected: int
    remaining_sewing_qty: int
    rolling_daily_rate: Decimal
    avg_efficiency_pct: Decimal
    projected_finish_date: date | None
    is_on_track: bool

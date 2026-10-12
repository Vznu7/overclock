import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.domains.jobwork.models import ChallanType, ProcessType


class JobworkProcessorBase(BaseModel):
    name: str = Field(..., max_length=128)
    process_type: ProcessType = ProcessType.DYEING
    contact_person: str | None = Field(default=None, max_length=128)
    phone: str | None = Field(default=None, max_length=32)
    address: str | None = None
    is_active: bool = True


class JobworkProcessorCreate(JobworkProcessorBase):
    pass


class JobworkProcessorResponse(JobworkProcessorBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: str
    created_at: datetime


class JobworkChallanBase(BaseModel):
    challan_number: str = Field(..., max_length=64)
    challan_type: ChallanType = ChallanType.OUTWARD_ISSUE
    processor_id: uuid.UUID
    order_id: uuid.UUID | None = None
    process_name: str = Field(..., max_length=64)
    material_description: str = Field(..., max_length=255)
    issued_qty: Decimal = Field(default=Decimal("0.000"), ge=Decimal("0.0"))
    issued_weight_kg: Decimal = Field(default=Decimal("0.000"), ge=Decimal("0.0"))
    expected_return_date: date
    notes: str | None = None


class JobworkChallanCreate(JobworkChallanBase):
    pass


class JobworkChallanReceive(BaseModel):
    received_qty: Decimal = Field(..., ge=Decimal("0.0"))
    received_weight_kg: Decimal = Field(..., ge=Decimal("0.0"))
    actual_return_date: date | None = None
    notes: str | None = None


class JobworkChallanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: str
    challan_number: str
    challan_type: str
    processor_id: uuid.UUID
    order_id: uuid.UUID | None
    process_name: str
    material_description: str
    issued_qty: Decimal
    issued_weight_kg: Decimal
    expected_return_date: date
    actual_return_date: date | None
    received_qty: Decimal
    received_weight_kg: Decimal
    status: str
    notes: str | None
    created_at: datetime
    # Calculated process reconciliation fields
    weight_loss_kg: Decimal = Decimal("0.000")
    weight_loss_pct: Decimal = Decimal("0.00")
    is_loss_anomaly: bool = False
    processor_name: str = ""

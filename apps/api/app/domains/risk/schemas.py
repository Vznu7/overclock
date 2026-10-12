import uuid
from datetime import date
from decimal import Decimal
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class RiskSeverity(StrEnum):
    NORMAL = "NORMAL"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class InboundPoInput(BaseModel):
    po_number: str
    material_id: uuid.UUID | str
    material_name: str | None = None
    quantity: Decimal
    expected_date: date
    status: str = "PLACED"


class TrimRequirementInput(BaseModel):
    material_id: uuid.UUID | str
    material_code: str
    material_name: str
    component_name: str
    required_qty: Decimal
    current_stock: Decimal = Decimal("0.000")
    inbound_pos: list[InboundPoInput] = Field(default_factory=list)


class RiskAssessment(BaseModel):
    rule: str
    rule_name: str
    order_id: str
    order_number: str | None = None
    buyer_name: str | None = None
    triggered: bool
    severity: RiskSeverity
    deficit_qty: Decimal = Decimal("0.000")
    days_delayed: int = 0
    headline: str
    explanation: str
    evidence: dict[str, Any] = Field(default_factory=dict)


class OrderRiskSummary(BaseModel):
    order_id: str
    order_number: str
    buyer_name: str | None = None
    max_severity: RiskSeverity
    risks: list[RiskAssessment]

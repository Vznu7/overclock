from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TenantCreate(BaseModel):
    id: str = Field(..., min_length=2, max_length=64, pattern=r"^[a-z0-9-]+$")
    name: str = Field(..., min_length=2, max_length=255)
    cluster: str = Field(default="Tiruppur", max_length=100)
    gstin: str | None = Field(default=None, max_length=15)
    currency: str = Field(default="INR", max_length=3)
    timezone: str = Field(default="Asia/Kolkata", max_length=50)


class TenantSettingsUpdate(BaseModel):
    sewing_capacity_daily: int | None = Field(default=None, ge=100, le=50000)
    working_days: list[str] | None = None
    risk_thresholds: dict[str, Any] | None = None
    monthly_ai_budget_inr: float | None = Field(default=None, ge=0.0, le=10000.0)
    daily_ai_budget_cap_inr: float | None = Field(default=None, ge=0.0, le=1000.0)


class TenantSettingsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tenant_id: str
    sewing_capacity_daily: int
    working_days: list[str]
    risk_thresholds: dict[str, Any]
    monthly_ai_budget_inr: float
    daily_ai_budget_cap_inr: float
    updated_at: datetime


class TenantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    cluster: str
    gstin: str | None
    currency: str
    timezone: str
    is_active: bool
    created_at: datetime
    settings: TenantSettingsRead | None = None

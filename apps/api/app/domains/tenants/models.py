from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    cluster: Mapped[str] = mapped_column(String(100), nullable=False, default="Tiruppur")
    gstin: Mapped[str | None] = mapped_column(String(15), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    timezone: Mapped[str] = mapped_column(String(50), nullable=False, default="Asia/Kolkata")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    settings: Mapped["TenantSettings | None"] = relationship(
        "TenantSettings", back_populates="tenant", uselist=False, cascade="all, delete-orphan"
    )


class TenantSettings(Base):
    __tablename__ = "tenant_settings"

    tenant_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("tenants.id", ondelete="CASCADE"), primary_key=True
    )
    sewing_capacity_daily: Mapped[int] = mapped_column(Integer, nullable=False, default=1500)
    working_days: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=lambda: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    )
    risk_thresholds: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=lambda: {
            "r1_need_by_days": 7,
            "r2_gate_days": 7,
            "r3_deficit_multiplier": 1.25,
            "r4_jobwork_tolerance_percent": 2.0,
            "r5_gate_overdue_days": 0,
            "r6_missing_input_lead_days": 14,
        },
    )
    monthly_ai_budget_inr: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=500.00
    )
    daily_ai_budget_cap_inr: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=50.00
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="settings")

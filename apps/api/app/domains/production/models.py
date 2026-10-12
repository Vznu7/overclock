import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ProductionStage(enum.StrEnum):
    CUTTING = "CUTTING"
    SEWING = "SEWING"
    FINISHING = "FINISHING"
    PACKING = "PACKING"


class ProductionLine(Base):
    __tablename__ = "production_lines"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    line_number: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    operator_count: Mapped[int] = mapped_column(default=24, nullable=False)
    helper_count: Mapped[int] = mapped_column(default=4, nullable=False)
    daily_working_hours: Mapped[Decimal] = mapped_column(
        Numeric(4, 2), default=Decimal("8.00"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )

    logs: Mapped[list["DailyProductionLog"]] = relationship(
        "DailyProductionLog", back_populates="line"
    )

    __table_args__ = (
        Index("ix_production_lines_tenant_line", "tenant_id", "line_number", unique=True),
    )


class DailyProductionLog(Base):
    __tablename__ = "daily_production_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("production_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    stage: Mapped[str] = mapped_column(String(32), default=ProductionStage.SEWING, nullable=False)
    planned_output: Mapped[int] = mapped_column(default=0, nullable=False)
    actual_output: Mapped[int] = mapped_column(default=0, nullable=False)
    rejected_qty: Mapped[int] = mapped_column(default=0, nullable=False)
    operator_count: Mapped[int] = mapped_column(default=0, nullable=False)
    working_hours: Mapped[Decimal] = mapped_column(
        Numeric(4, 2), default=Decimal("8.00"), nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )

    line: Mapped[ProductionLine | None] = relationship("ProductionLine", back_populates="logs")

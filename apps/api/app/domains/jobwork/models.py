import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ProcessType(enum.StrEnum):
    DYEING = "DYEING"
    PRINTING = "PRINTING"
    EMBROIDERY = "EMBROIDERY"
    WASHING = "WASHING"
    COMPACTING = "COMPACTING"


class ChallanType(enum.StrEnum):
    OUTWARD_ISSUE = "OUTWARD_ISSUE"
    INWARD_RECEIPT = "INWARD_RECEIPT"


class ChallanStatus(enum.StrEnum):
    ISSUED = "ISSUED"
    PARTIAL_RECEIVED = "PARTIAL_RECEIVED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class JobworkProcessor(Base):
    __tablename__ = "jobwork_processors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    process_type: Mapped[str] = mapped_column(String(32), default=ProcessType.DYEING, nullable=False)
    contact_person: Mapped[str | None] = mapped_column(String(128), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )

    challans: Mapped[list["JobworkChallan"]] = relationship(
        "JobworkChallan", back_populates="processor"
    )


class JobworkChallan(Base):
    __tablename__ = "jobwork_challans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    challan_number: Mapped[str] = mapped_column(String(64), nullable=False)
    challan_type: Mapped[str] = mapped_column(
        String(32), default=ChallanType.OUTWARD_ISSUE, nullable=False
    )
    processor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobwork_processors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    process_name: Mapped[str] = mapped_column(String(64), nullable=False)
    material_description: Mapped[str] = mapped_column(String(255), nullable=False)
    issued_qty: Mapped[Decimal] = mapped_column(
        Numeric(12, 3), default=Decimal("0.000"), nullable=False
    )
    issued_weight_kg: Mapped[Decimal] = mapped_column(
        Numeric(12, 3), default=Decimal("0.000"), nullable=False
    )
    expected_return_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    actual_return_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    received_qty: Mapped[Decimal] = mapped_column(
        Numeric(12, 3), default=Decimal("0.000"), nullable=False
    )
    received_weight_kg: Mapped[Decimal] = mapped_column(
        Numeric(12, 3), default=Decimal("0.000"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(32), default=ChallanStatus.ISSUED, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )

    processor: Mapped[JobworkProcessor] = relationship("JobworkProcessor", back_populates="challans")

    __table_args__ = (
        Index("ix_jobwork_challans_tenant_number", "tenant_id", "challan_number", unique=True),
    )

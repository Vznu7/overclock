import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class MaterialCategory(enum.StrEnum):
    FABRIC = "FABRIC"
    TRIM = "TRIM"
    PACKAGING = "PACKAGING"
    CHEMICAL = "CHEMICAL"


class UnitOfMeasure(enum.StrEnum):
    KG = "KG"
    METER = "METER"
    PIECE = "PIECE"
    CONE = "CONE"
    ROLL = "ROLL"
    BOX = "BOX"


class SupplierCategory(enum.StrEnum):
    FABRIC_MILL = "FABRIC_MILL"
    YARN_SPINNER = "YARN_SPINNER"
    TRIMS_VENDOR = "TRIMS_VENDOR"
    DYE_HOUSE = "DYE_HOUSE"


class SupplierPoStatus(enum.StrEnum):
    DRAFT = "DRAFT"
    PLACED = "PLACED"
    PARTIAL_RECEIVED = "PARTIAL_RECEIVED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class StockMovementType(enum.StrEnum):
    OPENING_BALANCE = "OPENING_BALANCE"
    GRN_RECEIPT = "GRN_RECEIPT"
    ISSUE_TO_CUTTING = "ISSUE_TO_CUTTING"
    RETURN_TO_STORE = "RETURN_TO_STORE"
    ADJUSTMENT = "ADJUSTMENT"


class Material(Base):
    __tablename__ = "materials"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(
        String(32), default=MaterialCategory.FABRIC.value, nullable=False
    )
    unit_of_measure: Mapped[str] = mapped_column(
        String(16), default=UnitOfMeasure.KG.value, nullable=False
    )
    minimum_stock_level: Mapped[Decimal] = mapped_column(
        Numeric(12, 3), default=Decimal("0.000"), nullable=False
    )
    unit_cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00"), nullable=False
    )
    currency: Mapped[str] = mapped_column(String(8), default="INR", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        server_onupdate=text("now()"),
        nullable=False,
    )

    bom_entries = relationship("StyleBom", back_populates="material", cascade="all, delete-orphan")
    supplier_pos = relationship("SupplierPo", back_populates="material")
    stock_entries = relationship(
        "StockLedgerEntry", back_populates="material", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_materials_tenant_code", "tenant_id", "code", unique=True),)


class StyleBom(Base):
    __tablename__ = "style_boms"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    style_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("styles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    material_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("materials.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    component_name: Mapped[str] = mapped_column(String(64), nullable=False)
    consumption_per_piece: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    wastage_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("5.00"), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        server_onupdate=text("now()"),
        nullable=False,
    )

    material = relationship("Material", back_populates="bom_entries")
    style = relationship("Style")


class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    category: Mapped[str] = mapped_column(
        String(32), default=SupplierCategory.FABRIC_MILL.value, nullable=False
    )
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    lead_time_days: Mapped[int] = mapped_column(default=14, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        server_onupdate=text("now()"),
        nullable=False,
    )

    purchase_orders = relationship("SupplierPo", back_populates="supplier")

    __table_args__ = (Index("ix_suppliers_tenant_code", "tenant_id", "code", unique=True),)


class SupplierPo(Base):
    __tablename__ = "supplier_pos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    po_number: Mapped[str] = mapped_column(String(64), nullable=False)
    supplier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("suppliers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    material_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("materials.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True
    )
    quantity_ordered: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    quantity_received: Mapped[Decimal] = mapped_column(
        Numeric(12, 3), default=Decimal("0.000"), nullable=False
    )
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    expected_delivery_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=SupplierPoStatus.PLACED.value, nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        server_onupdate=text("now()"),
        nullable=False,
    )

    supplier = relationship("Supplier", back_populates="purchase_orders")
    material = relationship("Material", back_populates="supplier_pos")
    order = relationship("Order")

    __table_args__ = (Index("ix_supplier_pos_tenant_po", "tenant_id", "po_number", unique=True),)


class StockLedgerEntry(Base):
    """
    Immutable double-entry stock movement ledger.
    No direct updates or deletions permitted. All movements are append-only.
    """

    __tablename__ = "stock_ledger_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    material_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("materials.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    movement_type: Mapped[str] = mapped_column(String(32), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 3), nullable=False
    )  # Positive for inward/receipts, negative for outward/issues
    unit_cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00"), nullable=False
    )
    reference_type: Mapped[str] = mapped_column(String(32), default="INTERNAL", nullable=False)
    reference_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False, index=True
    )

    material = relationship("Material", back_populates="stock_entries")
    created_by = relationship("User")

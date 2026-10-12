import uuid

from app.core.database import SessionLocal, set_session_tenant
from app.core.security import get_password_hash
from app.domains.audit.models import AuditAction, AuditLog
from app.domains.auth.models import User, UserRole
from app.domains.jobwork.models import JobworkChallan, JobworkProcessor
from app.domains.materials.models import (
    Material,
    MaterialCategory,
    StockLedgerEntry,
    StockMovementType,
    StyleBom,
    Supplier,
    SupplierCategory,
    SupplierPo,
    SupplierPoStatus,
    UnitOfMeasure,
)
from app.domains.orders.models import (
    Buyer,
    MilestoneStatus,
    Order,
    OrderLine,
    OrderMilestone,
    OrderStatus,
    Style,
)
from app.domains.production.models import DailyProductionLog, ProductionLine
from app.domains.tenants.models import Tenant, TenantSettings


def seed_demo():
    db = SessionLocal()
    tenant_id = "tirupur-demo"
    print(f"[*] Seeding demo tenant: {tenant_id}...")

    try:
        set_session_tenant(db, tenant_id)
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            tenant = Tenant(
                id=tenant_id,
                name="Tirupur Tex Fab (Demo)",
                cluster="Tirupur",
                is_active=True,
            )
            db.add(tenant)
            db.flush()

        set_session_tenant(db, tenant_id)
        settings = db.query(TenantSettings).filter(TenantSettings.tenant_id == tenant_id).first()
        if not settings:
            settings = TenantSettings(
                tenant_id=tenant_id,
                sewing_capacity_daily=2400,
                working_days=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
                monthly_ai_budget_inr=500.00,
                daily_ai_budget_cap_inr=50.00,
            )
            db.add(settings)
            db.commit()

        users_meta = [
            (
                "owner@tirupur-demo.com",
                "OwnerDemo123!",
                "Senthil Kumar (Managing Director)",
                UserRole.OWNER,
            ),
            (
                "merchandiser@tirupur-demo.com",
                "MerchDemo123!",
                "Priya Natarajan (Lead Merchandiser)",
                UserRole.MERCHANDISER,
            ),
            (
                "production@tirupur-demo.com",
                "ProdDemo123!",
                "Karthik Raja (Production Manager)",
                UserRole.PRODUCTION_MANAGER,
            ),
            (
                "store@tirupur-demo.com",
                "StoreDemo123!",
                "Ramesh Chandran (Store Keeper)",
                UserRole.STORE_KEEPER,
            ),
            (
                "supervisor@tirupur-demo.com",
                "SuperDemo123!",
                "Anand Velu (Floor Supervisor)",
                UserRole.SUPERVISOR,
            ),
            (
                "viewer@tirupur-demo.com",
                "ViewerDemo123!",
                "External Auditor / Buyer Viewer",
                UserRole.VIEWER,
            ),
        ]

        for email, password, full_name, role in users_meta:
            set_session_tenant(db, tenant_id)
            existing = (
                db.query(User).filter(User.tenant_id == tenant_id, User.email == email).first()
            )
            if not existing:
                u = User(
                    id=uuid.uuid4(),
                    tenant_id=tenant_id,
                    email=email,
                    hashed_password=get_password_hash(password),
                    full_name=full_name,
                    role=role.value,
                    is_active=True,
                )
                db.add(u)
                db.flush()

                # Add initial audit log for demo provisioning
                audit = AuditLog(
                    id=uuid.uuid4(),
                    tenant_id=tenant_id,
                    user_id=u.id,
                    entity_type="user",
                    entity_id=str(u.id),
                    action=AuditAction.CREATE.value,
                    changes_json={"email": email, "role": role.value, "name": full_name},
                    ip_address="127.0.0.1",
                    user_agent="SeedScript/1.0",
                )
                db.add(audit)
                db.commit()
                print(f" [+] Created user: {email} ({role.value})")
            else:
                print(f" [~] User already exists: {email}")

        # --- Seed Buyers ---
        buyers_data = [
            ("Decathlon Sports", "DECATH", "France", "sourcing@decathlon.com", "LC 60 Days"),
            ("Next Sourcing UK", "NEXT", "United Kingdom", "orders@nextsourcing.com", "LC 45 Days"),
            ("H&M Global", "HMG", "Sweden", "buyer@hm.com", "Net 30 Days"),
        ]
        buyer_objs: dict[str, Buyer] = {}
        for b_name, b_code, country, email, terms in buyers_data:
            b = db.query(Buyer).filter(Buyer.tenant_id == tenant_id, Buyer.name == b_name).first()
            if not b:
                b = Buyer(
                    id=uuid.uuid4(),
                    tenant_id=tenant_id,
                    name=b_name,
                    code=b_code,
                    country=country,
                    contact_email=email,
                    payment_terms=terms,
                )
                db.add(b)
                db.flush()
                print(f" [+] Created Buyer: {b_name} ({b_code})")
            buyer_objs[b_name] = b

        # --- Seed Styles ---
        from decimal import Decimal

        styles_data = [
            (
                "Decathlon Sports",
                "DEC-TEE-01",
                "QuickDry Performance Tee",
                "Crew Neck Tee",
                Decimal("12.50"),
            ),
            (
                "Decathlon Sports",
                "DEC-SHORT-02",
                "Running Stretch Shorts",
                "Shorts",
                Decimal("16.00"),
            ),
            (
                "Next Sourcing UK",
                "NXT-POLO-01",
                "Classic Pique Mercerized Polo",
                "Polo",
                Decimal("18.00"),
            ),
            (
                "Next Sourcing UK",
                "NXT-HOOD-02",
                "Brushed Fleece Zip Hoodie",
                "Hoodie",
                Decimal("24.50"),
            ),
            (
                "H&M Global",
                "HM-TEE-01",
                "Bio-Wash Single Jersey Tee",
                "Crew Neck Tee",
                Decimal("14.00"),
            ),
            ("H&M Global", "HM-VEST-02", "2x2 Ribbed Gym Vest", "Vest", Decimal("9.50")),
        ]
        style_objs: dict[str, Style] = {}
        for b_name, s_num, s_name, g_type, sam in styles_data:
            buyer = buyer_objs[b_name]
            s = (
                db.query(Style)
                .filter(Style.tenant_id == tenant_id, Style.style_number == s_num)
                .first()
            )
            if not s:
                s = Style(
                    id=uuid.uuid4(),
                    tenant_id=tenant_id,
                    buyer_id=buyer.id,
                    style_number=s_num,
                    style_name=s_name,
                    garment_type=g_type,
                    sam=sam,
                    target_efficiency=Decimal("68.00"),
                )
                db.add(s)
                db.flush()
                print(f" [+] Created Style: {s_num} - {s_name}")
            style_objs[s_num] = s

        # --- Seed Orders with Lines and Milestones ---
        from datetime import date, timedelta

        orders_data = [
            (
                "PO-DEC-8821",
                "Decathlon Sports",
                "DEC-TEE-01",
                12000,
                Decimal("320.00"),
                date(2026, 11, 28),
                date(2026, 11, 14),
            ),
            (
                "PO-NXT-9014",
                "Next Sourcing UK",
                "NXT-POLO-01",
                6500,
                Decimal("580.00"),
                date(2026, 12, 5),
                date(2026, 11, 18),
            ),
            (
                "PO-HM-4102",
                "H&M Global",
                "HM-TEE-01",
                15000,
                Decimal("290.00"),
                date(2026, 12, 12),
                date(2026, 11, 25),
            ),
            (
                "PO-DEC-8902",
                "Decathlon Sports",
                "DEC-SHORT-02",
                8000,
                Decimal("340.00"),
                date(2026, 12, 20),
                date(2026, 12, 2),
            ),
            (
                "PO-NXT-9220",
                "Next Sourcing UK",
                "NXT-HOOD-02",
                4200,
                Decimal("840.00"),
                date(2026, 12, 24),
                date(2026, 12, 8),
            ),
            (
                "PO-HM-4250",
                "H&M Global",
                "HM-VEST-02",
                9800,
                Decimal("260.00"),
                date(2027, 1, 5),
                date(2026, 12, 18),
            ),
        ]

        for po_num, b_name, s_num, qty, price, ex_fac, sew_start in orders_data:
            buyer = buyer_objs[b_name]
            style = style_objs[s_num]
            order = (
                db.query(Order)
                .filter(Order.tenant_id == tenant_id, Order.order_number == po_num)
                .first()
            )
            if not order:
                order = Order(
                    id=uuid.uuid4(),
                    tenant_id=tenant_id,
                    buyer_id=buyer.id,
                    style_id=style.id,
                    order_number=po_num,
                    total_quantity=qty,
                    unit_price=price,
                    currency="INR",
                    ex_factory_date=ex_fac,
                    planned_sewing_start=sew_start,
                    status=OrderStatus.CONFIRMED.value,
                )
                db.add(order)
                db.flush()

                # Add breakdown lines
                half = qty // 2
                db.add(
                    OrderLine(
                        id=uuid.uuid4(),
                        tenant_id=tenant_id,
                        order_id=order.id,
                        color="Navy Blue",
                        size="M",
                        quantity=half,
                    )
                )
                db.add(
                    OrderLine(
                        id=uuid.uuid4(),
                        tenant_id=tenant_id,
                        order_id=order.id,
                        color="Navy Blue",
                        size="L",
                        quantity=qty - half,
                    )
                )

                # Add milestones
                m_list = [
                    ("Fabric In-House", ex_fac - timedelta(days=21)),
                    ("PP Sample Approved", ex_fac - timedelta(days=18)),
                    ("Cutting Start", ex_fac - timedelta(days=14)),
                    ("Sewing Start", sew_start),
                    ("Final Inspection", ex_fac - timedelta(days=2)),
                ]
                for m_name, m_date in m_list:
                    db.add(
                        OrderMilestone(
                            id=uuid.uuid4(),
                            tenant_id=tenant_id,
                            order_id=order.id,
                            name=m_name,
                            planned_date=m_date,
                            status=MilestoneStatus.PENDING.value,
                        )
                    )

                print(f" [+] Created Order: {po_num} ({qty:,} pcs) with 5 milestones")

        # --- Phase 4: Seed Suppliers ---
        suppliers_data = [
            (
                "Lakshmi Yarn Spinning Mills",
                "LAKSHMI",
                SupplierCategory.FABRIC_MILL,
                "sales@lakshmispinning.com",
                "+91 98422 11001",
                14,
            ),
            (
                "Supreme Trims & Accessories",
                "SUPREME",
                SupplierCategory.TRIMS_VENDOR,
                "orders@supremetrims.in",
                "+91 94433 22002",
                7,
            ),
            (
                "Kongu Dyes & Processing Ltd",
                "KONGU",
                SupplierCategory.DYE_HOUSE,
                "dispatch@kongudyes.com",
                "+91 98944 33003",
                10,
            ),
        ]
        supplier_objs: dict[str, Supplier] = {}
        for s_name, s_code, s_cat, email, phone, lead_days in suppliers_data:
            sup = (
                db.query(Supplier)
                .filter(Supplier.tenant_id == tenant_id, Supplier.code == s_code)
                .first()
            )
            if not sup:
                sup = Supplier(
                    id=uuid.uuid4(),
                    tenant_id=tenant_id,
                    name=s_name,
                    code=s_code,
                    category=s_cat,
                    contact_email=email,
                    contact_phone=phone,
                    lead_time_days=lead_days,
                )
                db.add(sup)
                db.flush()
                print(f" [+] Created Supplier: {s_name} ({s_code})")
            supplier_objs[s_code] = sup

        # --- Phase 4: Seed Materials ---
        materials_data = [
            (
                "FAB-SJ-180",
                "100% Combed Cotton Single Jersey 180 GSM",
                MaterialCategory.FABRIC,
                UnitOfMeasure.KG,
                Decimal("500.000"),
                Decimal("340.00"),
            ),
            (
                "FAB-RIB-1X1",
                "1x1 Cotton Spandex Rib 220 GSM",
                MaterialCategory.FABRIC,
                UnitOfMeasure.KG,
                Decimal("100.000"),
                Decimal("380.00"),
            ),
            (
                "FAB-PIQ-220",
                "100% Cotton Pique 220 GSM",
                MaterialCategory.FABRIC,
                UnitOfMeasure.KG,
                Decimal("300.000"),
                Decimal("390.00"),
            ),
            (
                "FAB-FLC-320",
                "3-Thread Brushed Cotton Fleece 320 GSM",
                MaterialCategory.FABRIC,
                UnitOfMeasure.KG,
                Decimal("400.000"),
                Decimal("440.00"),
            ),
            (
                "TRM-THRD-01",
                "100% Spun Polyester 40/2 Thread",
                MaterialCategory.TRIM,
                UnitOfMeasure.CONE,
                Decimal("50.000"),
                Decimal("45.00"),
            ),
            (
                "TRM-BTN-18L",
                "Natural Horn Buttons 18L",
                MaterialCategory.TRIM,
                UnitOfMeasure.PIECE,
                Decimal("10000.000"),
                Decimal("1.20"),
            ),
            (
                "TRM-ZIP-YKK",
                "YKK #5 Antique Brass Open-End Zipper",
                MaterialCategory.TRIM,
                UnitOfMeasure.PIECE,
                Decimal("2000.000"),
                Decimal("38.50"),
            ),
            (
                "TRM-LBL-MAIN",
                "Woven Damask Brand Main Label",
                MaterialCategory.TRIM,
                UnitOfMeasure.PIECE,
                Decimal("5000.000"),
                Decimal("2.10"),
            ),
            (
                "TRM-LBL-CARE",
                "Printed Satin Care & Wash Label",
                MaterialCategory.TRIM,
                UnitOfMeasure.PIECE,
                Decimal("5000.000"),
                Decimal("0.85"),
            ),
            (
                "PKG-POLY-01",
                "Recycled LDPE Polybag 12x15",
                MaterialCategory.PACKAGING,
                UnitOfMeasure.PIECE,
                Decimal("10000.000"),
                Decimal("1.80"),
            ),
        ]
        material_objs: dict[str, Material] = {}
        for m_code, m_name, m_cat, uom, min_stock, cost in materials_data:
            mat = (
                db.query(Material)
                .filter(Material.tenant_id == tenant_id, Material.code == m_code)
                .first()
            )
            if not mat:
                mat = Material(
                    id=uuid.uuid4(),
                    tenant_id=tenant_id,
                    code=m_code,
                    name=m_name,
                    category=m_cat,
                    unit_of_measure=uom,
                    minimum_stock_level=min_stock,
                    unit_cost=cost,
                    currency="INR",
                )
                db.add(mat)
                db.flush()
                print(f" [+] Created Material: {m_code} - {m_name}")
            material_objs[m_code] = mat

        # --- Phase 4: Seed Style BOM Formulas ---
        boms_data = [
            # DEC-TEE-01
            ("DEC-TEE-01", "FAB-SJ-180", "Body Fabric", Decimal("0.2100"), Decimal("5.00")),
            ("DEC-TEE-01", "FAB-RIB-1X1", "Neck Rib", Decimal("0.0250"), Decimal("4.00")),
            ("DEC-TEE-01", "TRM-THRD-01", "Sewing Thread", Decimal("0.0150"), Decimal("2.00")),
            ("DEC-TEE-01", "TRM-LBL-MAIN", "Main Label", Decimal("1.0000"), Decimal("1.00")),
            ("DEC-TEE-01", "TRM-LBL-CARE", "Care Label", Decimal("1.0000"), Decimal("1.00")),
            # DEC-SHORT-02
            ("DEC-SHORT-02", "FAB-SJ-180", "Main Shell Fabric", Decimal("0.1800"), Decimal("5.00")),
            ("DEC-SHORT-02", "TRM-THRD-01", "Sewing Thread", Decimal("0.0180"), Decimal("2.00")),
            ("DEC-SHORT-02", "TRM-LBL-CARE", "Care Label", Decimal("1.0000"), Decimal("1.00")),
            # NXT-POLO-01
            ("NXT-POLO-01", "FAB-PIQ-220", "Pique Body Fabric", Decimal("0.2800"), Decimal("5.00")),
            (
                "NXT-POLO-01",
                "FAB-RIB-1X1",
                "Rib Collar & Cuffs",
                Decimal("0.0400"),
                Decimal("3.00"),
            ),
            ("NXT-POLO-01", "TRM-BTN-18L", "Placket Buttons", Decimal("3.0000"), Decimal("2.00")),
            ("NXT-POLO-01", "TRM-THRD-01", "Sewing Thread", Decimal("0.0200"), Decimal("2.00")),
            ("NXT-POLO-01", "TRM-LBL-MAIN", "Main Label", Decimal("1.0000"), Decimal("1.00")),
            # NXT-HOOD-02
            (
                "NXT-HOOD-02",
                "FAB-FLC-320",
                "Fleece Body & Hood",
                Decimal("0.5500"),
                Decimal("6.00"),
            ),
            ("NXT-HOOD-02", "TRM-ZIP-YKK", "Front Zipper", Decimal("1.0000"), Decimal("1.00")),
            (
                "NXT-HOOD-02",
                "FAB-RIB-1X1",
                "Bottom Hem & Cuff Rib",
                Decimal("0.0800"),
                Decimal("4.00"),
            ),
            ("NXT-HOOD-02", "TRM-LBL-MAIN", "Main Label", Decimal("1.0000"), Decimal("1.00")),
            # HM-TEE-01
            ("HM-TEE-01", "FAB-SJ-180", "Body Fabric", Decimal("0.2200"), Decimal("5.00")),
            ("HM-TEE-01", "FAB-RIB-1X1", "Neck Rib", Decimal("0.0250"), Decimal("4.00")),
            ("HM-TEE-01", "TRM-LBL-CARE", "Care Label", Decimal("1.0000"), Decimal("1.00")),
            # HM-VEST-02
            ("HM-VEST-02", "FAB-RIB-1X1", "Rib Shell Fabric", Decimal("0.1600"), Decimal("5.00")),
            ("HM-VEST-02", "TRM-THRD-01", "Sewing Thread", Decimal("0.0120"), Decimal("2.00")),
            ("HM-VEST-02", "TRM-LBL-CARE", "Care Label", Decimal("1.0000"), Decimal("1.00")),
        ]
        for s_num, m_code, comp_name, cons, wast in boms_data:
            style = style_objs.get(s_num)
            mat = material_objs.get(m_code)
            if style and mat:
                bom_entry = (
                    db.query(StyleBom)
                    .filter(
                        StyleBom.tenant_id == tenant_id,
                        StyleBom.style_id == style.id,
                        StyleBom.component_name == comp_name,
                    )
                    .first()
                )
                if not bom_entry:
                    bom_entry = StyleBom(
                        id=uuid.uuid4(),
                        tenant_id=tenant_id,
                        style_id=style.id,
                        material_id=mat.id,
                        component_name=comp_name,
                        consumption_per_piece=cons,
                        wastage_percentage=wast,
                    )
                    db.add(bom_entry)
                    print(f" [+] Added BOM for {s_num}: {comp_name} ({cons} {mat.unit_of_measure})")
        db.flush()

        # --- Phase 4: Seed Initial Stock Movement Ledger (Opening Balances) ---
        opening_stock = [
            ("FAB-SJ-180", Decimal("2200.000"), Decimal("340.00")),
            ("FAB-RIB-1X1", Decimal("450.000"), Decimal("380.00")),
            ("FAB-PIQ-220", Decimal("1200.000"), Decimal("390.00")),
            ("FAB-FLC-320", Decimal("800.000"), Decimal("440.00")),
            ("TRM-THRD-01", Decimal("350.000"), Decimal("45.00")),
            ("TRM-BTN-18L", Decimal("25000.000"), Decimal("1.20")),
            ("TRM-ZIP-YKK", Decimal("1500.000"), Decimal("38.50")),
            ("TRM-LBL-MAIN", Decimal("12000.000"), Decimal("2.10")),
            ("TRM-LBL-CARE", Decimal("18000.000"), Decimal("0.85")),
            ("PKG-POLY-01", Decimal("15000.000"), Decimal("1.80")),
        ]
        for m_code, qty, cost in opening_stock:
            mat = material_objs.get(m_code)
            if mat:
                existing_entry = (
                    db.query(StockLedgerEntry)
                    .filter(
                        StockLedgerEntry.tenant_id == tenant_id,
                        StockLedgerEntry.material_id == mat.id,
                        StockLedgerEntry.movement_type == StockMovementType.OPENING_BALANCE,
                    )
                    .first()
                )
                if not existing_entry:
                    entry = StockLedgerEntry(
                        id=uuid.uuid4(),
                        tenant_id=tenant_id,
                        material_id=mat.id,
                        movement_type=StockMovementType.OPENING_BALANCE,
                        quantity=qty,
                        unit_cost=cost,
                        reference_type="OPENING_STOCK",
                        reference_id="OP-2026-OCT",
                        notes="Opening inventory audit balance",
                    )
                    db.add(entry)
                    print(f" [+] Seeded Opening Stock: {m_code} -> {qty} {mat.unit_of_measure}")
        db.flush()

        # --- Phase 4: Seed Inbound Supplier POs ---
        supplier_pos_data = [
            (
                "SPO-2026-081",
                "LAKSHMI",
                "FAB-SJ-180",
                Decimal("1500.000"),
                Decimal("340.00"),
                date(2026, 11, 5),
                SupplierPoStatus.PLACED,
            ),
            (
                "SPO-2026-082",
                "LAKSHMI",
                "FAB-PIQ-220",
                Decimal("1000.000"),
                Decimal("390.00"),
                date(2026, 11, 25),
                SupplierPoStatus.PLACED,
            ),
            (
                "SPO-2026-083",
                "SUPREME",
                "TRM-ZIP-YKK",
                Decimal("3000.000"),
                Decimal("38.50"),
                date(2026, 12, 1),
                SupplierPoStatus.PLACED,
            ),
            (
                "SPO-2026-084",
                "SUPREME",
                "TRM-BTN-18L",
                Decimal("10000.000"),
                Decimal("1.20"),
                date(2026, 11, 28),
                SupplierPoStatus.PLACED,
            ),
        ]
        for po_num, s_code, m_code, qty, price, exp_date, stat in supplier_pos_data:
            sup = supplier_objs.get(s_code)
            mat = material_objs.get(m_code)
            if sup and mat:
                po_existing = (
                    db.query(SupplierPo)
                    .filter(
                        SupplierPo.tenant_id == tenant_id,
                        SupplierPo.po_number == po_num,
                    )
                    .first()
                )
                if not po_existing:
                    po_entry = SupplierPo(
                        id=uuid.uuid4(),
                        tenant_id=tenant_id,
                        po_number=po_num,
                        supplier_id=sup.id,
                        material_id=mat.id,
                        quantity_ordered=qty,
                        quantity_received=Decimal("0.000"),
                        unit_price=price,
                        expected_delivery_date=exp_date,
                        status=stat,
                    )
                    db.add(po_entry)
                    print(
                        f" [+] Seeded Supplier PO: {po_num} ({qty} {mat.unit_of_measure}) from {sup.name}"
                    )

        db.commit()
        print(
            "[OK] Phase 4 materials, BOMs, suppliers, stock movements, and inbound POs seeded successfully!"
        )

        # --- Phase 5: Seed Production Lines and Daily Logs ---
        print("\n[*] Seeding Phase 5 Production Lines and Daily Floor Logs...")
        from datetime import date, timedelta

        lines_data = [
            ("Line 1", "T-Shirt Sewing Line 1", 24, 4, Decimal("8.00")),
            ("Line 2", "T-Shirt Sewing Line 2", 24, 4, Decimal("8.00")),
            ("Line 3", "Polo Collar Line 3", 26, 5, Decimal("8.00")),
            ("Line 4", "Hoodie & Fleece Line 4", 28, 6, Decimal("8.00")),
        ]
        line_objs: dict[str, ProductionLine] = {}
        for l_num, l_name, ops, helpers, hrs in lines_data:
            line_existing = (
                db.query(ProductionLine)
                .filter(ProductionLine.tenant_id == tenant_id, ProductionLine.line_number == l_num)
                .first()
            )
            if not line_existing:
                line_obj = ProductionLine(
                    id=uuid.uuid4(),
                    tenant_id=tenant_id,
                    line_number=l_num,
                    name=l_name,
                    operator_count=ops,
                    helper_count=helpers,
                    daily_working_hours=hrs,
                    is_active=True,
                )
                db.add(line_obj)
                db.flush()
                print(f" [+] Created Production Line: {l_num} ({l_name})")
                line_objs[l_num] = line_obj
            else:
                line_objs[l_num] = line_existing

        # Retrieve seeded orders
        order_dec = db.query(Order).filter(Order.tenant_id == tenant_id, Order.order_number == "PO-DEC-8821").first()
        order_nxt = db.query(Order).filter(Order.tenant_id == tenant_id, Order.order_number == "PO-NXT-9014").first()

        today = date.today()
        # Seed daily logs for PO-DEC-8821 on Line 1 (healthy output)
        if order_dec and "Line 1" in line_objs:
            l1 = line_objs["Line 1"]
            for days_ago, actual, rejected in [(3, 580, 10), (2, 620, 12), (1, 650, 14)]:
                log_date = today - timedelta(days=days_ago)
                existing_log = (
                    db.query(DailyProductionLog)
                    .filter(
                        DailyProductionLog.tenant_id == tenant_id,
                        DailyProductionLog.order_id == order_dec.id,
                        DailyProductionLog.date == log_date,
                        DailyProductionLog.stage == "SEWING",
                    )
                    .first()
                )
                if not existing_log:
                    log_entry = DailyProductionLog(
                        id=uuid.uuid4(),
                        tenant_id=tenant_id,
                        date=log_date,
                        order_id=order_dec.id,
                        line_id=l1.id,
                        stage="SEWING",
                        planned_output=600,
                        actual_output=actual,
                        rejected_qty=rejected,
                        operator_count=l1.operator_count,
                        working_hours=l1.daily_working_hours,
                        notes="Main body assembly and neck rib attach",
                    )
                    db.add(log_entry)

            # Cutting log
            cut_log = (
                db.query(DailyProductionLog)
                .filter(
                    DailyProductionLog.tenant_id == tenant_id,
                    DailyProductionLog.order_id == order_dec.id,
                    DailyProductionLog.stage == "CUTTING",
                )
                .first()
            )
            if not cut_log:
                db.add(
                    DailyProductionLog(
                        id=uuid.uuid4(),
                        tenant_id=tenant_id,
                        date=today - timedelta(days=4),
                        order_id=order_dec.id,
                        stage="CUTTING",
                        planned_output=2500,
                        actual_output=2450,
                        rejected_qty=25,
                        operator_count=6,
                        working_hours=Decimal("8.00"),
                        notes="Layer spreading & automated laser cutting",
                    )
                )
            print(" [+] Seeded production logs for PO-DEC-8821")

        # Seed sluggish output for PO-NXT-9014 on Line 3 to trigger R3 warning demo
        if order_nxt and "Line 3" in line_objs:
            l3 = line_objs["Line 3"]
            for days_ago, actual, rejected in [(2, 180, 18), (1, 210, 22)]:
                log_date = today - timedelta(days=days_ago)
                existing_log = (
                    db.query(DailyProductionLog)
                    .filter(
                        DailyProductionLog.tenant_id == tenant_id,
                        DailyProductionLog.order_id == order_nxt.id,
                        DailyProductionLog.date == log_date,
                        DailyProductionLog.stage == "SEWING",
                    )
                    .first()
                )
                if not existing_log:
                    db.add(
                        DailyProductionLog(
                            id=uuid.uuid4(),
                            tenant_id=tenant_id,
                            date=log_date,
                            order_id=order_nxt.id,
                            line_id=l3.id,
                            stage="SEWING",
                            planned_output=450,
                            actual_output=actual,
                            rejected_qty=rejected,
                            operator_count=l3.operator_count,
                            working_hours=l3.daily_working_hours,
                            notes="Collar matching bottleneck causing line slowdown",
                        )
                    )
            print(" [+] Seeded sluggish production logs for PO-NXT-9014 (triggers R3 alert)")

        # --- Milestone 1: Job-Work Processors & Challans ---
        jw_processors_data = [
            {
                "name": "Sri Amman Washing & Bio-Polishing",
                "process_type": "WASHING",
                "contact_person": "K. Sengottaiyan",
                "phone": "+91-98422-11001",
                "address": "SF No. 142, SIDCO Industrial Estate, Harvey Nagar, Tirupur",
            },
            {
                "name": "Apex Rotary Screen Printers",
                "process_type": "PRINTING",
                "contact_person": "V. Radhakrishnan",
                "phone": "+91-98425-22334",
                "address": "Plot 18, Angeripalayam Main Road, Tirupur",
            },
            {
                "name": "Kaveri Yarn & Fabric Dyeing Mills",
                "process_type": "DYEING",
                "contact_person": "M. Thangavel",
                "phone": "+91-94433-77889",
                "address": "SIPCOT Industrial Complex, Perundurai, Erode",
            },
        ]

        proc_objs = {}
        for p_data in jw_processors_data:
            existing_proc = (
                db.query(JobworkProcessor)
                .filter(
                    JobworkProcessor.tenant_id == tenant_id,
                    JobworkProcessor.name == p_data["name"],
                )
                .first()
            )
            if not existing_proc:
                proc = JobworkProcessor(
                    id=uuid.uuid4(),
                    tenant_id=tenant_id,
                    name=p_data["name"],
                    process_type=p_data["process_type"],
                    contact_person=p_data["contact_person"],
                    phone=p_data["phone"],
                    address=p_data["address"],
                    is_active=True,
                )
                db.add(proc)
                db.flush()
                proc_objs[p_data["name"]] = proc
            else:
                proc_objs[p_data["name"]] = existing_proc
        print(f" [+] Seeded {len(proc_objs)} Job-Work processors")

        # Challans for PO-DEC-8821 and PO-NXT-9014
        if order_dec and "Sri Amman Washing & Bio-Polishing" in proc_objs:
            amman = proc_objs["Sri Amman Washing & Bio-Polishing"]
            c1_no = "DC-OUT-AMMAN-8821"
            if not db.query(JobworkChallan).filter(JobworkChallan.tenant_id == tenant_id, JobworkChallan.challan_number == c1_no).first():
                db.add(
                    JobworkChallan(
                        id=uuid.uuid4(),
                        tenant_id=tenant_id,
                        challan_number=c1_no,
                        challan_type="OUTWARD_ISSUE",
                        processor_id=amman.id,
                        order_id=order_dec.id,
                        process_name="Bio-Enzyme Soft Wash",
                        material_description="Single Jersey 160 GSM Combed Cotton",
                        issued_qty=Decimal("1200.000"),
                        issued_weight_kg=Decimal("240.000"),
                        expected_return_date=today + timedelta(days=2),
                        status="ISSUED",
                        notes="Normal lot. Color spec Pantone 19-4052.",
                    )
                )

        if order_nxt and "Apex Rotary Screen Printers" in proc_objs:
            apex = proc_objs["Apex Rotary Screen Printers"]
            c2_no = "DC-IN-APEX-9014"
            if not db.query(JobworkChallan).filter(JobworkChallan.tenant_id == tenant_id, JobworkChallan.challan_number == c2_no).first():
                # Excess loss challan (issued 350 kg, received 328 kg = 6.28% loss -> triggers R4 Anomaly Alert!)
                db.add(
                    JobworkChallan(
                        id=uuid.uuid4(),
                        tenant_id=tenant_id,
                        challan_number=c2_no,
                        challan_type="OUTWARD_ISSUE",
                        processor_id=apex.id,
                        order_id=order_nxt.id,
                        process_name="Chest Pigment Rotary Print",
                        material_description="Cotton Spandex Rib 220 GSM",
                        issued_qty=Decimal("1500.000"),
                        issued_weight_kg=Decimal("350.000"),
                        expected_return_date=today - timedelta(days=2),
                        actual_return_date=today - timedelta(days=1),
                        received_qty=Decimal("1470.000"),
                        received_weight_kg=Decimal("328.000"),
                        status="COMPLETED",
                        notes="Unexplained weight loss 22.0kg (6.28%) during curing process.",
                    )
                )

        if order_nxt and "Kaveri Yarn & Fabric Dyeing Mills" in proc_objs:
            kaveri = proc_objs["Kaveri Yarn & Fabric Dyeing Mills"]
            c3_no = "DC-OUT-KAV-9014"
            if not db.query(JobworkChallan).filter(JobworkChallan.tenant_id == tenant_id, JobworkChallan.challan_number == c3_no).first():
                # Overdue challan: expected 3 days ago, still open -> triggers R4 Overdue Alert!
                db.add(
                    JobworkChallan(
                        id=uuid.uuid4(),
                        tenant_id=tenant_id,
                        challan_number=c3_no,
                        challan_type="OUTWARD_ISSUE",
                        processor_id=kaveri.id,
                        order_id=order_nxt.id,
                        process_name="Reactive Yarn Dyeing",
                        material_description="Combed Cotton 30s Count Yarn",
                        issued_qty=Decimal("800.000"),
                        issued_weight_kg=Decimal("800.000"),
                        expected_return_date=today - timedelta(days=3),
                        status="ISSUED",
                        notes="Delay due to effluent treatment maintenance shutdown at SIPCOT.",
                    )
                )
        print(" [+] Seeded Job-Work challans (healthy + R4 weight loss anomaly + R4 overdue delay)")

        db.commit()
        print("[OK] Phase 5 production lines, logs, and Job-Work hub seeded successfully!")

    finally:
        db.close()


if __name__ == "__main__":
    seed_demo()

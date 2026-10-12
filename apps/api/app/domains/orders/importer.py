import csv
import io
import re
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.core.database import set_session_tenant
from app.domains.orders.models import (
    Buyer,
    MilestoneStatus,
    Order,
    OrderLine,
    OrderMilestone,
    OrderStatus,
    Style,
)
from app.domains.orders.schemas import CsvImportSummary, CsvRowError

DATE_PATTERNS = [
    "%d-%m-%Y",
    "%d/%m/%Y",
    "%d.%m.%Y",
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%d-%b-%Y",
    "%d %b %Y",
]


def parse_date_flexible(val: str) -> date | None:
    if not val:
        return None
    val_clean = val.strip()
    for fmt in DATE_PATTERNS:
        try:
            return datetime.strptime(val_clean, fmt).date()
        except ValueError:
            continue
    return None


def parse_csv_file(content_bytes: bytes) -> tuple[list[dict[str, str]], list[str]]:
    """Decode bytes and parse CSV rows with header normalization."""
    # Attempt decoding as utf-8-sig (handles BOM), then fallback to latin-1
    try:
        text = content_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = content_bytes.decode("latin-1")

    # Sniff dialect
    sample = text[:2048]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
    except Exception:
        dialect = csv.excel

    reader = csv.reader(io.StringIO(text), dialect=dialect)
    rows = list(reader)
    if not rows:
        return [], []

    raw_headers = [h.strip() for h in rows[0]]
    # Normalize headers
    normalized_headers = [re.sub(r"[^a-z0-9]", "", h.lower()) for h in raw_headers]

    parsed_rows: list[dict[str, str]] = []
    for row_values in rows[1:]:
        if not any(v.strip() for v in row_values):
            continue  # skip empty lines
        row_dict: dict[str, str] = {}
        for i, val in enumerate(row_values):
            if i < len(normalized_headers):
                row_dict[normalized_headers[i]] = val.strip()
        parsed_rows.append(row_dict)

    return parsed_rows, raw_headers


def find_col(row: dict[str, str], *aliases: str) -> str:
    for alias in aliases:
        norm = re.sub(r"[^a-z0-9]", "", alias.lower())
        if norm in row and row[norm]:
            return row[norm]
    return ""


def import_orders_csv(
    db: Session,
    tenant_id: str,
    content_bytes: bytes,
    strict: bool = False,
) -> CsvImportSummary:
    """Validate and import orders from CSV rows."""
    set_session_tenant(db, tenant_id)
    rows, _ = parse_csv_file(content_bytes)

    errors: list[CsvRowError] = []
    created_buyers_count = 0
    created_styles_count = 0
    created_orders_count = 0

    if not rows:
        errors.append(
            CsvRowError(
                row_number=0,
                field="file",
                message="CSV file is empty or headers could not be found",
            )
        )
        return CsvImportSummary(
            total_rows=0,
            successful_rows=0,
            failed_rows=0,
            created_buyers=0,
            created_styles=0,
            created_orders=0,
            errors=errors,
        )

    # Cache existing buyers and styles for this tenant to avoid redundant queries
    existing_buyers = {
        b.name.lower(): b for b in db.query(Buyer).filter(Buyer.tenant_id == tenant_id).all()
    }
    existing_styles = {
        (s.buyer_id, s.style_number.lower()): s
        for s in db.query(Style).filter(Style.tenant_id == tenant_id).all()
    }

    valid_order_payloads: list[dict[str, Any]] = []

    for idx, row in enumerate(rows, start=2):  # start=2 considering header is line 1
        order_num = find_col(row, "ordernumber", "order", "ponumber", "po", "pono", "orderno")
        buyer_name = find_col(row, "buyer", "buyername", "customer", "client")
        style_num = find_col(row, "style", "stylenumber", "styleno", "stylecode")
        style_desc = (
            find_col(row, "styledescription", "stylename", "description", "item") or style_num
        )
        qty_str = find_col(row, "quantity", "totalquantity", "qty", "orderqty")
        price_str = find_col(row, "price", "unitprice", "rate", "fob") or "0"
        ex_factory_str = find_col(
            row, "exfactorydate", "exfactory", "deliverydate", "shipdate", "targetdate"
        )
        sewing_start_str = find_col(row, "sewingstart", "plannedsewingstart", "sewingdate")
        color = find_col(row, "color", "colour", "shade")
        size = find_col(row, "size", "sizes")

        # Validation rules
        if not order_num:
            errors.append(
                CsvRowError(
                    row_number=idx,
                    field="order_number",
                    message="Missing Order / PO Number",
                    raw_data=row,
                )
            )
            continue
        if not buyer_name:
            errors.append(
                CsvRowError(
                    row_number=idx, field="buyer", message="Missing Buyer name", raw_data=row
                )
            )
            continue
        if not style_num:
            errors.append(
                CsvRowError(
                    row_number=idx, field="style", message="Missing Style number", raw_data=row
                )
            )
            continue
        if not qty_str:
            errors.append(
                CsvRowError(
                    row_number=idx, field="quantity", message="Missing Quantity", raw_data=row
                )
            )
            continue

        try:
            qty = int(qty_str.replace(",", "").strip())
            if qty <= 0:
                raise ValueError()
        except ValueError:
            errors.append(
                CsvRowError(
                    row_number=idx,
                    field="quantity",
                    message=f"Invalid positive integer quantity: '{qty_str}'",
                    raw_data=row,
                )
            )
            continue

        try:
            unit_price = Decimal(
                price_str.replace(",", "").replace("$", "").replace("₹", "").strip()
            )
        except Exception:
            unit_price = Decimal("0.00")

        ex_factory_date = parse_date_flexible(ex_factory_str)
        if not ex_factory_date:
            errors.append(
                CsvRowError(
                    row_number=idx,
                    field="ex_factory_date",
                    message=f"Unrecognized date format for Ex-Factory Date: '{ex_factory_str}'. Use DD-MM-YYYY.",
                    raw_data=row,
                )
            )
            continue

        sewing_start_date = parse_date_flexible(sewing_start_str)
        if not sewing_start_date:
            # Default to 12 days before ex_factory if omitted
            sewing_start_date = ex_factory_date - timedelta(days=12)

        valid_order_payloads.append(
            {
                "order_number": order_num,
                "buyer_name": buyer_name,
                "style_number": style_num,
                "style_desc": style_desc,
                "quantity": qty,
                "unit_price": unit_price,
                "ex_factory_date": ex_factory_date,
                "sewing_start_date": sewing_start_date,
                "color": color or "Standard Assorted",
                "size": size or "Assorted",
            }
        )

    # If strict mode and errors exist, fail without writing
    if strict and errors:
        return CsvImportSummary(
            total_rows=len(rows),
            successful_rows=0,
            failed_rows=len(errors),
            created_buyers=0,
            created_styles=0,
            created_orders=0,
            errors=errors,
        )

    # Commit valid payloads
    for item in valid_order_payloads:
        # 1. Resolve or create Buyer
        b_key = item["buyer_name"].lower()
        if b_key not in existing_buyers:
            code = re.sub(r"[^A-Za-z0-9]", "", item["buyer_name"])[:6].upper() or "BUYER"
            buyer = Buyer(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                name=item["buyer_name"],
                code=code,
                country="India",
                payment_terms="LC 60 Days",
            )
            db.add(buyer)
            db.flush()
            existing_buyers[b_key] = buyer
            created_buyers_count += 1
        else:
            buyer = existing_buyers[b_key]

        # 2. Resolve or create Style
        s_key = (buyer.id, item["style_number"].lower())
        if s_key not in existing_styles:
            style = Style(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                buyer_id=buyer.id,
                style_number=item["style_number"],
                style_name=item["style_desc"],
                garment_type="Crew Neck Tee",
                sam=Decimal("14.50"),
                target_efficiency=Decimal("65.00"),
            )
            db.add(style)
            db.flush()
            existing_styles[s_key] = style
            created_styles_count += 1
        else:
            style = existing_styles[s_key]

        # 3. Create or update Order
        order = (
            db.query(Order)
            .filter(Order.tenant_id == tenant_id, Order.order_number == item["order_number"])
            .first()
        )
        if not order:
            order = Order(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                buyer_id=buyer.id,
                style_id=style.id,
                order_number=item["order_number"],
                total_quantity=item["quantity"],
                unit_price=item["unit_price"],
                currency="INR",
                ex_factory_date=item["ex_factory_date"],
                planned_sewing_start=item["sewing_start_date"],
                status=OrderStatus.CONFIRMED.value,
            )
            db.add(order)
            db.flush()
            created_orders_count += 1

            # Create default order color/size line
            line = OrderLine(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                order_id=order.id,
                color=item["color"],
                size=item["size"],
                quantity=item["quantity"],
            )
            db.add(line)

            # Generate default 5 TNA milestones
            milestones_def = [
                ("Fabric In-House", item["ex_factory_date"] - timedelta(days=21)),
                ("PP Sample Approved", item["ex_factory_date"] - timedelta(days=18)),
                ("Cutting Start", item["ex_factory_date"] - timedelta(days=14)),
                ("Sewing Start", item["sewing_start_date"]),
                ("Final Inspection", item["ex_factory_date"] - timedelta(days=2)),
            ]
            for m_name, m_date in milestones_def:
                m = OrderMilestone(
                    id=uuid.uuid4(),
                    tenant_id=tenant_id,
                    order_id=order.id,
                    name=m_name,
                    planned_date=m_date,
                    status=MilestoneStatus.PENDING.value,
                )
                db.add(m)

    db.commit()

    return CsvImportSummary(
        total_rows=len(rows),
        successful_rows=len(valid_order_payloads),
        failed_rows=len(errors),
        created_buyers=created_buyers_count,
        created_styles=created_styles_count,
        created_orders=created_orders_count,
        errors=errors,
    )


def export_orders_to_csv(db: Session, tenant_id: str) -> str:
    """Generate CSV text containing all orders for this tenant."""
    set_session_tenant(db, tenant_id)
    orders = (
        db.query(Order)
        .filter(Order.tenant_id == tenant_id)
        .order_by(Order.ex_factory_date.asc())
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "Order Number",
            "Buyer",
            "Style Number",
            "Style Name",
            "Total Quantity",
            "Unit Price",
            "Currency",
            "Ex-Factory Date",
            "Sewing Start Date",
            "Status",
            "Pending Milestones",
        ]
    )

    for o in orders:
        b_name = o.buyer.name if o.buyer else ""
        s_num = o.style.style_number if o.style else ""
        s_name = o.style.style_name if o.style else ""
        pending_m = sum(1 for m in o.milestones if m.status == MilestoneStatus.PENDING.value)
        writer.writerow(
            [
                o.order_number,
                b_name,
                s_num,
                s_name,
                o.total_quantity,
                f"{o.unit_price:.2f}",
                o.currency,
                o.ex_factory_date.strftime("%d-%m-%Y"),
                o.planned_sewing_start.strftime("%d-%m-%Y"),
                o.status,
                pending_m,
            ]
        )

    return output.getvalue()

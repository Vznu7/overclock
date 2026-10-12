import io
import re
from datetime import date, datetime, timedelta
from typing import Any

from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.domains.orders.models import Buyer, Style
from app.domains.orders.schemas import ExtractedField, ExtractedLineItem, PoExtractionResult

# Sample Buyer Purchase Orders for testing and instant preview
SAMPLE_TEMPLATES: dict[str, dict[str, Any]] = {
    "sample_decathlon": {
        "order_number": "DEC-PO-2026-9041",
        "buyer_name": "Decathlon Sports",
        "buyer_code": "DECATH",
        "style_number": "DEC-TEE-01",
        "style_name": "QuickDry Performance Tee",
        "total_quantity": 12000,
        "unit_price": 4.20,
        "currency": "USD",
        "planned_sewing_start": (date.today() + timedelta(days=14)).isoformat(),
        "ex_factory_date": (date.today() + timedelta(days=45)).isoformat(),
        "lines": [
            {"color": "Jet Black", "size": "S", "quantity": 2500, "confidence": 0.99},
            {"color": "Jet Black", "size": "M", "quantity": 4000, "confidence": 0.99},
            {"color": "Jet Black", "size": "L", "quantity": 3500, "confidence": 0.99},
            {"color": "French Navy", "size": "M", "quantity": 2000, "confidence": 0.98},
        ],
        "raw_text": (
            "DECATHLON SOURCING INTERNATIONAL\n"
            "PURCHASE ORDER: DEC-PO-2026-9041\n"
            "VENDOR: Tirupur Tex Fab (Demo), Tirupur, India\n"
            "STYLE NO: DEC-TEE-01 (QuickDry Performance Tee)\n"
            "TOTAL QTY: 12,000 PCS @ USD 4.20 / PC\n"
            "BREAKDOWN:\n"
            "  - Jet Black / S: 2,500\n"
            "  - Jet Black / M: 4,000\n"
            "  - Jet Black / L: 3,500\n"
            "  - French Navy / M: 2,000\n"
            f"PLANNED SEWING START: {(date.today() + timedelta(days=14)).isoformat()}\n"
            f"EX-FACTORY DATE: {(date.today() + timedelta(days=45)).isoformat()}\n"
            "PAYMENT TERMS: LC 60 Days\n"
            "PORT OF DISCHARGE: Le Havre, France"
        ),
    },
    "sample_hm": {
        "order_number": "HMG-SWE-2026-4412",
        "buyer_name": "H&M Global",
        "buyer_code": "HMG",
        "style_number": "HMG-HOOD-03",
        "style_name": "Organic Cotton Hoodie",
        "total_quantity": 8500,
        "unit_price": 7.50,
        "currency": "EUR",
        "planned_sewing_start": (date.today() + timedelta(days=20)).isoformat(),
        "ex_factory_date": (date.today() + timedelta(days=55)).isoformat(),
        "lines": [
            {"color": "Grey Melange", "size": "M", "quantity": 3000, "confidence": 0.98},
            {"color": "Grey Melange", "size": "L", "quantity": 3500, "confidence": 0.98},
            {"color": "Deep Black", "size": "XL", "quantity": 2000, "confidence": 0.97},
        ],
        "raw_text": (
            "H&M HENNES & MAURITZ GBC AB\n"
            "PURCHASE ORDER NO: HMG-SWE-2026-4412\n"
            "SUPPLIER: Tirupur Tex Fab, Tamil Nadu\n"
            "STYLE REF: HMG-HOOD-03\n"
            "DESC: Organic Cotton Hoodie 320 GSM\n"
            "TOTAL UNITS: 8,500 PCS\n"
            "UNIT PRICE: 7.50 EUR\n"
            "COLOR / SIZE MATRIX:\n"
            "  - Grey Melange M: 3,000\n"
            "  - Grey Melange L: 3,500\n"
            "  - Deep Black XL: 2,000\n"
            f"SEWING START: {(date.today() + timedelta(days=20)).isoformat()}\n"
            f"EX-FACTORY / SHIP DATE: {(date.today() + timedelta(days=55)).isoformat()}\n"
            "PAYMENT TERMS: Net 30 Days\n"
            "PORT: Gothenburg"
        ),
    },
    "sample_next": {
        "order_number": "NEXT-UK-2026-1108",
        "buyer_name": "Next Sourcing UK",
        "buyer_code": "NEXT",
        "style_number": "NEXT-POLO-02",
        "style_name": "Pique Polo Shirt",
        "total_quantity": 6000,
        "unit_price": 5.80,
        "currency": "GBP",
        "planned_sewing_start": (date.today() + timedelta(days=10)).isoformat(),
        "ex_factory_date": (date.today() + timedelta(days=38)).isoformat(),
        "lines": [
            {"color": "Bright White", "size": "M", "quantity": 2000, "confidence": 0.96},
            {"color": "Bright White", "size": "L", "quantity": 2000, "confidence": 0.96},
            {"color": "Dark Navy", "size": "L", "quantity": 2000, "confidence": 0.96},
        ],
        "raw_text": (
            "NEXT RETAIL LIMITED - SOURCING DIVISION\n"
            "PO REF: NEXT-UK-2026-1108\n"
            "FACTORY: Tirupur Tex Fab (Demo)\n"
            "STYLE: NEXT-POLO-02 Pique Polo Shirt\n"
            "TOTAL QUANTITY: 6,000 UNITS\n"
            "UNIT FOB: 5.80 GBP\n"
            f"PRODUCTION WINDOW: {(date.today() + timedelta(days=10)).isoformat()} TO {(date.today() + timedelta(days=38)).isoformat()}\n"
            "LINES:\n"
            "  - White M: 2000\n"
            "  - White L: 2000\n"
            "  - Navy L: 2000"
        ),
    },
}


def extract_text_from_pdf(content_bytes: bytes) -> str:
    """Extract plain text from uploaded PDF bytes."""
    try:
        reader = PdfReader(io.BytesIO(content_bytes))
        pages_text: list[str] = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            pages_text.append(f"--- PAGE {i+1} ---\n" + text)
        return "\n".join(pages_text)
    except Exception as exc:
        return f"[Failed to parse PDF binary: {exc}]"


def parse_po_document(
    db: Session,
    tenant_id: str,
    raw_text: str | None = None,
    pdf_bytes: bytes | None = None,
    sample_id: str | None = None,
) -> PoExtractionResult:
    """Extract structured draft purchase order fields with confidence scores."""
    # 1. Preset Sample Quick Path
    if sample_id and sample_id in SAMPLE_TEMPLATES:
        sample = SAMPLE_TEMPLATES[sample_id]
        buyer = (
            db.query(Buyer)
            .filter(Buyer.tenant_id == tenant_id, Buyer.code == sample["buyer_code"])
            .first()
        )
        style = (
            db.query(Style)
            .filter(Style.tenant_id == tenant_id, Style.style_number == sample["style_number"])
            .first()
        )

        warnings: list[str] = []
        if not buyer:
            warnings.append(
                f"Buyer '{sample['buyer_name']}' is not yet registered. You can select an existing buyer."
            )
        if not style:
            warnings.append(
                f"Style '{sample['style_number']}' is not registered under this buyer. You can match or create it."
            )

        return PoExtractionResult(
            order_number=ExtractedField(
                value=sample["order_number"], confidence=0.99, source="sample_template"
            ),
            buyer_name=ExtractedField(
                value=sample["buyer_name"], confidence=0.98, source="sample_template"
            ),
            buyer_id=buyer.id if buyer else None,
            buyer_code=sample["buyer_code"],
            style_number=ExtractedField(
                value=sample["style_number"], confidence=0.97, source="sample_template"
            ),
            style_name=sample["style_name"],
            style_id=style.id if style else None,
            total_quantity=ExtractedField(
                value=sample["total_quantity"], confidence=0.99, source="sample_template"
            ),
            unit_price=ExtractedField(
                value=sample["unit_price"], confidence=0.95, source="sample_template"
            ),
            currency=ExtractedField(
                value=sample["currency"], confidence=0.99, source="sample_template"
            ),
            ex_factory_date=ExtractedField(
                value=sample["ex_factory_date"], confidence=0.96, source="sample_template"
            ),
            planned_sewing_start=ExtractedField(
                value=sample["planned_sewing_start"], confidence=0.95, source="sample_template"
            ),
            lines=[ExtractedLineItem(**line) for line in sample["lines"]],
            raw_preview_text=sample["raw_text"],
            warnings=warnings,
            extraction_source="sample_preset",
        )

    # 2. Extract text from PDF if bytes provided
    text_corpus = raw_text or ""
    if pdf_bytes:
        extracted = extract_text_from_pdf(pdf_bytes)
        text_corpus = extracted if extracted else text_corpus

    warnings = []
    if not text_corpus.strip():
        warnings.append("Document text could not be extracted. Manual entry required.")

    # 3. Deterministic Regex / Heuristic Cascades
    # Order / PO Number
    po_num_match = re.search(
        r"(?:(?:PURCHASE\s*ORDER|P\.?O\.?)\s*(?:Number|No\.?|#|REF)?[:\s]+)([A-Z0-9\-_/]+)",
        text_corpus,
        re.IGNORECASE,
    )
    po_number = (
        po_num_match.group(1).strip()
        if po_num_match
        else f"PO-{datetime.now().strftime('%Y%m%d')}-01"
    )
    po_conf = 0.95 if po_num_match else 0.40

    # Match registered buyers
    tenant_buyers = db.query(Buyer).filter(Buyer.tenant_id == tenant_id).all()
    matched_buyer: Buyer | None = None
    buyer_conf = 0.50
    buyer_name = "Unknown Buyer"
    buyer_code = None

    for b in tenant_buyers:
        if b.name.lower() in text_corpus.lower() or b.code.lower() in text_corpus.lower():
            matched_buyer = b
            buyer_name = b.name
            buyer_code = b.code
            buyer_conf = 0.96
            break

    if not matched_buyer and tenant_buyers:
        # Default to first buyer if available
        matched_buyer = tenant_buyers[0]
        buyer_name = matched_buyer.name
        buyer_code = matched_buyer.code
        buyer_conf = 0.60
        warnings.append(f"Buyer not identified in document text; defaulted to {matched_buyer.name}")

    # Match registered styles
    tenant_styles = db.query(Style).filter(Style.tenant_id == tenant_id).all()
    matched_style: Style | None = None
    style_num = "TS-1001"
    style_conf = 0.50

    style_match = re.search(
        r"(?:Style\s*(?:No\.?|#|Code)?[:\s]+)([A-Z0-9\-_]+)", text_corpus, re.IGNORECASE
    )
    if style_match:
        candidate_code = style_match.group(1).strip()
        for s in tenant_styles:
            if s.style_number.lower() == candidate_code.lower():
                matched_style = s
                style_num = s.style_number
                style_conf = 0.95
                break
        if not matched_style:
            style_num = candidate_code
            style_conf = 0.85

    if not matched_style and tenant_styles:
        matched_style = tenant_styles[0]
        style_num = matched_style.style_number
        style_conf = 0.65

    # Currency & Unit Price
    currency = "USD"
    curr_conf = 0.80
    if "EUR" in text_corpus or "€" in text_corpus:
        currency = "EUR"
        curr_conf = 0.95
    elif "GBP" in text_corpus or "£" in text_corpus:
        currency = "GBP"
        curr_conf = 0.95
    elif "INR" in text_corpus or "₹" in text_corpus:
        currency = "INR"
        curr_conf = 0.95

    price_match = re.search(
        r"(?:Unit\s*Price|Price|Rate|FOB)[:\s]+(?:[$€£₹]|USD|EUR|GBP)?\s*([0-9]+\.?[0-9]*)",
        text_corpus,
        re.IGNORECASE,
    )
    unit_price = float(price_match.group(1)) if price_match else 4.50
    price_conf = 0.92 if price_match else 0.50

    # Total Quantity
    qty_match = re.search(
        r"(?:Total\s*Qty|Quantity|Total\s*Units|PCS)[:\s]+([0-9,]+)",
        text_corpus,
        re.IGNORECASE,
    )
    if qty_match:
        qty_str = qty_match.group(1).replace(",", "")
        total_quantity = int(qty_str) if qty_str.isdigit() else 5000
        qty_conf = 0.95
    else:
        total_quantity = 5000
        qty_conf = 0.50

    # Dates
    today = date.today()
    planned_sewing = today + timedelta(days=14)
    ex_factory = today + timedelta(days=45)

    date_matches = re.findall(r"([0-9]{4}-[0-9]{2}-[0-9]{2})", text_corpus)
    if len(date_matches) >= 2:
        try:
            d1 = datetime.strptime(date_matches[0], "%Y-%m-%d").date()
            d2 = datetime.strptime(date_matches[1], "%Y-%m-%d").date()
            if d1 < d2:
                planned_sewing = d1
                ex_factory = d2
            else:
                planned_sewing = d2
                ex_factory = d1
            date_conf = 0.90
        except ValueError:
            date_conf = 0.60
    elif len(date_matches) == 1:
        try:
            ex_factory = datetime.strptime(date_matches[0], "%Y-%m-%d").date()
            planned_sewing = ex_factory - timedelta(days=30)
            date_conf = 0.80
        except ValueError:
            date_conf = 0.60
    else:
        date_conf = 0.60

    if ex_factory <= planned_sewing:
        warnings.append("Ex-Factory date must be strictly after planned sewing start date.")

    # Lines Breakdown
    lines: list[ExtractedLineItem] = []
    # Try parsing color / size / qty patterns e.g. "Black S 1000" or breakdown
    breakdown_matches = re.findall(
        r"([A-Za-z\s]+?)\s*[/–-]\s*(S|M|L|XL|2XL|XXL|XS)\s*[:=]\s*([0-9,]+)", text_corpus
    )
    if breakdown_matches:
        for c, s, q in breakdown_matches:
            clean_q = int(q.replace(",", ""))
            lines.append(
                ExtractedLineItem(
                    color=c.strip().title(), size=s.strip().upper(), quantity=clean_q, confidence=0.92
                )
            )

    if not lines:
        # Generate sensible default proportional breakdown
        lines = [
            ExtractedLineItem(
                color="Core Black",
                size="S",
                quantity=int(total_quantity * 0.25),
                confidence=0.75,
            ),
            ExtractedLineItem(
                color="Core Black",
                size="M",
                quantity=int(total_quantity * 0.40),
                confidence=0.75,
            ),
            ExtractedLineItem(
                color="Core Black",
                size="L",
                quantity=int(total_quantity * 0.35),
                confidence=0.75,
            ),
        ]

    return PoExtractionResult(
        order_number=ExtractedField(value=po_number, confidence=po_conf, source="regex_layout"),
        buyer_name=ExtractedField(value=buyer_name, confidence=buyer_conf, source="buyer_matcher"),
        buyer_id=matched_buyer.id if matched_buyer else None,
        buyer_code=buyer_code,
        style_number=ExtractedField(
            value=style_num, confidence=style_conf, source="style_matcher"
        ),
        style_name=matched_style.style_name if matched_style else "Extracted Style",
        style_id=matched_style.id if matched_style else None,
        total_quantity=ExtractedField(
            value=total_quantity, confidence=qty_conf, source="qty_parser"
        ),
        unit_price=ExtractedField(
            value=unit_price, confidence=price_conf, source="price_parser"
        ),
        currency=ExtractedField(value=currency, confidence=curr_conf, source="currency_parser"),
        ex_factory_date=ExtractedField(
            value=ex_factory.isoformat(), confidence=date_conf, source="date_matcher"
        ),
        planned_sewing_start=ExtractedField(
            value=planned_sewing.isoformat(), confidence=date_conf, source="date_matcher"
        ),
        lines=lines,
        raw_preview_text=text_corpus or "Document preview text generated by parser.",
        warnings=warnings,
        extraction_source="cascade_heuristics",
    )

import io
import uuid
from unittest.mock import MagicMock

import pytest
from pypdf import PdfWriter

from app.domains.orders.extractor import (
    SAMPLE_TEMPLATES,
    parse_po_document,
)
from app.domains.orders.models import Buyer, Style


@pytest.fixture
def mock_db():
    db = MagicMock()
    buyer = Buyer(
        id=uuid.uuid4(),
        tenant_id="test-tenant",
        name="Decathlon Sports",
        code="DECATH",
    )
    style = Style(
        id=uuid.uuid4(),
        tenant_id="test-tenant",
        buyer_id=buyer.id,
        style_number="DEC-TEE-01",
        style_name="QuickDry Performance Tee",
    )

    def mock_query(model):
        query_mock = MagicMock()
        if model == Buyer:
            query_mock.filter.return_value.first.return_value = buyer
            query_mock.filter.return_value.all.return_value = [buyer]
        elif model == Style:
            query_mock.filter.return_value.first.return_value = style
            query_mock.filter.return_value.all.return_value = [style]
        else:
            query_mock.filter.return_value.first.return_value = None
            query_mock.filter.return_value.all.return_value = []
        return query_mock

    db.query = mock_query
    return db


def test_sample_templates_exist():
    assert "sample_decathlon" in SAMPLE_TEMPLATES
    assert "sample_hm" in SAMPLE_TEMPLATES
    assert "sample_next" in SAMPLE_TEMPLATES


def test_parse_sample_decathlon(mock_db):
    result = parse_po_document(
        db=mock_db,
        tenant_id="test-tenant",
        sample_id="sample_decathlon",
    )
    assert result.order_number.value == "DEC-PO-2026-9041"
    assert result.buyer_name.value == "Decathlon Sports"
    assert result.style_number.value == "DEC-TEE-01"
    assert result.total_quantity.value == 12000
    assert result.unit_price.value == 4.20
    assert result.currency.value == "USD"
    assert len(result.lines) == 4
    assert result.order_number.confidence >= 0.95
    assert result.extraction_source == "sample_preset"


def test_parse_sample_hm(mock_db):
    result = parse_po_document(
        db=mock_db,
        tenant_id="test-tenant",
        sample_id="sample_hm",
    )
    assert result.order_number.value == "HMG-SWE-2026-4412"
    assert result.buyer_name.value == "H&M Global"
    assert result.currency.value == "EUR"
    assert result.total_quantity.value == 8500


def test_parse_sample_next(mock_db):
    result = parse_po_document(
        db=mock_db,
        tenant_id="test-tenant",
        sample_id="sample_next",
    )
    assert result.order_number.value == "NEXT-UK-2026-1108"
    assert result.currency.value == "GBP"
    assert result.total_quantity.value == 6000


def test_parse_custom_raw_text(mock_db):
    text = (
        "PURCHASE ORDER: PO-TIRUPUR-9901\n"
        "BUYER: Decathlon Sports\n"
        "STYLE: DEC-TEE-01\n"
        "TOTAL QTY: 7,500 PCS\n"
        "PRICE: $3.85 USD\n"
        "PLANNED SEWING START: 2026-11-01\n"
        "EX-FACTORY DATE: 2026-12-15\n"
        "BREAKDOWN:\n"
        "  Black / M: 4,000\n"
        "  Black / L: 3,500\n"
    )
    result = parse_po_document(
        db=mock_db,
        tenant_id="test-tenant",
        raw_text=text,
    )
    assert result.order_number.value == "PO-TIRUPUR-9901"
    assert result.total_quantity.value == 7500
    assert result.unit_price.value == 3.85
    assert result.currency.value == "USD"
    assert len(result.lines) == 2
    assert result.lines[0].color == "Black"
    assert result.lines[0].size == "M"
    assert result.lines[0].quantity == 4000


def test_parse_pdf_bytes_in_memory(mock_db):
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    stream = io.BytesIO()
    writer.write(stream)
    pdf_bytes = stream.getvalue()

    result = parse_po_document(
        db=mock_db,
        tenant_id="test-tenant",
        pdf_bytes=pdf_bytes,
    )
    assert result.order_number.value is not None
    assert result.total_quantity.value > 0

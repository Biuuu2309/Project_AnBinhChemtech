from datetime import datetime, timezone
from pathlib import Path

import pytest

from jobs.pptx_mapping import (
    MAX_PRODUCT_ROWS,
    PptxMappingError,
    SHAPE_CUSTOMER,
    SHAPE_DATE,
    SHAPE_PACK_SIZE,
    SHAPE_PRICE_EXCL_VAT,
    SHAPE_PRICE_INCL_VAT,
    SHAPE_PRODUCT_NAME,
    SHAPE_QUOTE_CODE,
    build_shape_writes,
    format_quote_code,
    parse_pack_size_kg,
)
from jobs.pptx_template_service import fill_pptx_template, read_shape_texts
from jobs.validator import validate_quotation_file

TEMPLATE = (
    Path(__file__).resolve().parents[1]
    / "templates"
    / "01_Bao_Gia_An_Binh_Chemtech.V2.pptx"
)


def _job(items, *, qid="QT-TEST-001", vat_percent=None):
    return {
        "id": qid,
        "created_at": datetime(2026, 3, 15, 10, 0, tzinfo=timezone.utc).isoformat(),
        "items": items,
        "payment_terms": "should-not-appear",
        "delivery_terms": "should-not-appear",
        "note": "secret-note",
        "vat_percent": vat_percent,
    }


def _customer():
    return {"company": "Cong Ty Demo", "name": "A", "email": "a@x.com"}


def test_parse_pack_size_and_default(caplog):
    assert parse_pack_size_kg("25 kg/bao", quotation_id="Q", item_index=1) == "25"
    assert parse_pack_size_kg("25", quotation_id="Q", item_index=1) == "25"
    with caplog.at_level("INFO"):
        assert parse_pack_size_kg("99.5%", quotation_id="Q", item_index=2) == "25"
    assert "specification_defaulted" in caplog.text


def test_format_quote_code():
    created = datetime(2026, 10, 12, tzinfo=timezone.utc)
    assert format_quote_code("QT-2026-112", created) == "ABC-[]/QT/[2610]-[112]"
    assert format_quote_code("QT-TEST-001", datetime(2026, 3, 15, tzinfo=timezone.utc)) == (
        "ABC-[]/QT/[2603]-[001]"
    )
    assert format_quote_code("QT-VAT", created) == "ABC-[]/QT/[2610]-[01]"


def test_reject_more_than_three_items():
    items = [
        {"product_name": f"P{i}", "specification": "25", "quantity": 1, "unit_price": 1000}
        for i in range(MAX_PRODUCT_ROWS + 1)
    ]
    with pytest.raises(PptxMappingError, match="at most 3"):
        build_shape_writes(_job(items), _customer())


def test_fill_one_item_clears_extra_rows_and_vat(tmp_path):
    assert TEMPLATE.is_file()
    out = tmp_path / "QT-TEST-001.pptx"
    job = _job(
        [
            {
                "product_name": "Chem A",
                "specification": "99.5%",
                "quantity": 10,
                "unit_price": 51560,
            }
        ]
    )
    fill_pptx_template(TEMPLATE, out, job, _customer())
    validate_quotation_file(out)

    texts = read_shape_texts(out)
    assert "Cong Ty Demo" in texts[SHAPE_CUSTOMER]
    assert "[…]" not in texts[SHAPE_CUSTOMER] and "[.]" not in texts[SHAPE_CUSTOMER]
    assert texts[SHAPE_PRODUCT_NAME[0]] == "Chem A"
    assert texts[SHAPE_PRICE_EXCL_VAT[0]] == "51,560"
    assert texts[SHAPE_PRICE_INCL_VAT[0]] == ""  # no vat_percent → empty
    assert texts[SHAPE_PACK_SIZE[0]] == "25"  # default from 99.5%
    assert texts[SHAPE_PRODUCT_NAME[1]] == ""
    assert texts[SHAPE_PRICE_EXCL_VAT[1]] == ""
    assert texts[SHAPE_PRICE_INCL_VAT[1]] == ""
    assert texts[SHAPE_DATE] == "Ngày 15 tháng 03 năm 2026"
    # QT-TEST-001 @ 2026-03-15 → ABC-[]/QT/[2603]-[001]
    assert texts[SHAPE_QUOTE_CODE] == "ABC-[]/QT/[2603]-[001]"
    assert "BẢNG BÁO GIÁ" in texts[18]
    assert "should-not-appear" not in "".join(texts.values())
    assert "secret-note" not in "".join(texts.values())


def test_fill_three_items(tmp_path):
    items = [
        {"product_name": "A", "specification": "25kg", "quantity": 1, "unit_price": 1000},
        {"product_name": "B", "specification": "50", "quantity": 1, "unit_price": 2000},
        {"product_name": "C", "specification": "x", "quantity": 1, "unit_price": 3000},
    ]
    out = tmp_path / "QT-TEST-003.pptx"
    fill_pptx_template(TEMPLATE, out, _job(items, qid="QT-TEST-003"), _customer())
    texts = read_shape_texts(out)
    assert texts[SHAPE_PRODUCT_NAME[0]] == "A"
    assert texts[SHAPE_PRODUCT_NAME[1]] == "B"
    assert texts[SHAPE_PRODUCT_NAME[2]] == "C"
    assert texts[SHAPE_PACK_SIZE[0]] == "25"
    assert texts[SHAPE_PACK_SIZE[1]] == "50"
    assert texts[SHAPE_PACK_SIZE[2]] == "25"
    assert texts[SHAPE_PRICE_INCL_VAT[2]] == ""


def test_fill_incl_vat_when_percent_set(tmp_path):
    out = tmp_path / "QT-VAT.pptx"
    job = _job(
        [
            {
                "product_name": "Chem A",
                "specification": "25",
                "quantity": 1,
                "unit_price": 51560,
            }
        ],
        qid="QT-VAT",
        vat_percent=8,
    )
    fill_pptx_template(TEMPLATE, out, job, _customer())
    texts = read_shape_texts(out)
    assert texts[SHAPE_PRICE_EXCL_VAT[0]] == "51,560"
    assert texts[SHAPE_PRICE_INCL_VAT[0]] == "55,684.80"
    assert texts[SHAPE_PRICE_INCL_VAT[1]] == ""


def test_vietnamese_preserved(tmp_path):
    out = tmp_path / "QT-VI.pptx"
    job = _job(
        [
            {
                "product_name": "Muối Phosphate Thực Phẩm",
                "specification": "25 kg/bao",
                "quantity": 2,
                "unit_price": 51560,
            }
        ],
        qid="QT-VI",
    )
    customer = {"company": "Công Ty TNHH An Bình Demo", "name": "Nguyễn Văn A"}
    fill_pptx_template(TEMPLATE, out, job, customer)
    texts = read_shape_texts(out)
    assert "Công Ty TNHH An Bình Demo" in texts[SHAPE_CUSTOMER]
    assert texts[SHAPE_PRODUCT_NAME[0]] == "Muối Phosphate Thực Phẩm"
    assert "Ngày" in texts[SHAPE_DATE] and "năm 2026" in texts[SHAPE_DATE]


def test_missing_template_raises(tmp_path):
    missing = tmp_path / "no-such.pptx"
    with pytest.raises(FileNotFoundError, match="PPTX template not found"):
        fill_pptx_template(missing, tmp_path / "out.pptx", _job([]), _customer())


def test_output_under_allowed_dir_readable(tmp_path):
    """Simulate worker output dir + re-read verification."""
    out_dir = tmp_path / "output"
    out_dir.mkdir()
    out = out_dir / "QT-SAFE-001.pptx"
    fill_pptx_template(
        TEMPLATE,
        out,
        _job(
            [{"product_name": "X", "specification": "25", "quantity": 1, "unit_price": 1}],
            qid="QT-SAFE-001",
        ),
        _customer(),
    )
    assert out.is_file() and out.stat().st_size > 0
    validate_quotation_file(out)
    assert out.resolve().is_relative_to(out_dir.resolve())
    assert "X" in read_shape_texts(out)[SHAPE_PRODUCT_NAME[0]]

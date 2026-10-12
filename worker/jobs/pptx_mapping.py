"""Centralized PPTX V2 shape-id mapping (no txt_* assumption)."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

logger = logging.getLogger("worker.pptx")

MAX_PRODUCT_ROWS = 3

# Verified shape ids on docs/01_Bao_Gia_An_Binh_Chemtech.V2.pptx (slide 1)
SHAPE_CUSTOMER = 20
SHAPE_PRODUCT_NAME = (28, 32, 36)
SHAPE_PRICE_EXCL_VAT = (29, 33, 37)
SHAPE_PRICE_INCL_VAT = (30, 34, 38)  # filled when vat_percent > 0; else empty
SHAPE_PACK_SIZE = (49, 50, 51)
SHAPE_DATE = 42
SHAPE_QUOTE_CODE = 46  # ABC-[]/QT/[yymm]-[seq]

REQUIRED_SHAPES: tuple[int, ...] = (
    SHAPE_CUSTOMER,
    SHAPE_DATE,
    SHAPE_QUOTE_CODE,
    *SHAPE_PRODUCT_NAME,
    *SHAPE_PRICE_EXCL_VAT,
    *SHAPE_PRICE_INCL_VAT,
    *SHAPE_PACK_SIZE,
)


class PptxMappingError(ValueError):
    """Business / template mapping error — fail the job."""


@dataclass(frozen=True)
class ShapeWrite:
    shape_id: int
    text: str


_PACK_RE = re.compile(
    r"^\s*(\d+(?:[.,]\d+)?)\s*(?:kg(?:\s*/\s*bao)?|/\s*bao)?\s*$",
    re.IGNORECASE,
)


def parse_pack_size_kg(specification: str | None, *, quotation_id: str, item_index: int) -> str:
    raw = (specification or "").strip()
    match = _PACK_RE.match(raw)
    if match:
        num = match.group(1).replace(",", ".")
        if num.endswith(".0"):
            num = num[:-2]
        try:
            as_float = float(num)
            if as_float == int(as_float):
                return str(int(as_float))
        except ValueError:
            pass
        return match.group(1).replace(",", ".")

    logger.info(
        "specification_defaulted quotation_id=%s item_index=%s raw=%r default=25",
        quotation_id,
        item_index,
        raw,
    )
    return "25"


def format_unit_price(value: float | int | str) -> str:
    amount = float(value)
    if amount == int(amount):
        return f"{int(amount):,}"
    return f"{amount:,.2f}"


def resolve_vat_percent(job: dict[str, Any]) -> float | None:
    raw = job.get("vat_percent")
    if raw is None or raw == "":
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if value <= 0:
        return None
    return value


def format_price_incl_vat(unit_price: float | int | str, vat_percent: float | None) -> str:
    if vat_percent is None:
        return ""
    incl = float(unit_price) * (1.0 + vat_percent / 100.0)
    return format_unit_price(incl)


def _parse_created_at(job: dict[str, Any]) -> datetime:
    raw = job.get("created_at")
    if isinstance(raw, datetime):
        return raw
    if isinstance(raw, str) and raw.strip():
        text = raw.strip().replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(text)
        except ValueError:
            pass
    return datetime.now().astimezone()


_SEQ_RE = re.compile(r"(\d+)\s*$")


def format_quote_code(quotation_id: str, created: datetime) -> str:
    """ABC-[]/QT/[yymm]-[seq] — [] after ABC left empty; seq from id suffix."""
    yymm = f"{created.year % 100:02d}{created.month:02d}"
    match = _SEQ_RE.search((quotation_id or "").strip())
    seq = match.group(1) if match else "01"
    if not match:
        logger.info(
            "quote_code_seq_defaulted quotation_id=%r default=01",
            quotation_id,
        )
    return f"ABC-[]/QT/[{yymm}]-[{seq}]"


def build_shape_writes(job: dict[str, Any], customer: dict[str, Any]) -> list[ShapeWrite]:
    items = list(job.get("items") or [])
    if len(items) > MAX_PRODUCT_ROWS:
        raise PptxMappingError(
            f"Quotation has {len(items)} items; PPTX V2 template supports at most {MAX_PRODUCT_ROWS}"
        )

    quotation_id = str(job.get("id") or "")
    company = (customer.get("company") or "").strip()
    created = _parse_created_at(job)
    vat_percent = resolve_vat_percent(job)

    writes: list[ShapeWrite] = [
        ShapeWrite(SHAPE_CUSTOMER, f"Quý khách hàng / Quý đối tác: {company}"),
        ShapeWrite(
            SHAPE_DATE,
            f"Ngày {created.day:02d} tháng {created.month:02d} năm 2026",
        ),
        ShapeWrite(SHAPE_QUOTE_CODE, format_quote_code(quotation_id, created)),
    ]

    for row in range(MAX_PRODUCT_ROWS):
        name_id = SHAPE_PRODUCT_NAME[row]
        excl_id = SHAPE_PRICE_EXCL_VAT[row]
        incl_id = SHAPE_PRICE_INCL_VAT[row]
        pack_id = SHAPE_PACK_SIZE[row]

        if row >= len(items):
            writes.append(ShapeWrite(name_id, ""))
            writes.append(ShapeWrite(excl_id, ""))
            writes.append(ShapeWrite(incl_id, ""))
            writes.append(ShapeWrite(pack_id, ""))
            continue

        item = items[row]
        unit_price = item.get("unit_price", 0)
        writes.append(ShapeWrite(name_id, str(item.get("product_name") or "").strip()))
        writes.append(ShapeWrite(excl_id, format_unit_price(unit_price)))
        writes.append(ShapeWrite(incl_id, format_price_incl_vat(unit_price, vat_percent)))
        writes.append(
            ShapeWrite(
                pack_id,
                parse_pack_size_kg(
                    item.get("specification"),
                    quotation_id=quotation_id,
                    item_index=row + 1,
                ),
            )
        )

    return writes

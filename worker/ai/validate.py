from __future__ import annotations

import re

from ai.types import NoteNormalizationResult

FORBIDDEN_KEYS = {
    "quantity",
    "unit_price",
    "unitprice",
    "price",
    "amount",
    "total",
    "items",
    "product_name",
    "product",
    "specification",
    "payment_terms",
    "delivery_terms",
}

MAX_SUMMARY_LEN = 1000
MAX_TAGS = 8


class AIValidationError(ValueError):
    pass


def validate_note_result(
    result: NoteNormalizationResult,
    *,
    raw_note: str,
    extra: dict | None = None,
) -> NoteNormalizationResult:
    """Reject AI payloads that try to set commercial fields or empty/malformed output."""
    if not isinstance(result, NoteNormalizationResult):
        raise AIValidationError("AI output must be NoteNormalizationResult")

    if extra:
        lowered = {str(k).lower().replace(" ", "_") for k in extra}
        bad = lowered & FORBIDDEN_KEYS
        if bad:
            raise AIValidationError(f"AI output contains forbidden commercial fields: {sorted(bad)}")

    if not isinstance(result.summary, str):
        raise AIValidationError("AI note summary must be a string")

    summary = result.summary.strip()
    if not summary:
        raise AIValidationError("AI note summary is empty")
    if len(summary) > MAX_SUMMARY_LEN:
        summary = summary[:MAX_SUMMARY_LEN].rstrip() + "…"

    # Block structured commercial overrides smuggled inside the note text
    if re.search(
        r"(?i)\b(quantity|unit[_ ]?price|payment_terms|delivery_terms)\s*[:=]\s*\S+",
        summary,
    ):
        if not re.search(
            r"(?i)\b(quantity|unit[_ ]?price|payment_terms|delivery_terms|đơn giá|số lượng)\b",
            raw_note or "",
        ):
            raise AIValidationError("AI note appears to inject structured commercial fields")

    raw_tags = result.tags or ()
    if not isinstance(raw_tags, (list, tuple)):
        raise AIValidationError("AI tags must be a list/tuple of strings")
    tags = tuple(str(t).strip().lower() for t in raw_tags if str(t).strip())[:MAX_TAGS]
    return NoteNormalizationResult(summary=summary, tags=tags, source=result.source)

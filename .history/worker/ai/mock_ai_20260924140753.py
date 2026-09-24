from __future__ import annotations

import logging
import re

from ai.types import NoteNormalizationResult

logger = logging.getLogger("worker.ai.mock")


class MockAI:
    """
    Deterministic stand-in for Codex/LLM note normalization.
    Demo-only: rule-based cleanup — not a real model.
    """

    def normalize_note(self, raw_note: str) -> NoteNormalizationResult:
        text = (raw_note or "").strip()
        logger.info("ai_step=normalize_note provider=mock status=start chars=%s", len(text))

        if not text:
            result = NoteNormalizationResult(summary="(no customer note)", tags=(), source="mock")
            logger.info("ai_step=normalize_note provider=mock status=ok empty_input=1")
            return result

        cleaned = re.sub(r"\s+", " ", text)
        tags: list[str] = []
        lower = cleaned.lower()
        if any(k in lower for k in ("gấp", "gap", "urgent", "asap")):
            tags.append("urgent")
        if any(k in lower for k in ("mẫu", "mau", "sample")):
            tags.append("sample")
        if any(k in lower for k in ("vat", "hóa đơn", "hoa don", "invoice")):
            tags.append("invoice")

        summary = cleaned
        if tags:
            summary = f"{cleaned} [tags: {', '.join(tags)}]"

        # Light professional framing — still derived only from user text
        summary = f"Ghi chú đã chuẩn hóa: {summary}"

        result = NoteNormalizationResult(summary=summary, tags=tuple(tags), source="mock")
        logger.info(
            "ai_step=normalize_note provider=mock status=ok tags=%s summary_len=%s",
            list(result.tags),
            len(result.summary),
        )
        return result

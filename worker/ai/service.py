from __future__ import annotations

import logging
from typing import Protocol, runtime_checkable

from ai.mock_ai import MockAI
from ai.types import NoteNormalizationResult
from ai.validate import AIValidationError, validate_note_result
from codex.codex_runner import CodexRunner, CodexUnavailableError
from config import settings

logger = logging.getLogger("worker.ai")

# Commercial / structured fields — never sourced from AI output.
PROTECTED_JOB_FIELDS = (
    "quantity",
    "unit_price",
    "product_name",
    "specification",
    "payment_terms",
    "delivery_terms",
    "items",
    "customer_id",
    "id",
)


@runtime_checkable
class AIService(Protocol):
    def normalize_note(self, raw_note: str) -> NoteNormalizationResult: ...


def get_ai_service() -> AIService:
    if settings.use_codex_cli:
        logger.info("ai_provider=codex_runner (USE_CODEX_CLI=true)")
        return CodexRunner()
    logger.info("ai_provider=mock_ai (USE_CODEX_CLI=false)")
    return MockAI()


def apply_note_only(job: dict, note: str) -> dict:
    """Return a shallow copy of job with only `note` replaced."""
    updated = dict(job)
    updated["note"] = note
    return updated


def assert_protected_fields_unchanged(before: dict, after: dict) -> None:
    for key in PROTECTED_JOB_FIELDS:
        if key == "items":
            assert before.get("items") == after.get("items")
        elif key in before or key in after:
            assert before.get(key) == after.get(key), f"Protected field changed: {key}"


def normalize_quotation_note(raw_note: str | None) -> tuple[str, NoteNormalizationResult | None]:
    """
    Optional AI step: free-text note → validated normalized note.
    On failure: fallback to original note (pipeline continues when AI_FAIL_JOB_ON_ERROR=false).
    """
    raw = (raw_note or "").strip()
    if not settings.ai_note_enabled:
        logger.info("ai_step=normalize_note skipped reason=ai_note_enabled=false")
        return raw, None

    if not raw:
        return "", None

    service = get_ai_service()
    try:
        result = service.normalize_note(raw)
        validated = validate_note_result(result, raw_note=raw)
        logger.info(
            "ai_step=normalize_note status=accepted source=%s tags=%s",
            validated.source,
            list(validated.tags),
        )
        return validated.summary, validated
    except (AIValidationError, CodexUnavailableError, NotImplementedError) as exc:
        logger.warning(
            "ai_step=normalize_note status=fallback reason=%s original_kept=1",
            exc,
        )
        if settings.ai_fail_job_on_error:
            raise
        return raw, NoteNormalizationResult(summary=raw, tags=(), source="fallback")
    except Exception:
        logger.exception("ai_step=normalize_note status=fallback reason=unexpected")
        if settings.ai_fail_job_on_error:
            raise
        return raw, NoteNormalizationResult(summary=raw, tags=(), source="fallback")

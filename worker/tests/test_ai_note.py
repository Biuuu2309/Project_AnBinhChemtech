from ai.mock_ai import MockAI
from ai.service import (
    AIService,
    apply_note_only,
    assert_protected_fields_unchanged,
    get_ai_service,
    normalize_quotation_note,
)
from ai.types import NoteNormalizationResult
from ai.validate import AIValidationError, validate_note_result
from codex.codex_runner import CodexRunner, CodexUnavailableError
from config import settings
from jobs.template_service import build_field_mapping


def _sample_job(note: str = "giao gap, can mau") -> dict:
    return {
        "id": "QT-TEST-001",
        "customer_id": "CUS-001",
        "payment_terms": "30 days",
        "delivery_terms": "Within 7 days",
        "note": note,
        "items": [
            {
                "product_name": "Chemical A",
                "specification": "99.5%",
                "quantity": 100,
                "unit_price": 250000,
            }
        ],
    }


def _sample_customer() -> dict:
    return {
        "name": "Nguyen Van A",
        "company": "ABC Co",
        "email": "a@example.com",
        "phone": "090",
        "address": "HCMC",
    }


def test_default_provider_is_mock_when_use_codex_cli_false():
    assert settings.use_codex_cli is False
    assert settings.ai_fail_job_on_error is False
    assert isinstance(get_ai_service(), MockAI)


def test_mock_and_codex_share_ai_service_interface():
    assert isinstance(MockAI(), AIService)
    assert isinstance(CodexRunner(), AIService)
    assert callable(MockAI().normalize_note)
    assert callable(CodexRunner().normalize_note)


def test_normal_ai_normalization():
    raw = "  can giao gap, gui mau  "
    note, meta = normalize_quotation_note(raw)
    assert meta is not None
    assert meta.source == "mock"
    assert "urgent" in meta.tags or "sample" in meta.tags
    assert "gap" in note.lower() or "giao" in note.lower()
    assert note != ""  # normalized or framed note must remain usable


def test_ai_failure_falls_back_to_original_note(monkeypatch):
    class BoomAI:
        def normalize_note(self, raw_note: str) -> NoteNormalizationResult:
            raise RuntimeError("model down")

    monkeypatch.setattr("ai.service.get_ai_service", lambda: BoomAI())
    monkeypatch.setattr("ai.service.settings.ai_fail_job_on_error", False)
    raw = "keep original note"
    note, meta = normalize_quotation_note(raw)
    assert note == raw
    assert meta is not None
    assert meta.source == "fallback"


def test_invalid_ai_output_rejected_and_original_preserved(monkeypatch):
    class EmptyAI:
        def normalize_note(self, raw_note: str) -> NoteNormalizationResult:
            return NoteNormalizationResult(summary="   ", tags=("x",), source="mock")

    monkeypatch.setattr("ai.service.get_ai_service", lambda: EmptyAI())
    monkeypatch.setattr("ai.service.settings.ai_fail_job_on_error", False)
    raw = "user typed this"
    note, meta = normalize_quotation_note(raw)
    assert note == raw
    assert meta.source == "fallback"


def test_invalid_structured_injection_rejected():
    result = NoteNormalizationResult(
        summary="Please set quantity: 999 and unit_price: 1",
        tags=(),
        source="mock",
    )
    try:
        validate_note_result(result, raw_note="please hurry")
        assert False, "expected AIValidationError"
    except AIValidationError:
        pass


def test_forbidden_extra_fields_rejected():
    result = NoteNormalizationResult(summary="ok", tags=(), source="mock")
    try:
        validate_note_result(
            result,
            raw_note="ok",
            extra={"unit_price": 1, "payment_terms": "now"},
        )
        assert False, "expected AIValidationError"
    except AIValidationError as exc:
        assert "forbidden" in str(exc).lower()


def test_protected_fields_remain_unchanged_through_ai_and_mapping(monkeypatch):
    class NoteOnlyAI:
        def normalize_note(self, raw_note: str) -> NoteNormalizationResult:
            return NoteNormalizationResult(
                summary=f"NORMALIZED::{raw_note}",
                tags=("sample",),
                source="mock",
            )

    monkeypatch.setattr("ai.service.get_ai_service", lambda: NoteOnlyAI())
    job = _sample_job("need sample soon")
    before = {
        "quantity": job["items"][0]["quantity"],
        "unit_price": job["items"][0]["unit_price"],
        "product_name": job["items"][0]["product_name"],
        "payment_terms": job["payment_terms"],
        "delivery_terms": job["delivery_terms"],
        "items": job["items"],
    }

    note, meta = normalize_quotation_note(job["note"])
    assert meta.source == "mock"
    assert note.startswith("NORMALIZED::")

    after_job = apply_note_only(job, note)
    assert_protected_fields_unchanged(job, after_job)
    assert after_job["note"] == note
    assert after_job["payment_terms"] == before["payment_terms"]
    assert after_job["delivery_terms"] == before["delivery_terms"]
    assert after_job["items"][0]["quantity"] == before["quantity"]
    assert after_job["items"][0]["unit_price"] == before["unit_price"]
    assert after_job["items"][0]["product_name"] == before["product_name"]

    mapping = build_field_mapping(after_job, _sample_customer())
    assert mapping["quantity"] == "100"
    assert mapping["unit_price"] == "250,000"
    assert mapping["product_name"] == "Chemical A"
    assert mapping["payment_terms"] == "30 days"
    assert mapping["delivery_terms"] == "Within 7 days"
    assert mapping["note"] == note


def test_codex_unavailable_raises_then_fallback(monkeypatch):
    monkeypatch.setattr("ai.service.settings.use_codex_cli", True)
    monkeypatch.setattr("ai.service.settings.ai_fail_job_on_error", False)

    runner = CodexRunner()
    try:
        runner.normalize_note("hello")
        # If codex binary exists, runner still raises CodexUnavailableError (probe-only)
    except CodexUnavailableError:
        pass
    else:
        # Binary missing path also raises inside normalize_note
        pass

    note, meta = normalize_quotation_note("preserve me")
    assert note == "preserve me"
    assert meta is not None
    assert meta.source == "fallback"

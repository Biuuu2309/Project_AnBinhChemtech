from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.core.migrate import ensure_schema
from app.core.database import engine
from app.main import app
from app.models import AttemptStatus, ProcessingAttempt, Quotation, QuotationStatus


def _close_all_active() -> None:
    """Clear in-flight jobs so tests are not blocked by a live worker / leftover rows."""
    db = SessionLocal()
    try:
        rows = (
            db.query(Quotation)
            .filter(Quotation.status.in_([QuotationStatus.PENDING, QuotationStatus.PROCESSING]))
            .all()
        )
        for row in rows:
            row.status = QuotationStatus.FAILED
            row.error_message = "cleared by test"
        # Close orphan STARTED attempts (e.g. worker died mid-job)
        for attempt in (
            db.query(ProcessingAttempt)
            .filter(ProcessingAttempt.status == AttemptStatus.STARTED)
            .all()
        ):
            attempt.status = AttemptStatus.FAILED
            attempt.error_message = attempt.error_message or "cleared by test"
        db.commit()
    finally:
        db.close()


def test_customer_crud_and_soft_delete():
    ensure_schema(engine)
    with TestClient(app) as client:
        created = client.post(
            "/api/customers",
            json={
                "name": "Test User",
                "company": "Test Co",
                "email": "test@example.com",
                "phone": "0900000000",
                "address": "HCMC",
            },
        )
        assert created.status_code == 201, created.text
        cid = created.json()["id"]
        assert created.json()["is_active"] is True

        listed = client.get("/api/customers", params={"q": "Test Co"})
        assert listed.status_code == 200
        assert any(c["id"] == cid for c in listed.json())

        updated = client.put(
            f"/api/customers/{cid}",
            json={"phone": "0911111111"},
        )
        assert updated.status_code == 200
        assert updated.json()["phone"] == "0911111111"

        deactivated = client.post(f"/api/customers/{cid}/deactivate")
        assert deactivated.status_code == 200
        assert deactivated.json()["is_active"] is False

        active_list = client.get("/api/customers", params={"active_only": True})
        assert all(c["id"] != cid for c in active_list.json())


def test_quotation_list_history_attempt_retry_audit():
    ensure_schema(engine)
    _close_all_active()

    with TestClient(app) as client:
        payload = {
            "customer_id": "CUS-001",
            "items": [
                {
                    "product_name": "Chem A",
                    "specification": "99%",
                    "quantity": 10,
                    "unit_price": 1000,
                }
            ],
            "payment_terms": "30 days",
            "delivery_terms": "7 days",
            "note": "history test",
        }
        created = client.post("/api/quotations", json=payload)
        assert created.status_code == 201, created.text
        qid = created.json()["id"]

        listed = client.get("/api/quotations", params={"status": "PENDING"})
        assert listed.status_code == 200
        assert any(r["id"] == qid for r in listed.json()), listed.json()[:5]

        claimed = client.get("/api/internal/jobs/next")
        assert claimed.status_code == 200
        assert claimed.json()["id"] == qid
        assert claimed.json()["attempt_count"] >= 1

        failed = client.post(
            f"/api/internal/jobs/{qid}/fail",
            json={"error_message": "boom"},
        )
        assert failed.status_code == 200
        assert failed.json()["status"] == "FAILED"

        history = client.get(f"/api/quotations/{qid}/history")
        assert history.status_code == 200
        statuses = [e["to_status"] for e in history.json()]
        assert "PENDING" in statuses
        assert "PROCESSING" in statuses
        assert "FAILED" in statuses

        attempts = client.get(f"/api/quotations/{qid}/attempts")
        assert attempts.status_code == 200
        assert len(attempts.json()) >= 1
        # Prefer last attempt FAILED; tolerate a live worker appending a new STARTED claim
        statuses = [a["status"] for a in attempts.json()]
        assert "FAILED" in statuses, statuses

        retried = client.post(f"/api/quotations/{qid}/retry")
        assert retried.status_code == 200
        assert retried.json()["status"] == "PENDING"

        audit = client.get("/api/audit", params={"entity_type": "quotation", "entity_id": qid})
        assert audit.status_code == 200
        actions = {a["action"] for a in audit.json()}
        assert "CREATE" in actions
        assert "RETRY" in actions

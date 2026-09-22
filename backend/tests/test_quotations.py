from pathlib import Path

from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.main import app
from app.models import Quotation, QuotationStatus


def _payload(customer_id: str = "CUS-002", quantity: float = 10):
    return {
        "customer_id": customer_id,
        "items": [
            {
                "product_name": "Chem A",
                "specification": "99%",
                "quantity": quantity,
                "unit_price": 1000,
            }
        ],
        "payment_terms": "30 days",
        "delivery_terms": "7 days",
        "note": "phase5-test",
    }


def _close_active(customer_id: str) -> None:
    db = SessionLocal()
    try:
        rows = (
            db.query(Quotation)
            .filter(
                Quotation.customer_id == customer_id,
                Quotation.status.in_([QuotationStatus.PENDING, QuotationStatus.PROCESSING]),
            )
            .all()
        )
        for row in rows:
            row.status = QuotationStatus.FAILED
            row.error_message = "cleared by test"
        db.commit()
    finally:
        db.close()


def test_validation_anti_duplicate_retry_and_missing_download():
    _close_active("CUS-002")

    with TestClient(app) as client:
        assert client.post("/api/quotations", json=_payload(quantity=0)).status_code == 422

        first = client.post("/api/quotations", json=_payload())
        assert first.status_code == 201
        qid = first.json()["id"]
        assert first.json()["status"] == "PENDING"

        second = client.post("/api/quotations", json=_payload())
        assert second.status_code == 200
        assert second.json()["id"] == qid

        claimed = client.get("/api/internal/jobs/next")
        assert claimed.status_code == 200
        assert claimed.json()["id"] == qid
        assert claimed.json()["status"] == "PROCESSING"

        failed = client.post(
            f"/api/internal/jobs/{qid}/fail",
            json={"error_message": "simulated worker failure"},
        )
        assert failed.status_code == 200
        assert failed.json()["status"] == "FAILED"

        retried = client.post(f"/api/quotations/{qid}/retry")
        assert retried.status_code == 200
        assert retried.json()["status"] == "PENDING"

        claimed_again = client.get("/api/internal/jobs/next")
        assert claimed_again.status_code == 200
        assert claimed_again.json()["id"] == qid

        missing = Path("missing-phase5.docx")
        completed = client.post(
            f"/api/internal/jobs/{qid}/complete",
            json={"output_path": str(missing.resolve())},
        )
        assert completed.status_code == 200
        assert client.get(f"/api/quotations/{qid}/download").status_code == 404

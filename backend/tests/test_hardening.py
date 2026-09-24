from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.config import PROJECT_ROOT
from app.core.database import SessionLocal, engine
from app.core.migrate import ensure_schema
from app.main import app
from app.models import Quotation, QuotationStatus


def _close_all_active() -> None:
    db = SessionLocal()
    try:
        for row in db.query(Quotation).filter(
            Quotation.status.in_([QuotationStatus.PENDING, QuotationStatus.PROCESSING])
        ):
            row.status = QuotationStatus.FAILED
            row.error_message = "cleared"
        db.commit()
    finally:
        db.close()


def test_validation_and_business_rules_and_idempotency():
    ensure_schema(engine)
    _close_all_active()

    with TestClient(app) as client:
        # invalid note length
        long_note = "x" * 2001
        r = client.post(
            "/api/quotations",
            json={
                "customer_id": "CUS-001",
                "items": [
                    {
                        "product_name": "A",
                        "specification": "1",
                        "quantity": 1,
                        "unit_price": 1,
                    }
                ],
                "payment_terms": "30",
                "delivery_terms": "7",
                "note": long_note,
            },
        )
        assert r.status_code == 422

        # invalid quantity
        assert (
            client.post(
                "/api/quotations",
                json={
                    "customer_id": "CUS-001",
                    "items": [
                        {
                            "product_name": "A",
                            "specification": "1",
                            "quantity": -1,
                            "unit_price": 1,
                        }
                    ],
                    "payment_terms": "30",
                    "delivery_terms": "7",
                },
            ).status_code
            == 422
        )

        # unknown quotation
        assert client.get("/api/quotations/QT-NOPE").status_code == 404
        assert client.post("/api/quotations/QT-NOPE/retry").status_code == 400

        # idempotency key (unique per run — shared SQLite keeps prior keys)
        payload = {
            "customer_id": "CUS-001",
            "items": [
                {
                    "product_name": "A",
                    "specification": "1",
                    "quantity": 1,
                    "unit_price": 1,
                }
            ],
            "payment_terms": "30",
            "delivery_terms": "7",
            "note": "idem",
        }
        headers = {"Idempotency-Key": f"integ-key-{uuid4().hex}"}
        a = client.post("/api/quotations", json=payload, headers=headers)
        assert a.status_code == 201, a.text
        qid = a.json()["id"]
        b = client.post("/api/quotations", json=payload, headers=headers)
        assert b.status_code == 200
        assert b.json()["id"] == qid

        # cannot retry PENDING
        assert client.post(f"/api/quotations/{qid}/retry").status_code == 400

        # claim -> PROCESSING; cannot update/retry
        claimed = client.get("/api/internal/jobs/next")
        assert claimed.status_code == 200
        assert claimed.json()["id"] == qid
        assert client.put(f"/api/quotations/{qid}", json={"note": "x"}).status_code == 400
        assert client.post(f"/api/quotations/{qid}/retry").status_code == 400

        # fail then retry OK
        assert (
            client.post(
                f"/api/internal/jobs/{qid}/fail",
                json={"error_message": "boom"},
            ).status_code
            == 200
        )
        assert client.post(f"/api/quotations/{qid}/retry").status_code == 200

        # inactive customer cannot create
        cust = client.post(
            "/api/customers",
            json={
                "name": "Z",
                "company": "Z Co",
                "email": "z@ex.com",
                "phone": "1",
                "address": "a",
            },
        )
        cid = cust.json()["id"]
        client.post(f"/api/customers/{cid}/deactivate")
        blocked = client.post(
            "/api/quotations",
            json={
                "customer_id": cid,
                "items": [
                    {
                        "product_name": "A",
                        "specification": "1",
                        "quantity": 1,
                        "unit_price": 1,
                    }
                ],
                "payment_terms": "30",
                "delivery_terms": "7",
            },
        )
        assert blocked.status_code == 400

        # path traversal / wrong name rejected on complete
        _close_all_active()
        c = client.post(
            "/api/quotations",
            json={
                "customer_id": "CUS-002",
                "items": [
                    {
                        "product_name": "A",
                        "specification": "1",
                        "quantity": 1,
                        "unit_price": 1,
                    }
                ],
                "payment_terms": "30",
                "delivery_terms": "7",
                "note": "sec",
            },
        )
        q2 = c.json()["id"]
        client.get("/api/internal/jobs/next")
        evil = client.post(
            f"/api/internal/jobs/{q2}/complete",
            json={"output_path": str((PROJECT_ROOT / "README.md").resolve())},
        )
        assert evil.status_code == 400

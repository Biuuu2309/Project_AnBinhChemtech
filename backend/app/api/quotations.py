from pathlib import Path

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.files import ensure_file_readable, resolve_allowed_output_path
from app.models import Quotation
from app.schemas import (
    ProcessingAttemptOut,
    QuotationCreate,
    QuotationEventOut,
    QuotationOut,
    QuotationUpdate,
)
from app.services import quotation_service

router = APIRouter(prefix="/api/quotations", tags=["quotations"])


def _to_out(quotation: Quotation) -> QuotationOut:
    return QuotationOut(
        id=quotation.id,
        customer_id=quotation.customer_id,
        status=quotation.status.value,
        payment_terms=quotation.payment_terms,
        delivery_terms=quotation.delivery_terms,
        note=quotation.note,
        output_path=quotation.output_path,
        error_message=quotation.error_message,
        attempt_count=quotation.attempt_count or 0,
        created_at=quotation.created_at,
        updated_at=quotation.updated_at,
        items=quotation.items,
    )


@router.get("", response_model=list[QuotationOut])
def list_quotations(
    q: str | None = Query(default=None),
    status: str | None = Query(default=None),
    customer_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    try:
        rows = quotation_service.list_quotations(
            db, q=q, status=status, customer_id=customer_id
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return [_to_out(row) for row in rows]


@router.post("", response_model=QuotationOut)
def create_quotation(
    payload: QuotationCreate,
    response: Response,
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    try:
        quotation, created = quotation_service.create_quotation(
            db, payload, idempotency_key=idempotency_key
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    response.status_code = 201 if created else 200
    return _to_out(quotation)


@router.get("/{quotation_id}", response_model=QuotationOut)
def get_quotation(quotation_id: str, db: Session = Depends(get_db)):
    try:
        quotation = quotation_service.get_quotation(db, quotation_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _to_out(quotation)


@router.put("/{quotation_id}", response_model=QuotationOut)
def update_quotation(quotation_id: str, payload: QuotationUpdate, db: Session = Depends(get_db)):
    try:
        quotation = quotation_service.update_quotation(db, quotation_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_out(quotation)


@router.get("/{quotation_id}/history", response_model=list[QuotationEventOut])
def quotation_history(quotation_id: str, db: Session = Depends(get_db)):
    try:
        events = quotation_service.list_events(db, quotation_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return events


@router.get("/{quotation_id}/attempts", response_model=list[ProcessingAttemptOut])
def quotation_attempts(quotation_id: str, db: Session = Depends(get_db)):
    try:
        attempts = quotation_service.list_attempts(db, quotation_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return [
        ProcessingAttemptOut(
            id=a.id,
            quotation_id=a.quotation_id,
            attempt_no=a.attempt_no,
            status=a.status.value,
            error_message=a.error_message,
            output_path=a.output_path,
            started_at=a.started_at,
            finished_at=a.finished_at,
        )
        for a in attempts
    ]


@router.get("/{quotation_id}/download")
def download_quotation(quotation_id: str, db: Session = Depends(get_db)):
    try:
        quotation = quotation_service.record_download(db, quotation_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if not quotation.output_path:
        raise HTTPException(status_code=404, detail="Quotation file not ready")

    try:
        path = resolve_allowed_output_path(quotation.output_path, quotation_id=quotation_id)
        ensure_file_readable(path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=path.name,
    )


@router.post("/{quotation_id}/retry", response_model=QuotationOut)
def retry_quotation(quotation_id: str, db: Session = Depends(get_db)):
    try:
        quotation = quotation_service.retry_quotation(db, quotation_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_out(quotation)

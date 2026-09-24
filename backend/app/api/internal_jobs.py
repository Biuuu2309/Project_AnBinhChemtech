from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Quotation
from app.schemas import JobCompleteIn, JobFailIn, QuotationOut
from app.services import quotation_service

router = APIRouter(prefix="/api/internal/jobs", tags=["internal-jobs"])


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


@router.get("/next", response_model=None)
def next_job(db: Session = Depends(get_db)):
    quotation = quotation_service.claim_next_job(db)
    if not quotation:
        return Response(status_code=204)
    return _to_out(quotation)


@router.post("/{quotation_id}/complete", response_model=QuotationOut)
def complete_job(quotation_id: str, payload: JobCompleteIn, db: Session = Depends(get_db)):
    try:
        quotation = quotation_service.complete_job(db, quotation_id, payload.output_path)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_out(quotation)


@router.post("/{quotation_id}/fail", response_model=QuotationOut)
def fail_job(quotation_id: str, payload: JobFailIn, db: Session = Depends(get_db)):
    try:
        quotation = quotation_service.fail_job(db, quotation_id, payload.error_message)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_out(quotation)

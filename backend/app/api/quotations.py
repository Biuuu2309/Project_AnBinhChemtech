from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Quotation
from app.schemas import QuotationCreate, QuotationOut
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
        created_at=quotation.created_at,
        updated_at=quotation.updated_at,
        items=quotation.items,
    )


@router.post("", response_model=QuotationOut)
def create_quotation(payload: QuotationCreate, response: Response, db: Session = Depends(get_db)):
    try:
        quotation, created = quotation_service.create_quotation(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    response.status_code = 201 if created else 200
    return _to_out(quotation)


@router.get("/{quotation_id}", response_model=QuotationOut)
def get_quotation(quotation_id: str, db: Session = Depends(get_db)):
    quotation = db.get(Quotation, quotation_id)
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")
    return _to_out(quotation)


@router.get("/{quotation_id}/download")
def download_quotation(quotation_id: str, db: Session = Depends(get_db)):
    quotation = db.get(Quotation, quotation_id)
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")
    if not quotation.output_path:
        raise HTTPException(status_code=404, detail="Quotation file not ready")

    path = Path(quotation.output_path)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Quotation file missing on disk")

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

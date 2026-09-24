from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import AuditLogOut
from app.services import audit_service

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("", response_model=list[AuditLogOut])
def list_audit(
    entity_type: str | None = Query(default=None),
    entity_id: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    rows = audit_service.list_audit(
        db, entity_type=entity_type, entity_id=entity_id, limit=limit
    )
    return [
        AuditLogOut(
            id=r.id,
            action=r.action.value,
            entity_type=r.entity_type,
            entity_id=r.entity_id,
            detail=r.detail,
            created_at=r.created_at,
        )
        for r in rows
    ]

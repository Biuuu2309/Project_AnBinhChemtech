import logging

from sqlalchemy.orm import Session

from app.models import AuditAction, AuditLog

logger = logging.getLogger(__name__)


def record_audit(
    db: Session,
    *,
    action: AuditAction,
    entity_type: str,
    entity_id: str,
    detail: str | None = None,
    commit: bool = False,
) -> AuditLog:
    row = AuditLog(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        detail=detail,
    )
    db.add(row)
    if commit:
        db.commit()
        db.refresh(row)
    logger.info("audit action=%s entity=%s:%s detail=%s", action.value, entity_type, entity_id, detail)
    return row


def list_audit(
    db: Session,
    *,
    entity_type: str | None = None,
    entity_id: str | None = None,
    limit: int = 100,
) -> list[AuditLog]:
    q = db.query(AuditLog).order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
    if entity_type:
        q = q.filter(AuditLog.entity_type == entity_type)
    if entity_id:
        q = q.filter(AuditLog.entity_id == entity_id)
    return q.limit(limit).all()

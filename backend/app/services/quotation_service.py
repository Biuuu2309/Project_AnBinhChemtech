import logging
from datetime import datetime, timezone

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.files import ensure_file_readable, resolve_allowed_output_path
from app.models import (
    AttemptStatus,
    AuditAction,
    Customer,
    ProcessingAttempt,
    Quotation,
    QuotationEvent,
    QuotationItem,
    QuotationStatus,
)
from app.schemas import QuotationCreate, QuotationUpdate
from app.services import audit_service

logger = logging.getLogger(__name__)


def seed_customers(db: Session) -> None:
    if db.get(Customer, "CUS-001"):
        # ensure soft-delete flag present on legacy rows
        for row in db.query(Customer).all():
            if getattr(row, "is_active", None) is None:
                row.is_active = True
        db.commit()
        return

    customers = [
        Customer(
            id="CUS-001",
            name="Nguyen Van A",
            company="ABC Chemicals Co.",
            email="a.nguyen@abc-chem.vn",
            phone="+84 90 111 2233",
            address="12 Nguyen Hue, District 1, HCMC",
            is_active=True,
        ),
        Customer(
            id="CUS-002",
            name="Tran Thi B",
            company="Delta Industrial Ltd.",
            email="b.tran@delta-ind.vn",
            phone="+84 91 444 5566",
            address="88 Le Loi, Hai Ba Trung, Hanoi",
            is_active=True,
        ),
    ]
    db.add_all(customers)
    db.commit()
    logger.info("Seeded %s customers", len(customers))


def _next_quotation_id(db: Session) -> str:
    year = datetime.now().year
    prefix = f"QT-{year}-"
    count = db.query(Quotation).filter(Quotation.id.like(f"{prefix}%")).count()
    return f"{prefix}{count + 1:03d}"


def _add_event(
    db: Session,
    quotation: Quotation,
    *,
    from_status: str | None,
    to_status: str,
    message: str,
    error_message: str | None = None,
) -> None:
    db.add(
        QuotationEvent(
            quotation_id=quotation.id,
            from_status=from_status,
            to_status=to_status,
            message=message,
            error_message=error_message,
        )
    )


def _load_quotation(db: Session, quotation_id: str) -> Quotation:
    quotation = (
        db.query(Quotation)
        .options(joinedload(Quotation.items))
        .filter(Quotation.id == quotation_id)
        .one_or_none()
    )
    if not quotation:
        raise ValueError(f"Quotation not found: {quotation_id}")
    return quotation


def list_quotations(
    db: Session,
    *,
    q: str | None = None,
    status: str | None = None,
    customer_id: str | None = None,
) -> list[Quotation]:
    query = db.query(Quotation).options(selectinload(Quotation.items))
    if status:
        query = query.filter(Quotation.status == QuotationStatus(status))
    if customer_id:
        query = query.filter(Quotation.customer_id == customer_id)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(or_(Quotation.id.ilike(like), Quotation.note.ilike(like)))
    return query.order_by(Quotation.created_at.desc()).all()


def create_quotation(
    db: Session,
    payload: QuotationCreate,
    *,
    idempotency_key: str | None = None,
) -> tuple[Quotation, bool]:
    customer = db.get(Customer, payload.customer_id)
    if not customer:
        raise ValueError(f"Customer not found: {payload.customer_id}")
    if not getattr(customer, "is_active", True):
        raise ValueError(f"Customer is inactive: {payload.customer_id}")

    key = (idempotency_key or "").strip() or None
    if key:
        if len(key) > 100:
            raise ValueError("Idempotency-Key too long (max 100)")
        existing = (
            db.query(Quotation)
            .options(joinedload(Quotation.items))
            .filter(Quotation.idempotency_key == key)
            .one_or_none()
        )
        if existing:
            logger.info(
                "quotation_idempotent_hit id=%s key=%s status=%s",
                existing.id,
                key,
                existing.status.value,
            )
            return existing, False

    active = (
        db.query(Quotation)
        .options(joinedload(Quotation.items))
        .filter(
            Quotation.customer_id == payload.customer_id,
            Quotation.status.in_([QuotationStatus.PENDING, QuotationStatus.PROCESSING]),
        )
        .order_by(Quotation.created_at.desc())
        .first()
    )
    if active:
        logger.info(
            "quotation_deduplicated id=%s customer_id=%s status=%s",
            active.id,
            payload.customer_id,
            active.status.value,
        )
        return active, False

    quotation = Quotation(
        id=_next_quotation_id(db),
        customer_id=payload.customer_id,
        status=QuotationStatus.PENDING,
        payment_terms=payload.payment_terms,
        delivery_terms=payload.delivery_terms,
        note=payload.note,
        attempt_count=0,
        idempotency_key=key,
    )
    for item in payload.items:
        quotation.items.append(
            QuotationItem(
                product_name=item.product_name,
                specification=item.specification,
                quantity=item.quantity,
                unit_price=item.unit_price,
            )
        )

    db.add(quotation)
    db.flush()
    _add_event(
        db,
        quotation,
        from_status=None,
        to_status=QuotationStatus.PENDING.value,
        message="Quotation created",
    )
    audit_service.record_audit(
        db,
        action=AuditAction.CREATE,
        entity_type="quotation",
        entity_id=quotation.id,
        detail=f"customer={payload.customer_id}",
    )
    db.commit()
    logger.info(
        "quotation_created id=%s status=PENDING idempotency_key=%s",
        quotation.id,
        "set" if key else "none",
    )
    return _load_quotation(db, quotation.id), True


def update_quotation(db: Session, quotation_id: str, payload: QuotationUpdate) -> Quotation:
    quotation = _load_quotation(db, quotation_id)
    if quotation.status == QuotationStatus.COMPLETED:
        raise ValueError("COMPLETED quotations cannot be updated")
    if quotation.status == QuotationStatus.PROCESSING:
        raise ValueError("PROCESSING quotations cannot be updated")
    if quotation.status not in (QuotationStatus.PENDING, QuotationStatus.FAILED):
        raise ValueError("Only PENDING or FAILED quotations can be updated")

    data = payload.model_dump(exclude_unset=True)
    if not data:
        return quotation
    if "payment_terms" in data and data["payment_terms"] is not None:
        quotation.payment_terms = data["payment_terms"]
    if "delivery_terms" in data and data["delivery_terms"] is not None:
        quotation.delivery_terms = data["delivery_terms"]
    if "note" in data:
        quotation.note = data["note"]
    if "items" in data and data["items"] is not None:
        quotation.items.clear()
        for item in payload.items or []:
            quotation.items.append(
                QuotationItem(
                    product_name=item.product_name,
                    specification=item.specification,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                )
            )

    _add_event(
        db,
        quotation,
        from_status=quotation.status.value,
        to_status=quotation.status.value,
        message="Quotation updated",
    )
    audit_service.record_audit(
        db,
        action=AuditAction.UPDATE,
        entity_type="quotation",
        entity_id=quotation.id,
        detail=",".join(data.keys()),
    )
    db.commit()
    logger.info("quotation_updated id=%s status=%s fields=%s", quotation_id, quotation.status.value, list(data.keys()))
    return _load_quotation(db, quotation_id)


def claim_next_job(db: Session) -> Quotation | None:
    quotation = (
        db.query(Quotation)
        .options(joinedload(Quotation.items))
        .filter(Quotation.status == QuotationStatus.PENDING)
        .order_by(Quotation.created_at.asc())
        .first()
    )
    if not quotation:
        return None

    from_status = quotation.status.value
    quotation.status = QuotationStatus.PROCESSING
    quotation.error_message = None
    quotation.attempt_count = (quotation.attempt_count or 0) + 1
    attempt_no = quotation.attempt_count

    db.add(
        ProcessingAttempt(
            quotation_id=quotation.id,
            attempt_no=attempt_no,
            status=AttemptStatus.STARTED,
        )
    )
    _add_event(
        db,
        quotation,
        from_status=from_status,
        to_status=QuotationStatus.PROCESSING.value,
        message=f"Worker claimed job (attempt #{attempt_no})",
    )
    quotation_id = quotation.id
    db.commit()
    attempt = _latest_started_attempt(db, quotation_id)
    logger.info(
        "automation_started quotation_id=%s status=PROCESSING attempt_no=%s attempt_id=%s",
        quotation_id,
        attempt_no,
        attempt.id if attempt else None,
    )
    return _load_quotation(db, quotation_id)


def _latest_started_attempt(db: Session, quotation_id: str) -> ProcessingAttempt | None:
    return (
        db.query(ProcessingAttempt)
        .filter(
            ProcessingAttempt.quotation_id == quotation_id,
            ProcessingAttempt.status == AttemptStatus.STARTED,
        )
        .order_by(ProcessingAttempt.attempt_no.desc())
        .first()
    )


def complete_job(db: Session, quotation_id: str, output_path: str) -> Quotation:
    quotation = db.get(Quotation, quotation_id)
    if not quotation:
        raise ValueError(f"Quotation not found: {quotation_id}")
    if quotation.status != QuotationStatus.PROCESSING:
        raise ValueError(f"Quotation {quotation_id} is not PROCESSING")

    safe_path = resolve_allowed_output_path(output_path, quotation_id=quotation_id)
    ensure_file_readable(safe_path)

    from_status = quotation.status.value
    quotation.status = QuotationStatus.COMPLETED
    quotation.output_path = str(safe_path)
    quotation.error_message = None

    attempt = _latest_started_attempt(db, quotation_id)
    if attempt:
        attempt.status = AttemptStatus.SUCCEEDED
        attempt.output_path = str(safe_path)
        attempt.finished_at = datetime.now(timezone.utc)

    _add_event(
        db,
        quotation,
        from_status=from_status,
        to_status=QuotationStatus.COMPLETED.value,
        message="Quotation file generated",
    )
    db.commit()
    logger.info(
        "quotation_completed quotation_id=%s status=COMPLETED attempt_id=%s file=%s",
        quotation.id,
        attempt.id if attempt else None,
        safe_path.name,
    )
    return _load_quotation(db, quotation_id)


def fail_job(db: Session, quotation_id: str, error_message: str) -> Quotation:
    quotation = db.get(Quotation, quotation_id)
    if not quotation:
        raise ValueError(f"Quotation not found: {quotation_id}")
    if quotation.status != QuotationStatus.PROCESSING:
        raise ValueError(f"Quotation {quotation_id} is not PROCESSING")

    from_status = quotation.status.value
    quotation.status = QuotationStatus.FAILED
    quotation.error_message = error_message[:2000]

    attempt = _latest_started_attempt(db, quotation_id)
    if attempt:
        attempt.status = AttemptStatus.FAILED
        attempt.error_message = error_message[:2000]
        attempt.finished_at = datetime.now(timezone.utc)

    _add_event(
        db,
        quotation,
        from_status=from_status,
        to_status=QuotationStatus.FAILED.value,
        message="Processing failed",
        error_message=error_message[:2000],
    )
    db.commit()
    logger.info(
        "quotation_failed quotation_id=%s status=FAILED attempt_id=%s error=%s",
        quotation.id,
        attempt.id if attempt else None,
        (error_message or "")[:200],
    )
    return _load_quotation(db, quotation_id)


def retry_quotation(db: Session, quotation_id: str) -> Quotation:
    quotation = db.get(Quotation, quotation_id)
    if not quotation:
        raise ValueError(f"Quotation not found: {quotation_id}")
    if quotation.status == QuotationStatus.PROCESSING:
        raise ValueError("Cannot retry a PROCESSING quotation")
    if quotation.status == QuotationStatus.COMPLETED:
        raise ValueError("Cannot retry a COMPLETED quotation")
    if quotation.status != QuotationStatus.FAILED:
        raise ValueError("Only FAILED quotations can be retried")

    from_status = quotation.status.value
    quotation.status = QuotationStatus.PENDING
    quotation.error_message = None
    quotation.output_path = None

    _add_event(
        db,
        quotation,
        from_status=from_status,
        to_status=QuotationStatus.PENDING.value,
        message="Retry requested — waiting for worker",
    )
    audit_service.record_audit(
        db,
        action=AuditAction.RETRY,
        entity_type="quotation",
        entity_id=quotation.id,
        detail="FAILED -> PENDING",
    )
    db.commit()
    logger.info("quotation_retry quotation_id=%s status=PENDING from=%s", quotation.id, from_status)
    return _load_quotation(db, quotation_id)


def get_quotation(db: Session, quotation_id: str) -> Quotation:
    return _load_quotation(db, quotation_id)


def list_events(db: Session, quotation_id: str) -> list[QuotationEvent]:
    _load_quotation(db, quotation_id)
    return (
        db.query(QuotationEvent)
        .filter(QuotationEvent.quotation_id == quotation_id)
        .order_by(QuotationEvent.created_at.asc(), QuotationEvent.id.asc())
        .all()
    )


def list_attempts(db: Session, quotation_id: str) -> list[ProcessingAttempt]:
    _load_quotation(db, quotation_id)
    return (
        db.query(ProcessingAttempt)
        .filter(ProcessingAttempt.quotation_id == quotation_id)
        .order_by(ProcessingAttempt.attempt_no.asc())
        .all()
    )


def record_download(db: Session, quotation_id: str) -> Quotation:
    quotation = _load_quotation(db, quotation_id)
    audit_service.record_audit(
        db,
        action=AuditAction.DOWNLOAD,
        entity_type="quotation",
        entity_id=quotation.id,
        detail=quotation.output_path,
        commit=True,
    )
    return quotation

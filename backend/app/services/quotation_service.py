import logging
from datetime import datetime

from sqlalchemy.orm import Session, joinedload

from app.models import Customer, Quotation, QuotationItem, QuotationStatus
from app.schemas import QuotationCreate

logger = logging.getLogger(__name__)


def seed_customers(db: Session) -> None:
    if db.get(Customer, "CUS-001"):
        return

    customers = [
        Customer(
            id="CUS-001",
            name="Nguyen Van A",
            company="ABC Chemicals Co.",
            email="a.nguyen@abc-chem.vn",
            phone="+84 90 111 2233",
            address="12 Nguyen Hue, District 1, HCMC",
        ),
        Customer(
            id="CUS-002",
            name="Tran Thi B",
            company="Delta Industrial Ltd.",
            email="b.tran@delta-ind.vn",
            phone="+84 91 444 5566",
            address="88 Le Loi, Hai Ba Trung, Hanoi",
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


def create_quotation(db: Session, payload: QuotationCreate) -> tuple[Quotation, bool]:
    customer = db.get(Customer, payload.customer_id)
    if not customer:
        raise ValueError(f"Customer not found: {payload.customer_id}")

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
    db.commit()
    quotation_id = quotation.id
    logger.info("quotation_created id=%s status=PENDING", quotation_id)
    return (
        db.query(Quotation)
        .options(joinedload(Quotation.items))
        .filter(Quotation.id == quotation_id)
        .one(),
        True,
    )


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

    quotation.status = QuotationStatus.PROCESSING
    quotation.error_message = None
    quotation_id = quotation.id
    db.commit()
    logger.info("automation_started id=%s status=PROCESSING", quotation_id)
    return (
        db.query(Quotation)
        .options(joinedload(Quotation.items))
        .filter(Quotation.id == quotation_id)
        .one()
    )


def complete_job(db: Session, quotation_id: str, output_path: str) -> Quotation:
    quotation = db.get(Quotation, quotation_id)
    if not quotation:
        raise ValueError(f"Quotation not found: {quotation_id}")
    if quotation.status != QuotationStatus.PROCESSING:
        raise ValueError(f"Quotation {quotation_id} is not PROCESSING")

    quotation.status = QuotationStatus.COMPLETED
    quotation.output_path = output_path
    quotation.error_message = None
    db.commit()
    db.refresh(quotation)
    logger.info("quotation_completed id=%s path=%s", quotation.id, output_path)
    return quotation


def fail_job(db: Session, quotation_id: str, error_message: str) -> Quotation:
    quotation = db.get(Quotation, quotation_id)
    if not quotation:
        raise ValueError(f"Quotation not found: {quotation_id}")
    if quotation.status != QuotationStatus.PROCESSING:
        raise ValueError(f"Quotation {quotation_id} is not PROCESSING")

    quotation.status = QuotationStatus.FAILED
    quotation.error_message = error_message
    db.commit()
    db.refresh(quotation)
    logger.info("quotation_failed id=%s error=%s", quotation.id, error_message)
    return quotation


def retry_quotation(db: Session, quotation_id: str) -> Quotation:
    quotation = db.get(Quotation, quotation_id)
    if not quotation:
        raise ValueError(f"Quotation not found: {quotation_id}")
    if quotation.status != QuotationStatus.FAILED:
        raise ValueError("Only FAILED quotations can be retried")

    quotation.status = QuotationStatus.PENDING
    quotation.error_message = None
    quotation.output_path = None
    db.commit()
    db.refresh(quotation)
    logger.info("quotation_retry id=%s status=%s", quotation.id, quotation.status.value)
    return quotation

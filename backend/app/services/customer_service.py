import logging

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import AuditAction, Customer
from app.schemas import CustomerCreate, CustomerUpdate
from app.services import audit_service

logger = logging.getLogger(__name__)


def _next_customer_id(db: Session) -> str:
    count = db.query(Customer).count()
    return f"CUS-{count + 1:03d}"


def list_customers(
    db: Session,
    *,
    q: str | None = None,
    active_only: bool = True,
) -> list[Customer]:
    query = db.query(Customer)
    if active_only:
        query = query.filter(Customer.is_active.is_(True))
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Customer.id.ilike(like),
                Customer.name.ilike(like),
                Customer.company.ilike(like),
                Customer.email.ilike(like),
            )
        )
    return query.order_by(Customer.id).all()


def get_customer(db: Session, customer_id: str) -> Customer:
    customer = db.get(Customer, customer_id)
    if not customer:
        raise ValueError(f"Customer not found: {customer_id}")
    return customer


def create_customer(db: Session, payload: CustomerCreate) -> Customer:
    customer = Customer(
        id=_next_customer_id(db),
        name=payload.name,
        company=payload.company,
        email=payload.email,
        phone=payload.phone,
        address=payload.address,
        is_active=True,
    )
    db.add(customer)
    db.flush()
    audit_service.record_audit(
        db,
        action=AuditAction.CREATE,
        entity_type="customer",
        entity_id=customer.id,
        detail=customer.company,
    )
    db.commit()
    db.refresh(customer)
    logger.info("customer_created id=%s", customer.id)
    return customer


def update_customer(db: Session, customer_id: str, payload: CustomerUpdate) -> Customer:
    customer = get_customer(db, customer_id)
    data = payload.model_dump(exclude_unset=True)
    if not data:
        return customer
    for key, value in data.items():
        setattr(customer, key, value)
    audit_service.record_audit(
        db,
        action=AuditAction.UPDATE,
        entity_type="customer",
        entity_id=customer.id,
        detail=",".join(data.keys()),
    )
    db.commit()
    db.refresh(customer)
    logger.info("customer_updated id=%s fields=%s", customer.id, list(data.keys()))
    return customer


def deactivate_customer(db: Session, customer_id: str) -> Customer:
    customer = get_customer(db, customer_id)
    if not customer.is_active:
        return customer
    customer.is_active = False
    audit_service.record_audit(
        db,
        action=AuditAction.DEACTIVATE,
        entity_type="customer",
        entity_id=customer.id,
        detail="soft delete",
    )
    db.commit()
    db.refresh(customer)
    logger.info("customer_deactivated id=%s", customer.id)
    return customer

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _strip(v: str | None) -> str | None:
    if v is None:
        return None
    s = v.strip()
    return s if s else None


class CustomerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    company: str = Field(min_length=1, max_length=200)
    email: str = Field(min_length=3, max_length=200)
    phone: str = Field(min_length=1, max_length=50)
    address: str = Field(min_length=1, max_length=300)

    @field_validator("name", "company", "email", "phone", "address", mode="before")
    @classmethod
    def strip_text(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v


class CustomerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    company: str | None = Field(default=None, min_length=1, max_length=200)
    email: str | None = Field(default=None, min_length=3, max_length=200)
    phone: str | None = Field(default=None, min_length=1, max_length=50)
    address: str | None = Field(default=None, min_length=1, max_length=300)

    @field_validator("name", "company", "email", "phone", "address", mode="before")
    @classmethod
    def strip_text(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v


class CustomerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    company: str
    email: str
    phone: str
    address: str
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None


class QuotationItemIn(BaseModel):
    product_name: str = Field(min_length=1, max_length=200)
    specification: str = Field(min_length=1, max_length=200)
    quantity: float = Field(gt=0)
    unit_price: float = Field(ge=0)

    @field_validator("product_name", "specification", mode="before")
    @classmethod
    def strip_text(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v


class QuotationItemOut(QuotationItemIn):
    model_config = ConfigDict(from_attributes=True)

    id: int


class QuotationCreate(BaseModel):
    customer_id: str = Field(min_length=1, max_length=32)
    items: list[QuotationItemIn] = Field(min_length=1, max_length=50)
    payment_terms: str = Field(min_length=1, max_length=200)
    delivery_terms: str = Field(min_length=1, max_length=200)
    note: str | None = Field(default=None, max_length=2000)

    @field_validator("customer_id", "payment_terms", "delivery_terms", mode="before")
    @classmethod
    def strip_required(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator("note", mode="before")
    @classmethod
    def strip_note(cls, v):
        return _strip(v) if isinstance(v, str) or v is None else v


class QuotationUpdate(BaseModel):
    items: list[QuotationItemIn] | None = Field(default=None, min_length=1, max_length=50)
    payment_terms: str | None = Field(default=None, min_length=1, max_length=200)
    delivery_terms: str | None = Field(default=None, min_length=1, max_length=200)
    note: str | None = Field(default=None, max_length=2000)

    @field_validator("payment_terms", "delivery_terms", mode="before")
    @classmethod
    def strip_optional(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator("note", mode="before")
    @classmethod
    def strip_note(cls, v):
        return _strip(v) if isinstance(v, str) or v is None else v


class QuotationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    customer_id: str
    status: str
    payment_terms: str
    delivery_terms: str
    note: str | None
    output_path: str | None
    error_message: str | None
    attempt_count: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None
    items: list[QuotationItemOut] = []


class QuotationEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    quotation_id: str
    from_status: str | None
    to_status: str
    message: str
    error_message: str | None
    created_at: datetime | None = None


class ProcessingAttemptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    quotation_id: str
    attempt_no: int
    status: str
    error_message: str | None
    output_path: str | None
    started_at: datetime | None = None
    finished_at: datetime | None = None


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    action: str
    entity_type: str
    entity_id: str
    detail: str | None
    created_at: datetime | None = None


class JobCompleteIn(BaseModel):
    output_path: str = Field(min_length=1, max_length=500)


class JobFailIn(BaseModel):
    error_message: str = Field(min_length=1, max_length=2000)

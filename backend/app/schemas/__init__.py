from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CustomerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    company: str
    email: str
    phone: str
    address: str


class QuotationItemIn(BaseModel):
    product_name: str = Field(min_length=1, max_length=200)
    specification: str = Field(min_length=1, max_length=200)
    quantity: float = Field(gt=0)
    unit_price: float = Field(ge=0)


class QuotationItemOut(QuotationItemIn):
    model_config = ConfigDict(from_attributes=True)

    id: int


class QuotationCreate(BaseModel):
    customer_id: str
    items: list[QuotationItemIn] = Field(min_length=1)
    payment_terms: str = Field(min_length=1, max_length=200)
    delivery_terms: str = Field(min_length=1, max_length=200)
    note: str | None = None


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
    created_at: datetime | None = None
    updated_at: datetime | None = None
    items: list[QuotationItemOut] = []


class JobCompleteIn(BaseModel):
    output_path: str = Field(min_length=1)


class JobFailIn(BaseModel):
    error_message: str = Field(min_length=1)

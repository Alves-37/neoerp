from datetime import datetime

from pydantic import BaseModel


class QuoteItemIn(BaseModel):
    product_id: int | None = None
    product_name: str
    qty: float
    unit_price: float


class QuoteItemOut(BaseModel):
    id: int
    product_id: int | None = None
    product_name: str
    qty: float
    unit_price: float
    line_net: float
    tax_rate: float
    line_tax: float
    line_gross: float

    class Config:
        from_attributes = True


class QuoteOut(BaseModel):
    id: int
    company_id: int
    cashier_id: int | None = None

    series: str
    number: int
    status: str

    customer_name: str | None = None
    customer_nuit: str | None = None

    currency: str
    net_total: float
    tax_total: float
    gross_total: float

    include_tax: bool = True
    discount_value: float = 0

    sale_id: int | None = None

    created_at: datetime
    updated_at: datetime

    items: list[QuoteItemOut] = []


class CreateQuotePayload(BaseModel):
    series: str = "A"
    customer_name: str | None = None
    customer_nuit: str | None = None
    currency: str = "MZN"

    include_tax: bool = True
    discount_value: float = 0

    items: list[QuoteItemIn]


class QuoteUpdatePayload(BaseModel):
    series: str | None = None
    customer_name: str | None = None
    customer_nuit: str | None = None
    currency: str | None = None

    include_tax: bool | None = None
    discount_value: float | None = None

    items: list[QuoteItemIn] | None = None


class ConvertQuotePayload(BaseModel):
    payment_method: str | None = "cash"
    paid: float | None = None

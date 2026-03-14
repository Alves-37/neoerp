from datetime import datetime

from pydantic import BaseModel


class CustomerUpsert(BaseModel):
    name: str
    nuit: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None


class FiscalDocumentLineOut(BaseModel):
    id: int
    product_id: int | None = None
    description: str
    qty: float
    unit_price: float
    line_net: float
    tax_rate: float
    line_tax: float
    line_gross: float

    class Config:
        from_attributes = True


class FiscalDocumentOut(BaseModel):
    id: int
    company_id: int
    branch_id: int
    sale_id: int | None = None
    cashier_id: int | None = None

    document_type: str
    series: str
    number: int
    status: str

    customer_id: int | None = None
    customer_name: str | None = None
    customer_nuit: str | None = None

    currency: str
    net_total: float
    tax_total: float
    gross_total: float

    issued_at: datetime

    cancelled_at: datetime | None = None
    cancelled_by: int | None = None
    cancel_reason: str | None = None

    lines: list[FiscalDocumentLineOut] = []


class IssueFromSalePayload(BaseModel):
    sale_id: int
    document_type: str  # invoice|receipt|ticket
    series: str = "A"
    customer_id: int | None = None
    customer: CustomerUpsert | None = None


class CancelFiscalDocumentPayload(BaseModel):
    reason: str | None = None

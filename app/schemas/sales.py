from datetime import datetime

from pydantic import BaseModel


class SaleItemCreate(BaseModel):
    product_id: int
    qty: float = 1
    price_at_sale: float
    cost_at_sale: float


class SaleCreate(BaseModel):
    sale_channel: str = "counter"
    table_number: int | None = None
    seat_number: int | None = None
    payment_method: str = "cash"
    include_tax: bool = True
    paid: float = 0
    items: list[SaleItemCreate]


class SaleVoidPayload(BaseModel):
    reason: str | None = None


class SaleEditPayload(BaseModel):
    include_tax: bool = True
    items: list[SaleItemCreate]


class SaleItemOut(BaseModel):
    id: int
    sale_id: int
    product_id: int
    product_name: str | None = None
    qty: float
    price_at_sale: float
    cost_at_sale: float
    line_total: float

    class Config:
        from_attributes = True


class SaleOut(BaseModel):
    id: int
    company_id: int
    branch_id: int
    business_type: str
    cashier_id: int | None = None
    cash_session_id: int | None = None
    cashier_name: str | None = None
    sale_channel: str
    table_number: int | None = None
    seat_number: int | None = None
    total: float
    net_total: float = 0
    tax_total: float = 0
    include_tax: bool = True
    paid: float
    change: float
    payment_method: str
    status: str
    created_at: datetime
    items: list[SaleItemOut] = []

    class Config:
        from_attributes = True

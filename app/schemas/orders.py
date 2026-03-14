from datetime import datetime

from pydantic import BaseModel


class OrderItemCreate(BaseModel):
    product_id: int
    qty: float = 1
    price_at_order: float
    cost_at_order: float


class OrderCreate(BaseModel):
    table_number: int
    seat_number: int
    items: list[OrderItemCreate]


class OrderUpdate(BaseModel):
    status: str | None = None


class OrderItemOut(BaseModel):
    id: int
    order_id: int
    product_id: int
    qty: float
    price_at_order: float
    cost_at_order: float
    line_total: float

    class Config:
        from_attributes = True


class OrderOut(BaseModel):
    id: int
    company_id: int
    branch_id: int
    business_type: str
    status: str
    table_number: int
    seat_number: int
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemOut] = []

    class Config:
        from_attributes = True


class OrderClosePayload(BaseModel):
    payment_method: str = "cash"
    paid: float = 0

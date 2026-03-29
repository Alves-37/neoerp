from datetime import datetime
from typing import Any

from pydantic import BaseModel


class OrderItemOptionCreate(BaseModel):
    option_group_id: int
    option_id: int
    option_name: str
    price_adjustment: float
    ingredient_impact: dict[str, Any] = {}


class OrderItemCreate(BaseModel):
    product_id: int
    qty: float = 1
    price_at_order: float
    cost_at_order: float
    options: list[OrderItemOptionCreate] = []


class OrderCreate(BaseModel):
    table_number: int
    seat_number: int
    items: list[OrderItemCreate]


class OrderUpdate(BaseModel):
    status: str | None = None
    table_number: int | None = None
    seat_number: int | None = None
    items: list[OrderItemCreate] | None = None


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
    order_uuid: str | None = None
    order_type: str = "table"
    delivery_kind: str | None = None
    customer_name: str | None = None
    customer_phone: str | None = None
    delivery_address: str | None = None
    delivery_zone_name: str | None = None
    delivery_fee: float = 0
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

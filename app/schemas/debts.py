from datetime import datetime

from pydantic import BaseModel


class DebtItemCreate(BaseModel):
    product_id: int
    qty: float = 1
    price_at_debt: float
    cost_at_debt: float


class DebtCreate(BaseModel):
    customer_id: int | None = None
    customer_name: str | None = None
    customer_nuit: str | None = None
    include_tax: bool = True
    items: list[DebtItemCreate]


class DebtPayPayload(BaseModel):
    payment_method: str = "cash"
    paid: float = 0


class DebtItemOut(BaseModel):
    id: int
    debt_id: int
    product_id: int
    qty: float | None = 0
    price_at_debt: float | None = 0
    cost_at_debt: float | None = 0
    line_total: float | None = 0

    class Config:
        from_attributes = True


class DebtOut(BaseModel):
    id: int
    company_id: int
    branch_id: int
    cashier_id: int | None = None

    customer_id: int | None = None
    customer_name: str | None = None
    customer_nuit: str | None = None

    currency: str = "MZN"
    total: float
    net_total: float = 0
    tax_total: float = 0
    include_tax: bool = True

    status: str
    sale_id: int | None = None

    created_at: datetime
    paid_at: datetime | None = None

    items: list[DebtItemOut] = []

    class Config:
        from_attributes = True

from datetime import date, datetime

from pydantic import BaseModel


class ExpenseCreate(BaseModel):
    description: str
    amount: float
    due_date: date
    category_id: int | None = None


class ExpenseUpdate(BaseModel):
    description: str | None = None
    amount: float | None = None
    due_date: date | None = None
    category_id: int | None = None
    status: str | None = None


class ExpensePayRequest(BaseModel):
    paid_at: datetime | None = None


class ExpenseOut(BaseModel):
    id: int
    company_id: int
    branch_id: int
    establishment_id: int | None = None

    category_id: int | None = None
    category_name: str | None = None

    description: str
    amount: float
    due_date: date

    status: str
    paid_at: datetime | None = None
    paid_cash_session_id: int | None = None
    paid_by: int | None = None

    is_void: bool = False
    voided_at: datetime | None = None
    voided_by: int | None = None
    void_reason: str | None = None

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

from datetime import datetime

from pydantic import BaseModel


class CashSessionOpenRequest(BaseModel):
    opening_balance: float = 0


class CashSessionCloseRequest(BaseModel):
    closing_balance_counted: float
    notes: str | None = None


class CashSessionOut(BaseModel):
    id: int
    company_id: int
    branch_id: int
    opened_by: int
    opened_at: datetime
    opening_balance: float
    status: str
    closed_at: datetime | None = None
    closed_by: int | None = None
    closing_balance_expected: float = 0
    closing_balance_counted: float = 0
    difference: float = 0
    notes: str | None = None

    class Config:
        from_attributes = True


class CashSessionPaymentTotals(BaseModel):
    payment_method: str
    sales_count: int = 0
    gross_total: float = 0
    net_total: float = 0
    tax_total: float = 0


class CashSessionSummaryOut(BaseModel):
    cash_session_id: int
    company_id: int
    branch_id: int
    opened_by: int
    opened_at: datetime
    status: str
    closed_at: datetime | None = None

    opening_balance: float
    cash_sales_total: float = 0
    expected_cash: float = 0

    sales_count: int = 0
    gross_total: float = 0
    net_total: float = 0
    tax_total: float = 0

    by_payment_method: list[CashSessionPaymentTotals] = []

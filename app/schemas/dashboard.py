from datetime import date

from pydantic import BaseModel


class DashboardSummaryOut(BaseModel):
    products_total: int
    sales_today: float
    sales_month: float
    profit_today: float
    profit_month: float

    low_stock_default_count: int = 0
    low_stock_warehouse_count: int = 0
    stock_value_cost: float = 0
    stock_value_potential: float = 0


class SalesSeriesPointOut(BaseModel):
    day: date
    total: float


class ExpiryAlertItemOut(BaseModel):
    product_id: int
    name: str
    validade: str
    days_to_expire: int


class ExpiryAlertsOut(BaseModel):
    expired_count: int
    expiring_soon_count: int
    days_window: int
    items: list[ExpiryAlertItemOut]

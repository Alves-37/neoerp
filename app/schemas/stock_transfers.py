from datetime import datetime

from pydantic import BaseModel, Field


class StockTransferCreate(BaseModel):
    product_id: int
    from_location_id: int
    to_location_id: int
    qty: float = Field(gt=0)
    notes: str | None = None


class StockTransferOut(BaseModel):
    id: int
    company_id: int
    branch_id: int
    product_id: int
    from_location_id: int
    to_location_id: int
    qty: float
    notes: str | None = None
    created_by: int | None = None
    created_at: datetime

    class Config:
        from_attributes = True

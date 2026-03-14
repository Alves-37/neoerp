from datetime import datetime

from pydantic import BaseModel


class StockMovementOut(BaseModel):
    id: int
    company_id: int
    branch_id: int
    product_id: int
    location_id: int
    movement_type: str
    qty_delta: float
    reference_type: str | None = None
    reference_id: int | None = None
    notes: str | None = None
    created_by: int | None = None
    created_at: datetime

    class Config:
        from_attributes = True

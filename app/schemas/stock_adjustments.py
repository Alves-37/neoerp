from pydantic import BaseModel, Field


class StockAdjustmentCreate(BaseModel):
    product_id: int
    location_id: int
    qty_delta: float = Field(ne=0)
    notes: str | None = None

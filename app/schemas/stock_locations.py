from datetime import datetime

from pydantic import BaseModel


class StockLocationBase(BaseModel):
    type: str
    name: str
    is_default: bool = False
    is_active: bool = True


class StockLocationCreate(StockLocationBase):
    pass


class StockLocationUpdate(BaseModel):
    type: str | None = None
    name: str | None = None
    is_default: bool | None = None
    is_active: bool | None = None


class StockLocationOut(StockLocationBase):
    id: int
    company_id: int
    branch_id: int
    created_at: datetime

    class Config:
        from_attributes = True

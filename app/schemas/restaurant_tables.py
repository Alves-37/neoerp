from datetime import datetime

from pydantic import BaseModel


class RestaurantTableBase(BaseModel):
    number: int
    capacity: int = 4
    is_active: bool = True


class RestaurantTableCreate(RestaurantTableBase):
    pass


class RestaurantTableUpdate(BaseModel):
    number: int | None = None
    capacity: int | None = None
    is_active: bool | None = None


class RestaurantTableOut(RestaurantTableBase):
    id: int
    company_id: int
    branch_id: int
    created_at: datetime

    class Config:
        from_attributes = True

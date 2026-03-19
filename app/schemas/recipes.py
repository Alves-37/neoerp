from datetime import datetime

from pydantic import BaseModel


class RecipeItemIn(BaseModel):
    ingredient_product_id: int
    qty: float
    unit: str = "un"
    waste_percent: float = 0


class RecipeUpsertIn(BaseModel):
    items: list[RecipeItemIn]


class RecipeItemOut(BaseModel):
    id: int
    ingredient_product_id: int
    qty: float
    unit: str
    waste_percent: float

    class Config:
        from_attributes = True


class RecipeOut(BaseModel):
    id: int
    product_id: int
    yield_qty: float
    yield_unit: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    items: list[RecipeItemOut]

    class Config:
        from_attributes = True

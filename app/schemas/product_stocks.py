from pydantic import BaseModel


class ProductStockOut(BaseModel):
    id: int
    company_id: int
    branch_id: int
    product_id: int
    location_id: int
    qty_on_hand: float

    class Config:
        from_attributes = True


class LowStockRowOut(BaseModel):
    product_id: int
    product_name: str
    location_id: int
    location_name: str
    location_type: str
    qty_on_hand: float
    min_stock: float

    class Config:
        from_attributes = True

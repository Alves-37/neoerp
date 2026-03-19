from datetime import datetime

from pydantic import BaseModel, Field


class ProductBase(BaseModel):
    name: str
    sku: str | None = None
    barcode: str | None = None
    supplier_id: int | None = None
    default_location_id: int
    unit: str = "un"
    price: float = 0
    cost: float = 0
    tax_rate: float = 0
    min_stock: float = 0
    track_stock: bool = True
    is_service: bool = False
    is_active: bool = True
    show_in_menu: bool = False
    attributes: dict = Field(default_factory=dict)


class ProductCreate(ProductBase):
    establishment_id: int | None = None
    category_id: int | None = None
    category_name: str | None = None
    stock_qty: float | None = None


class ProductUpdate(BaseModel):
    category_id: int | None = None
    establishment_id: int | None = None
    name: str | None = None
    sku: str | None = None
    barcode: str | None = None
    supplier_id: int | None = None
    default_location_id: int | None = None
    unit: str | None = None
    price: float | None = None
    cost: float | None = None
    tax_rate: float | None = None
    min_stock: float | None = None
    track_stock: bool | None = None
    is_service: bool | None = None
    is_active: bool | None = None
    show_in_menu: bool | None = None
    attributes: dict | None = None
    stock_qty: float | None = None


class ProductOut(ProductBase):
    id: int
    company_id: int
    establishment_id: int | None = None
    category_id: int | None
    supplier_id: int | None = None
    business_type: str
    image_url: str | None = None
    stock_qty: float | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductImageOut(BaseModel):
    id: int
    product_id: int
    company_id: int
    file_path: str
    url: str
    created_at: datetime

    class Config:
        from_attributes = True

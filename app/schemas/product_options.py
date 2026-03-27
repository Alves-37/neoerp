from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ProductOptionGroupBase(BaseModel):
    name: str = Field(..., max_length=100)
    display_type: str = Field(default="radio", pattern="^(radio|checkbox|select)$")
    is_required: bool = Field(default=False)
    min_selections: int = Field(default=0, ge=0)
    max_selections: int = Field(default=1, ge=1)
    sort_order: int = Field(default=0, ge=0)


class ProductOptionGroupCreate(ProductOptionGroupBase):
    product_id: int


class ProductOptionGroupUpdate(ProductOptionGroupBase):
    pass


class ProductOptionGroupOut(ProductOptionGroupBase):
    id: int
    company_id: int
    branch_id: int
    product_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductOptionBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: str | None = Field(None, max_length=200)
    option_type: str = Field(default="addon", pattern="^(variant|addon|removal)$")
    price_adjustment: float = Field(default=0, ge=0)
    adjustment_type: str = Field(default="fixed", pattern="^(fixed|percentage)$")
    ingredient_impact: dict[str, Any] = Field(default_factory=dict)
    ingredient_remove: dict[str, Any] = Field(default_factory=dict)
    ingredient_multiplier: dict[str, Any] = Field(default_factory=dict)
    sort_order: int = Field(default=0, ge=0)


class ProductOptionCreate(ProductOptionBase):
    option_group_id: int


class ProductOptionUpdate(ProductOptionBase):
    pass


class ProductOptionOut(ProductOptionBase):
    id: int
    company_id: int
    branch_id: int
    option_group_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductOptionGroupWithOptionsOut(ProductOptionGroupOut):
    options: list[ProductOptionOut] = Field(default_factory=list)


class SaleItemOptionOut(BaseModel):
    id: int
    sale_item_id: int
    option_group_id: int
    option_id: int
    option_name: str
    price_adjustment: float
    ingredient_impact: dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class SaleItemWithOptionsOut(BaseModel):
    sale_item_id: int
    product_id: int
    product_name: str
    quantity: int
    unit_price: float
    options: list[SaleItemOptionOut] = Field(default_factory=list)
    total_with_options: float

    class Config:
        from_attributes = True

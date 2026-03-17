from datetime import datetime

from pydantic import BaseModel


class ProductCategoryCreate(BaseModel):
    name: str
    business_type: str | None = None


class ProductCategoryUpdate(BaseModel):
    name: str


class ProductCategoryOut(BaseModel):
    id: int
    company_id: int
    business_type: str
    name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

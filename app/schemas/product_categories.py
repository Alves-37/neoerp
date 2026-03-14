from datetime import datetime

from pydantic import BaseModel


class ProductCategoryOut(BaseModel):
    id: int
    company_id: int
    business_type: str
    name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

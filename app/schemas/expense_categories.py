from datetime import datetime

from pydantic import BaseModel


class ExpenseCategoryCreate(BaseModel):
    name: str


class ExpenseCategoryUpdate(BaseModel):
    name: str | None = None


class ExpenseCategoryOut(BaseModel):
    id: int
    company_id: int
    branch_id: int
    name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

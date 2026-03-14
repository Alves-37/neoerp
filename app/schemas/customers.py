from datetime import datetime

from pydantic import BaseModel


class CustomerBase(BaseModel):
    name: str
    nuit: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    name: str | None = None
    nuit: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None


class CustomerOut(CustomerBase):
    id: int
    company_id: int
    branch_id: int
    created_at: datetime

    class Config:
        from_attributes = True

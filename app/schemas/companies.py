from datetime import datetime

from pydantic import BaseModel


class CompanyCreate(BaseModel):
    name: str


class CompanyUpdate(BaseModel):
    name: str | None = None
    business_type: str | None = None
    nuit: str | None = None
    email: str | None = None
    phone: str | None = None
    province: str | None = None
    city: str | None = None
    address: str | None = None
    logo_url: str | None = None


class CompanyOut(BaseModel):
    id: int
    name: str
    business_type: str
    nuit: str | None = None
    email: str | None = None
    phone: str | None = None
    province: str | None = None
    city: str | None = None
    address: str | None = None
    logo_url: str | None = None
    owner_id: int | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

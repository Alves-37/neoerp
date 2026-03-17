from datetime import datetime

from pydantic import BaseModel


class EstablishmentBase(BaseModel):
    name: str
    is_active: bool = True


class EstablishmentCreate(EstablishmentBase):
    branch_id: int


class EstablishmentUpdate(BaseModel):
    name: str | None = None
    is_active: bool | None = None


class EstablishmentOut(EstablishmentBase):
    id: int
    company_id: int
    branch_id: int
    created_at: datetime

    class Config:
        from_attributes = True

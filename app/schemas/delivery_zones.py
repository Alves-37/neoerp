from datetime import datetime

from pydantic import BaseModel


class DeliveryZoneBase(BaseModel):
    branch_id: int
    name: str
    fee: float = 0
    keywords: list[str] = []
    is_active: bool = True


class DeliveryZoneCreate(DeliveryZoneBase):
    pass


class DeliveryZoneUpdate(BaseModel):
    branch_id: int | None = None
    name: str | None = None
    fee: float | None = None
    keywords: list[str] | None = None
    is_active: bool | None = None


class DeliveryZoneOut(DeliveryZoneBase):
    id: int
    company_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PublicDeliveryZoneOut(BaseModel):
    id: int
    name: str
    fee: float
    keywords: list[str] = []

from datetime import datetime

from pydantic import BaseModel


class BranchBase(BaseModel):
    name: str
    business_type: str = "retail"
    is_active: bool = True


class BranchCreate(BranchBase):
    pass


class BranchUpdate(BaseModel):
    name: str | None = None
    business_type: str | None = None
    is_active: bool | None = None


class BranchOut(BranchBase):
    id: int
    company_id: int
    created_at: datetime

    class Config:
        from_attributes = True

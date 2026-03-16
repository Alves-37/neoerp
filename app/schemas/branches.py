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
    public_menu_enabled: bool | None = None
    public_menu_subdomain: str | None = None
    public_menu_custom_domain: str | None = None


class BranchOut(BranchBase):
    id: int
    company_id: int
    public_menu_enabled: bool = False
    public_menu_subdomain: str | None = None
    public_menu_custom_domain: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True

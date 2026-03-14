from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserRoleBase(BaseModel):
    name: str
    display_name: str
    permissions: Optional[str] = None
    is_active: bool = True

class UserRoleCreate(UserRoleBase):
    pass

class UserRoleUpdate(BaseModel):
    name: Optional[str] = None
    display_name: Optional[str] = None
    permissions: Optional[str] = None
    is_active: Optional[bool] = None

class UserRoleOut(UserRoleBase):
    id: int
    company_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

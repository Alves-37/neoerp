from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class UserBase(BaseModel):
    name: str
    username: str
    email: str
    role: str = 'admin'
    branch_id: Optional[int] = None
    establishment_id: Optional[int] = None
    is_active: bool = True

class UserCreate(UserBase):
    password: str  # em prod, aceitar só plain text e fazer hash no endpoint

class UserUpdate(BaseModel):
    name: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    branch_id: Optional[int] = None
    establishment_id: Optional[int] = None
    is_active: Optional[bool] = None

class UserOut(UserBase):
    id: int
    company_id: int
    created_at: datetime

    class Config:
        from_attributes = True

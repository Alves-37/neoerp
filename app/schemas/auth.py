from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    id: int
    company_id: int
    branch_id: int | None = None
    establishment_id: int | None = None
    name: str
    username: str
    email: EmailStr
    role: str
    visible_branch_ids: list[int] | None = None


class UpdateMeRequest(BaseModel):
    name: str | None = None
    username: str | None = None
    email: EmailStr | None = None
    visible_branch_ids: list[int] | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

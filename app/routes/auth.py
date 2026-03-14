from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.auth import ChangePasswordRequest, LoginRequest, MeResponse, TokenResponse, UpdateMeRequest
from app.services.auth_service import create_access_token, hash_password, is_password_hash_recognized, verify_password

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas")

    # If the stored hash is legacy/plaintext, upgrade it to bcrypt on login.
    if not is_password_hash_recognized(user.password_hash):
        user.password_hash = hash_password(payload.password)
        db.add(user)
        db.commit()

    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token)


@router.get("/me", response_model=MeResponse)
def me(current_user: User = Depends(get_current_user)):
    return MeResponse(
        id=current_user.id,
        company_id=current_user.company_id,
        branch_id=getattr(current_user, "branch_id", None),
        name=current_user.name,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
    )


@router.put("/me", response_model=MeResponse)
@router.put("/me/", response_model=MeResponse, include_in_schema=False)
def update_me(
    payload: UpdateMeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(current_user, k, v)

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return MeResponse(
        id=current_user.id,
        company_id=current_user.company_id,
        branch_id=getattr(current_user, "branch_id", None),
        name=current_user.name,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
    )


@router.post("/change-password")
@router.post("/change-password/", include_in_schema=False)
def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Senha atual incorreta")

    if len(payload.new_password) < 6:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A nova senha é muito curta")

    current_user.password_hash = hash_password(payload.new_password)
    db.add(current_user)
    db.commit()
    return {"status": "ok"}

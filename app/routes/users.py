from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.deps import get_current_user
from app.models.establishment import Establishment
from app.models.user import User
from app.schemas.users import UserCreate, UserOut, UserUpdate
from app.services.auth_service import hash_password

router = APIRouter()

@router.get('', response_model=list[UserOut])
def list_users(
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    role = (getattr(current_user, "role", "") or "").strip().lower()
    is_admin = role in {"admin", "owner"}

    stmt = select(User).where(User.company_id == current_user.company_id)
    if is_admin:
        if branch_id is not None:
            stmt = stmt.where(User.branch_id == branch_id)
        else:
            if current_user.branch_id is None:
                raise HTTPException(status_code=400, detail='Informe branch_id para listar usuários (usuário atual sem filial definida).')
            stmt = stmt.where(User.branch_id == current_user.branch_id)
    else:
        if current_user.branch_id is None:
            raise HTTPException(status_code=400, detail='Usuário atual sem filial definida. Contacte o administrador.')
        stmt = stmt.where(User.branch_id == current_user.branch_id)

    rows = db.scalars(stmt.order_by(User.name)).all()
    return rows

@router.post('', response_model=UserOut)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verificar duplicidade de username/email
    existing = db.scalar(
        select(User)
        .where((User.username == payload.username) | (User.email == payload.email))
    )
    if existing:
        raise HTTPException(status_code=400, detail='Já existe um usuário com este username ou e-mail.')

    role = (getattr(current_user, "role", "") or "").strip().lower()
    is_admin = role in {"admin", "owner"}
    target_branch_id = payload.branch_id if (is_admin and payload.branch_id is not None) else current_user.branch_id

    if target_branch_id is None:
        raise HTTPException(status_code=400, detail='Não foi possível determinar a filial do usuário. Informe branch_id ou defina a filial do usuário atual.')

    establishment_id = payload.establishment_id
    if establishment_id is not None:
        est = db.get(Establishment, int(establishment_id))
        if (not est) or (est.company_id != current_user.company_id):
            raise HTTPException(status_code=404, detail='Ponto não encontrado.')
        if int(est.branch_id) != int(target_branch_id):
            raise HTTPException(status_code=400, detail='Ponto não pertence à filial selecionada.')

    user = User(
        company_id=current_user.company_id,
        branch_id=target_branch_id,
        establishment_id=int(establishment_id) if establishment_id is not None else None,
        name=payload.name,
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        is_active=payload.is_active,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail='Já existe um usuário com este username ou e-mail.')
    db.refresh(user)
    return user

@router.get('/{user_id}', response_model=UserOut)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    role = (getattr(current_user, "role", "") or "").strip().lower()
    is_admin = role in {"admin", "owner"}

    stmt = select(User).where(User.id == user_id).where(User.company_id == current_user.company_id)
    if not is_admin:
        stmt = stmt.where(User.branch_id == current_user.branch_id)

    user = db.scalar(stmt)
    if not user:
        raise HTTPException(status_code=404, detail='Usuário não encontrado.')
    return user

@router.put('/{user_id}', response_model=UserOut)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    role = (getattr(current_user, "role", "") or "").strip().lower()
    is_admin = role in {"admin", "owner"}

    stmt = select(User).where(User.id == user_id).where(User.company_id == current_user.company_id)
    if not is_admin:
        stmt = stmt.where(User.branch_id == current_user.branch_id)

    user = db.scalar(stmt)
    if not user:
        raise HTTPException(status_code=404, detail='Usuário não encontrado.')

    data = payload.model_dump(exclude_unset=True)

    if (not is_admin) and ("branch_id" in data):
        raise HTTPException(status_code=403, detail='Sem permissão para alterar a filial do usuário.')

    if "branch_id" in data and data.get("branch_id") is None:
        raise HTTPException(status_code=400, detail='branch_id não pode ser nulo.')

    if "establishment_id" in data and data.get("establishment_id") is not None:
        next_branch_id = int(data.get("branch_id")) if data.get("branch_id") is not None else int(user.branch_id)
        est = db.get(Establishment, int(data.get("establishment_id")))
        if (not est) or (est.company_id != current_user.company_id):
            raise HTTPException(status_code=404, detail='Ponto não encontrado.')
        if int(est.branch_id) != int(next_branch_id):
            raise HTTPException(status_code=400, detail='Ponto não pertence à filial do usuário.')

    if "password" in data:
        password = data.pop("password")
        if password:
            user.password_hash = hash_password(password)

    for k, v in data.items():
        setattr(user, k, v)

    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail='Já existe um usuário com este username ou e-mail.')
    db.refresh(user)
    return user

@router.delete('/{user_id}')
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail='Não é possível excluir seu próprio usuário.')

    role = (getattr(current_user, "role", "") or "").strip().lower()
    is_admin = role in {"admin", "owner"}

    stmt = select(User).where(User.id == user_id).where(User.company_id == current_user.company_id)
    if not is_admin:
        stmt = stmt.where(User.branch_id == current_user.branch_id)

    user = db.scalar(stmt)
    if not user:
        raise HTTPException(status_code=404, detail='Usuário não encontrado.')

    db.delete(user)
    db.commit()
    return {'detail': 'Usuário excluído.'}

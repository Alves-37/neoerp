from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.deps import get_current_user
from app.models.company import Company
from app.models.user import User
from app.models.user_role import UserRole
from app.schemas.user_roles import UserRoleCreate, UserRoleOut, UserRoleUpdate

router = APIRouter()

@router.get('/', response_model=list[UserRoleOut])
def list_user_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    rows = db.scalars(
        select(UserRole)
        .where(UserRole.company_id == current_user.company_id)
        .order_by(UserRole.name)
    ).all()
    return rows

@router.post('/', response_model=UserRoleOut)
def create_user_role(
    payload: UserRoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verificar duplicidade de nome
    existing = db.scalar(
        select(UserRole)
        .where(UserRole.company_id == current_user.company_id)
        .where(UserRole.name == payload.name)
    )
    if existing:
        raise HTTPException(status_code=400, detail='Já existe um papel com este nome.')

    role = UserRole(
        company_id=current_user.company_id,
        name=payload.name,
        display_name=payload.display_name,
        permissions=payload.permissions,
        is_active=payload.is_active,
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    return role

@router.get('/{role_id}', response_model=UserRoleOut)
def get_user_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    role = db.scalar(
        select(UserRole)
        .where(UserRole.id == role_id)
        .where(UserRole.company_id == current_user.company_id)
    )
    if not role:
        raise HTTPException(status_code=404, detail='Papel não encontrado.')
    return role

@router.put('/{role_id}', response_model=UserRoleOut)
def update_user_role(
    role_id: int,
    payload: UserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    role = db.scalar(
        select(UserRole)
        .where(UserRole.id == role_id)
        .where(UserRole.company_id == current_user.company_id)
    )
    if not role:
        raise HTTPException(status_code=404, detail='Papel não encontrado.')

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(role, k, v)

    db.add(role)
    db.commit()
    db.refresh(role)
    return role

@router.delete('/{role_id}')
def delete_user_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    role = db.scalar(
        select(UserRole)
        .where(UserRole.id == role_id)
        .where(UserRole.company_id == current_user.company_id)
    )
    if not role:
        raise HTTPException(status_code=404, detail='Papel não encontrado.')

    # Verificar se há usuários vinculados
    users_with_role = db.scalar(
        select(User)
        .where(User.role_id == role_id)
    )
    if users_with_role:
        raise HTTPException(status_code=400, detail='Não é possível excluir um papel que está em uso.')

    db.delete(role)
    db.commit()
    return {'detail': 'Papel excluído.'}

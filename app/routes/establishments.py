from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.deps import get_current_user
from app.models.branch import Branch
from app.models.establishment import Establishment
from app.models.user import User
from app.schemas.establishments import EstablishmentCreate, EstablishmentOut, EstablishmentUpdate

router = APIRouter()


def _is_admin(current_user: User) -> bool:
    role = (getattr(current_user, "role", "") or "").strip().lower()
    return role in {"admin", "owner"}


class SwitchEstablishmentRequest(BaseModel):
    establishment_id: int


@router.get("", response_model=list[EstablishmentOut])
@router.get("/", response_model=list[EstablishmentOut], include_in_schema=False)
def list_establishments(
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    effective_branch_id = int(branch_id) if branch_id is not None else int(getattr(current_user, "branch_id", 0) or 0)
    if not effective_branch_id:
        raise HTTPException(status_code=400, detail="Filial inválida")

    b = db.get(Branch, effective_branch_id)
    if not b or b.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Filial não encontrada")

    rows = db.scalars(
        select(Establishment)
        .where(Establishment.company_id == current_user.company_id)
        .where(Establishment.branch_id == effective_branch_id)
        .order_by(Establishment.name.asc(), Establishment.id.asc())
    ).all()
    return rows


@router.post("", response_model=EstablishmentOut)
@router.post("/", response_model=EstablishmentOut, include_in_schema=False)
def create_establishment(
    payload: EstablishmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not _is_admin(current_user):
        raise HTTPException(status_code=403, detail="Apenas admin pode criar pontos")

    b = db.get(Branch, int(payload.branch_id))
    if not b or b.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Filial não encontrada")

    row = Establishment(
        company_id=current_user.company_id,
        branch_id=int(payload.branch_id),
        name=(payload.name or "").strip() or "Ponto",
        is_active=bool(payload.is_active),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.put("/{establishment_id}", response_model=EstablishmentOut)
@router.put("/{establishment_id}/", response_model=EstablishmentOut, include_in_schema=False)
def update_establishment(
    establishment_id: int,
    payload: EstablishmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not _is_admin(current_user):
        raise HTTPException(status_code=403, detail="Apenas admin pode atualizar pontos")

    row = db.get(Establishment, establishment_id)
    if not row or row.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Ponto não encontrado")

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(row, k, v)

    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.post("/switch", response_model=EstablishmentOut)
@router.post("/switch/", response_model=EstablishmentOut, include_in_schema=False)
def switch_my_establishment(
    payload: SwitchEstablishmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not _is_admin(current_user):
        raise HTTPException(status_code=403, detail="Apenas admin pode trocar de ponto")

    if not getattr(current_user, "branch_id", None):
        raise HTTPException(status_code=400, detail="Filial inválida")

    row = db.get(Establishment, int(payload.establishment_id))
    if not row or row.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Ponto não encontrado")

    if int(row.branch_id) != int(current_user.branch_id):
        raise HTTPException(status_code=400, detail="Ponto não pertence à filial atual")

    if not getattr(row, "is_active", True):
        raise HTTPException(status_code=400, detail="Ponto inativo")

    current_user.establishment_id = row.id
    db.add(current_user)
    db.commit()
    return row


@router.delete("/{establishment_id}")
@router.delete("/{establishment_id}/", include_in_schema=False)
def delete_establishment(
    establishment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not _is_admin(current_user):
        raise HTTPException(status_code=403, detail="Apenas admin pode excluir pontos")

    row = db.get(Establishment, int(establishment_id))
    if not row or row.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Ponto não encontrado")

    # Clear user references to avoid FK violations.
    users = db.scalars(
        select(User)
        .where(User.company_id == current_user.company_id)
        .where(User.establishment_id == int(row.id))
    ).all()
    for u in users:
        u.establishment_id = None
        db.add(u)

    try:
        db.delete(row)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Não é possível excluir este ponto porque existem registros vinculados (ex: caixas, vendas, impressoras). Desative o ponto ou apague os registros primeiro.",
        )

    return {"ok": True}

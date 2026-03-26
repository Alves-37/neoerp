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

    if not rows:
        # Guarantee each branch has at least one default point.
        # This keeps the system usable even if the branch was created without establishments.
        if _is_admin(current_user):
            row = Establishment(
                company_id=current_user.company_id,
                branch_id=int(effective_branch_id),
                name="Ponto Principal",
                is_active=True,
                is_default=True,
            )
            db.add(row)
            db.commit()
            db.refresh(row)
            rows = [row]

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
    role = (getattr(current_user, "role", "") or "").strip().lower()
    if role in {"admin", "owner"}:
        if payload.establishment_id is None:
            raise HTTPException(status_code=400, detail="Ponto inválido")

        row = db.get(Establishment, int(payload.establishment_id))
        if not row:
            raise HTTPException(status_code=404, detail="Ponto não encontrado")
        if int(row.company_id) != int(current_user.company_id):
            raise HTTPException(status_code=403, detail="Ponto inválido")
        if int(row.branch_id) != int(current_user.branch_id):
            raise HTTPException(status_code=403, detail="Ponto inválido")
        if getattr(row, "is_active", True) is False:
            raise HTTPException(status_code=400, detail="Ponto inválido")

        current_user.establishment_id = int(row.id)
        db.add(current_user)
        db.commit()
        db.refresh(current_user)
        return row
    else:
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


def _get_branch_default_establishment_id(db: Session, *, company_id: int, branch_id: int) -> int:
    row = db.scalar(
        select(Establishment)
        .where(Establishment.company_id == int(company_id))
        .where(Establishment.branch_id == int(branch_id))
        .order_by(Establishment.is_default.desc(), Establishment.id.asc())
        .limit(1)
    )
    if not row:
        _ensure_default_establishment(db, company_id=company_id, branch_id=branch_id)
        row = db.scalar(
            select(Establishment)
            .where(Establishment.company_id == int(company_id))
            .where(Establishment.branch_id == int(branch_id))
            .order_by(Establishment.is_default.desc(), Establishment.id.asc())
            .limit(1)
        )
    if not row:
        raise HTTPException(status_code=400, detail="Ponto padrão não encontrado")
    return int(row.id)


def _ensure_default_establishment(db: Session, *, company_id: int, branch_id: int) -> None:
    row = Establishment(
        company_id=company_id,
        branch_id=branch_id,
        name="Ponto Principal",
        is_active=True,
        is_default=True,
    )
    db.add(row)
    db.commit()
    db.refresh(row)


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

    _ensure_default_establishment(db, company_id=current_user.company_id, branch_id=int(row.branch_id))

    return {"ok": True}

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import asc, func, select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.deps import get_current_user
from app.models.branch import Branch
from app.models.delivery_zone import DeliveryZone
from app.models.user import User
from app.schemas.delivery_zones import DeliveryZoneCreate, DeliveryZoneOut, DeliveryZoneUpdate

router = APIRouter()


def _ensure_admin(current_user: User):
    role = (getattr(current_user, "role", "") or "").strip().lower()
    if role not in {"admin", "owner"}:
        raise HTTPException(status_code=403, detail="Sem permissão")


def _ensure_branch_access(db: Session, current_user: User, branch_id: int) -> Branch:
    row = db.get(Branch, int(branch_id))
    if not row or row.company_id != current_user.company_id:
        raise HTTPException(status_code=400, detail="Filial inválida")
    return row


@router.get("", response_model=list[DeliveryZoneOut])
@router.get("/", response_model=list[DeliveryZoneOut], include_in_schema=False)
def list_delivery_zones(
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(DeliveryZone).where(DeliveryZone.company_id == current_user.company_id)
    if branch_id is not None:
        _ensure_branch_access(db, current_user, int(branch_id))
        stmt = stmt.where(DeliveryZone.branch_id == int(branch_id))
    else:
        stmt = stmt.where(DeliveryZone.branch_id == int(current_user.branch_id))

    rows = db.scalars(stmt.order_by(asc(DeliveryZone.name), asc(DeliveryZone.id))).all()
    return rows


@router.post("", response_model=DeliveryZoneOut)
def create_delivery_zone(
    payload: DeliveryZoneCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)

    branch = _ensure_branch_access(db, current_user, int(payload.branch_id))
    bt = (branch.business_type or "").strip().lower()
    if bt != "restaurant":
        raise HTTPException(status_code=400, detail="Disponível apenas para restaurante")

    name = (payload.name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Nome inválido")

    exists = db.scalar(
        select(DeliveryZone)
        .where(DeliveryZone.company_id == current_user.company_id)
        .where(DeliveryZone.branch_id == int(payload.branch_id))
        .where(func.lower(DeliveryZone.name) == name.lower())
    )
    if exists:
        return exists

    keywords = payload.keywords or []
    keywords = [str(x).strip() for x in keywords if str(x).strip()]

    row = DeliveryZone(
        company_id=current_user.company_id,
        branch_id=int(payload.branch_id),
        name=name,
        fee=float(payload.fee or 0),
        keywords=keywords,
        is_active=bool(payload.is_active),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.put("/{zone_id}", response_model=DeliveryZoneOut)
def update_delivery_zone(
    zone_id: int,
    payload: DeliveryZoneUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)

    row = db.get(DeliveryZone, int(zone_id))
    if not row or row.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Zona não encontrada")

    data = payload.model_dump(exclude_unset=True)

    if "branch_id" in data and data["branch_id"] is not None:
        _ensure_branch_access(db, current_user, int(data["branch_id"]))
        row.branch_id = int(data["branch_id"])

    if "name" in data and data["name"] is not None:
        name = str(data["name"]).strip()
        if not name:
            raise HTTPException(status_code=400, detail="Nome inválido")

        dup = db.scalar(
            select(DeliveryZone)
            .where(DeliveryZone.company_id == current_user.company_id)
            .where(DeliveryZone.branch_id == row.branch_id)
            .where(func.lower(DeliveryZone.name) == name.lower())
            .where(DeliveryZone.id != row.id)
        )
        if dup:
            raise HTTPException(status_code=400, detail="Já existe uma zona com este nome")

        row.name = name

    if "fee" in data and data["fee"] is not None:
        row.fee = float(data["fee"] or 0)

    if "keywords" in data and data["keywords"] is not None:
        keywords = data["keywords"] or []
        row.keywords = [str(x).strip() for x in keywords if str(x).strip()]

    if "is_active" in data and data["is_active"] is not None:
        row.is_active = bool(data["is_active"])

    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{zone_id}")
def delete_delivery_zone(
    zone_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)

    row = db.get(DeliveryZone, int(zone_id))
    if not row or row.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Zona não encontrada")

    db.delete(row)
    db.commit()
    return {"status": "deleted"}

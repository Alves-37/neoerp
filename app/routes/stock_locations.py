from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import asc, select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.deps import get_current_user
from app.models.branch import Branch
from app.models.stock_location import StockLocation
from app.models.user import User
from app.schemas.stock_locations import StockLocationCreate, StockLocationOut, StockLocationUpdate

router = APIRouter()


def _ensure_default_locations(db: Session, company_id: int, branch_id: int) -> None:
    existing = db.scalars(
        select(StockLocation)
        .where(StockLocation.company_id == company_id)
        .where(StockLocation.branch_id == branch_id)
    ).all()
    if existing:
        return

    loja = StockLocation(
        company_id=company_id,
        branch_id=branch_id,
        type="store",
        name="Loja Principal",
        is_default=True,
        is_active=True,
    )
    armazem = StockLocation(
        company_id=company_id,
        branch_id=branch_id,
        type="warehouse",
        name="Armazém",
        is_default=False,
        is_active=True,
    )
    db.add(loja)
    db.add(armazem)
    db.commit()


@router.get("/", response_model=list[StockLocationOut])
def list_locations(
    include_inactive: bool = False,
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    role = (getattr(current_user, "role", "") or "").strip().lower()
    is_admin = role in {"admin", "owner"}

    # Default behavior: always scope to the user's current branch for safety/isolation.
    # Admins can explicitly request another branch by passing branch_id.
    effective_branch_id = int(branch_id) if (is_admin and branch_id is not None) else int(current_user.branch_id)

    b = db.get(Branch, effective_branch_id)
    if not b or b.company_id != current_user.company_id:
        raise HTTPException(status_code=400, detail="Filial inválida")

    _ensure_default_locations(db, current_user.company_id, effective_branch_id)
    stmt = (
        select(StockLocation)
        .where(StockLocation.company_id == current_user.company_id)
        .where(StockLocation.branch_id == effective_branch_id)
    )

    if not include_inactive:
        stmt = stmt.where(StockLocation.is_active.is_(True))

    rows = db.scalars(stmt.order_by(asc(StockLocation.type), asc(StockLocation.name))).all()
    return rows


@router.post("/", response_model=StockLocationOut)
def create_location(
    payload: StockLocationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.type not in {"store", "warehouse"}:
        raise HTTPException(status_code=400, detail="Tipo inválido (use store/warehouse)")

    if payload.is_default:
        db.query(StockLocation).filter(
            StockLocation.company_id == current_user.company_id,
            StockLocation.branch_id == current_user.branch_id,
            StockLocation.is_default.is_(True),
        ).update({"is_default": False})

    row = StockLocation(company_id=current_user.company_id, branch_id=int(current_user.branch_id), **payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.put("/{location_id}", response_model=StockLocationOut)
def update_location(
    location_id: int,
    payload: StockLocationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = db.get(StockLocation, location_id)
    role = (getattr(current_user, "role", "") or "").strip().lower()
    is_admin = role in {"admin", "owner"}

    if not row or row.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Local não encontrado")
    if not is_admin and getattr(row, "branch_id", None) != current_user.branch_id:
        raise HTTPException(status_code=404, detail="Local não encontrado")

    data = payload.model_dump(exclude_unset=True)

    if "type" in data and data["type"] is not None and data["type"] not in {"store", "warehouse"}:
        raise HTTPException(status_code=400, detail="Tipo inválido (use store/warehouse)")

    if data.get("is_default") is True:
        db.query(StockLocation).filter(
            StockLocation.company_id == current_user.company_id,
            StockLocation.branch_id == getattr(row, "branch_id", None),
            StockLocation.is_default.is_(True),
        ).update({"is_default": False})

    for k, v in data.items():
        setattr(row, k, v)

    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{location_id}")
def delete_location(
    location_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = db.get(StockLocation, location_id)
    role = (getattr(current_user, "role", "") or "").strip().lower()
    is_admin = role in {"admin", "owner"}

    if not row or row.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Local não encontrado")

    if not is_admin and getattr(row, "branch_id", None) != current_user.branch_id:
        raise HTTPException(status_code=404, detail="Local não encontrado")

    if row.is_default:
        raise HTTPException(status_code=400, detail="Não é possível excluir o local padrão")

    db.delete(row)
    db.commit()
    return {"ok": True}

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import asc, select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.deps import get_current_user
from app.models.branch import Branch
from app.models.restaurant_table import RestaurantTable
from app.models.user import User
from app.schemas.restaurant_tables import RestaurantTableCreate, RestaurantTableOut, RestaurantTableUpdate

router = APIRouter()


@router.get("", response_model=list[RestaurantTableOut])
@router.get("/", response_model=list[RestaurantTableOut], include_in_schema=False)
def list_tables(
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    role = (getattr(current_user, "role", "") or "").strip().lower()
    is_admin = role in {"admin", "owner"}

    stmt = select(RestaurantTable).where(RestaurantTable.company_id == current_user.company_id)

    # Admin default: all branches
    if is_admin and branch_id is None:
        pass
    else:
        effective_branch_id = int(branch_id) if (is_admin and branch_id is not None) else int(current_user.branch_id)
        stmt = stmt.where(RestaurantTable.branch_id == effective_branch_id)

    rows = db.scalars(stmt.order_by(asc(RestaurantTable.number))).all()
    return rows


@router.post("", response_model=RestaurantTableOut)
def create_table(payload: RestaurantTableCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    branch = db.get(Branch, int(current_user.branch_id))
    if not branch or branch.company_id != current_user.company_id:
        raise HTTPException(status_code=400, detail="Filial inválida")
    if (branch.business_type or "").strip().lower() != "restaurant":
        raise HTTPException(status_code=400, detail="Disponível apenas para restaurante")

    existing = db.scalar(
        select(RestaurantTable)
        .where(RestaurantTable.company_id == current_user.company_id)
        .where(RestaurantTable.branch_id == int(current_user.branch_id))
        .where(RestaurantTable.number == payload.number)
    )
    if existing:
        raise HTTPException(status_code=400, detail="Mesa já existe")

    row = RestaurantTable(
        company_id=current_user.company_id,
        branch_id=int(current_user.branch_id),
        number=payload.number,
        capacity=payload.capacity,
        is_active=payload.is_active,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.put("/{table_id}", response_model=RestaurantTableOut)
def update_table(
    table_id: int, payload: RestaurantTableUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    row = db.get(RestaurantTable, table_id)
    role = (getattr(current_user, "role", "") or "").strip().lower()
    is_admin = role in {"admin", "owner"}

    if not row or row.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Mesa não encontrada")
    if not is_admin and getattr(row, "branch_id", None) != current_user.branch_id:
        raise HTTPException(status_code=404, detail="Mesa não encontrada")

    data = payload.model_dump(exclude_unset=True)
    if "number" in data and data["number"] is not None and int(data["number"]) != row.number:
        existing = db.scalar(
            select(RestaurantTable)
            .where(RestaurantTable.company_id == current_user.company_id)
            .where(RestaurantTable.branch_id == getattr(row, "branch_id", None))
            .where(RestaurantTable.number == int(data["number"]))
        )
        if existing:
            raise HTTPException(status_code=400, detail="Já existe uma mesa com este número")

    for k, v in data.items():
        setattr(row, k, v)

    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{table_id}")
def delete_table(table_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    row = db.get(RestaurantTable, table_id)
    role = (getattr(current_user, "role", "") or "").strip().lower()
    is_admin = role in {"admin", "owner"}

    if not row or row.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Mesa não encontrada")
    if not is_admin and getattr(row, "branch_id", None) != current_user.branch_id:
        raise HTTPException(status_code=404, detail="Mesa não encontrada")

    db.delete(row)
    db.commit()
    return {"status": "deleted"}

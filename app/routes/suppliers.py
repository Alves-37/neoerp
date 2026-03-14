from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.deps import get_current_user
from app.models.supplier import Supplier
from app.models.user import User
from app.schemas.suppliers import SupplierCreate, SupplierOut, SupplierUpdate

router = APIRouter()


@router.get("/", response_model=list[SupplierOut])
def list_suppliers(
    q: str | None = None,
    limit: int = 50,
    offset: int = 0,
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    role = (getattr(current_user, "role", "") or "").strip().lower()
    is_admin = role in {"admin", "owner"}

    stmt = select(Supplier).where(Supplier.company_id == current_user.company_id)
    effective_branch_id = int(branch_id) if (is_admin and branch_id is not None) else int(current_user.branch_id)
    stmt = stmt.where(Supplier.branch_id == effective_branch_id)
    if q:
        stmt = stmt.where(Supplier.name.ilike(f"%{q}%"))

    rows = db.scalars(stmt.order_by(Supplier.name.asc(), Supplier.id.asc()).limit(limit).offset(offset)).all()
    return rows


@router.post("/", response_model=SupplierOut)
def create_supplier(
    payload: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    supplier = Supplier(company_id=current_user.company_id, branch_id=int(current_user.branch_id), **payload.model_dump())
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.put("/{supplier_id}", response_model=SupplierOut)
def update_supplier(
    supplier_id: int,
    payload: SupplierUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    role = (getattr(current_user, "role", "") or "").strip().lower()
    is_admin = role in {"admin", "owner"}

    supplier = db.get(Supplier, supplier_id)
    if not supplier or supplier.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Fornecedor não encontrado")

    if not is_admin and getattr(supplier, "branch_id", None) != int(current_user.branch_id):
        raise HTTPException(status_code=403, detail="Sem permissão para alterar este fornecedor")

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(supplier, k, v)

    db.commit()
    db.refresh(supplier)
    return supplier


@router.delete("/{supplier_id}")
def delete_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    role = (getattr(current_user, "role", "") or "").strip().lower()
    is_admin = role in {"admin", "owner"}

    supplier = db.get(Supplier, supplier_id)
    if not supplier or supplier.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Fornecedor não encontrado")

    if not is_admin and getattr(supplier, "branch_id", None) != int(current_user.branch_id):
        raise HTTPException(status_code=403, detail="Sem permissão para excluir este fornecedor")

    try:
        db.delete(supplier)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Não é possível excluir este fornecedor porque existem compras/pagamentos associados.",
        )

    return {"ok": True}

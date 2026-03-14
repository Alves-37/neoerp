from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.deps import get_current_user
from app.models.customer import Customer
from app.models.user import User
from app.schemas.customers import CustomerCreate, CustomerOut, CustomerUpdate

router = APIRouter()


@router.get("/", response_model=list[CustomerOut])
def list_customers(
    q: str | None = None,
    limit: int = 50,
    offset: int = 0,
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    role = (getattr(current_user, "role", "") or "").strip().lower()
    is_admin = role in {"admin", "owner"}

    stmt = select(Customer).where(Customer.company_id == current_user.company_id)
    effective_branch_id = int(branch_id) if (is_admin and branch_id is not None) else int(current_user.branch_id)
    stmt = stmt.where(Customer.branch_id == effective_branch_id)

    if q:
        stmt = stmt.where(Customer.name.ilike(f"%{q}%"))

    rows = db.scalars(stmt.order_by(Customer.name.asc(), Customer.id.asc()).limit(limit).offset(offset)).all()
    return rows


@router.post("/", response_model=CustomerOut)
def create_customer(
    payload: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    customer = Customer(company_id=current_user.company_id, branch_id=int(current_user.branch_id), **payload.model_dump())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.put("/{customer_id}", response_model=CustomerOut)
def update_customer(
    customer_id: int,
    payload: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    role = (getattr(current_user, "role", "") or "").strip().lower()
    is_admin = role in {"admin", "owner"}

    customer = db.get(Customer, customer_id)
    if not customer or customer.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    if not is_admin and customer.branch_id != current_user.branch_id:
        raise HTTPException(status_code=403, detail="Sem permissão para alterar este cliente")

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(customer, k, v)

    db.commit()
    db.refresh(customer)
    return customer


@router.delete("/{customer_id}")
def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    role = (getattr(current_user, "role", "") or "").strip().lower()
    is_admin = role in {"admin", "owner"}

    customer = db.get(Customer, customer_id)
    if not customer or customer.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    if not is_admin and customer.branch_id != current_user.branch_id:
        raise HTTPException(status_code=403, detail="Sem permissão para excluir este cliente")

    db.delete(customer)
    try:
        db.commit()
        return {"ok": True}
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Não é possível excluir este cliente porque ele está associado a documentos fiscais.",
        )

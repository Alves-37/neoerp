from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.deps import get_current_user
from app.models.supplier import Supplier
from app.models.supplier_purchase import SupplierPurchase
from app.models.supplier_payment import SupplierPayment
from app.models.user import User
from app.schemas.suppliers import SupplierPurchaseCreate, SupplierPurchaseOut, SupplierPurchaseUpdate

router = APIRouter()


def _recalc_purchase_status(db: Session, purchase: SupplierPurchase):
    paid = db.scalar(
        select(SupplierPayment)
        .with_only_columns(SupplierPayment.amount)
        .where(SupplierPayment.company_id == purchase.company_id)
        .where(SupplierPayment.purchase_id == purchase.id)
    )


@router.get("/", response_model=list[SupplierPurchaseOut])
def list_purchases(
    supplier_id: int | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(SupplierPurchase)
        .join(Supplier, Supplier.id == SupplierPurchase.supplier_id)
        .where(SupplierPurchase.company_id == current_user.company_id)
        .where(Supplier.company_id == current_user.company_id)
        .where(Supplier.branch_id == int(current_user.branch_id))
    )
    if supplier_id:
        supplier = db.get(Supplier, int(supplier_id))
        if (
            not supplier
            or supplier.company_id != current_user.company_id
            or getattr(supplier, "branch_id", None) != int(current_user.branch_id)
        ):
            raise HTTPException(status_code=400, detail="Fornecedor inválido")
        stmt = stmt.where(SupplierPurchase.supplier_id == int(supplier_id))
    if status:
        stmt = stmt.where(SupplierPurchase.status == status)

    rows = db.scalars(stmt.order_by(desc(SupplierPurchase.id)).limit(limit).offset(offset)).all()
    return rows


@router.post("/", response_model=SupplierPurchaseOut)
def create_purchase(
    payload: SupplierPurchaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    supplier = db.get(Supplier, payload.supplier_id)
    if (
        not supplier
        or supplier.company_id != current_user.company_id
        or getattr(supplier, "branch_id", None) != int(current_user.branch_id)
    ):
        raise HTTPException(status_code=400, detail="Fornecedor inválido")

    purchase = SupplierPurchase(company_id=current_user.company_id, **payload.model_dump())
    db.add(purchase)
    db.commit()
    db.refresh(purchase)
    return purchase


@router.put("/{purchase_id}", response_model=SupplierPurchaseOut)
def update_purchase(
    purchase_id: int,
    payload: SupplierPurchaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    purchase = db.get(SupplierPurchase, purchase_id)
    if not purchase or purchase.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Compra não encontrada")

    supplier = db.get(Supplier, int(getattr(purchase, "supplier_id", 0) or 0))
    if (
        not supplier
        or supplier.company_id != current_user.company_id
        or getattr(supplier, "branch_id", None) != int(current_user.branch_id)
    ):
        raise HTTPException(status_code=403, detail="Sem permissão para alterar esta compra")

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(purchase, k, v)

    db.commit()
    db.refresh(purchase)
    return purchase


@router.delete("/{purchase_id}")
def delete_purchase(
    purchase_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    purchase = db.get(SupplierPurchase, purchase_id)
    if not purchase or purchase.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Compra não encontrada")

    supplier = db.get(Supplier, int(getattr(purchase, "supplier_id", 0) or 0))
    if (
        not supplier
        or supplier.company_id != current_user.company_id
        or getattr(supplier, "branch_id", None) != int(current_user.branch_id)
    ):
        raise HTTPException(status_code=403, detail="Sem permissão para excluir esta compra")

    # Desvincular pagamentos para evitar erro de FK (pagamentos podem existir sem vínculo a uma compra)
    db.execute(
        update(SupplierPayment)
        .where(SupplierPayment.company_id == current_user.company_id)
        .where(SupplierPayment.purchase_id == purchase.id)
        .values(purchase_id=None)
    )

    try:
        db.delete(purchase)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Não é possível excluir esta compra porque existe informação relacionada.",
        )

    return {"ok": True}

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.deps import get_current_user
from app.models.supplier import Supplier
from app.models.supplier_payment import SupplierPayment
from app.models.supplier_purchase import SupplierPurchase
from app.models.user import User
from app.schemas.suppliers import SupplierPaymentCreate, SupplierPaymentOut, SupplierPaymentUpdate

router = APIRouter()


@router.get("/", response_model=list[SupplierPaymentOut])
def list_payments(
    supplier_id: int | None = None,
    purchase_id: int | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(SupplierPayment)
        .join(Supplier, Supplier.id == SupplierPayment.supplier_id)
        .where(SupplierPayment.company_id == current_user.company_id)
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
        stmt = stmt.where(SupplierPayment.supplier_id == supplier_id)
    if purchase_id:
        stmt = stmt.where(SupplierPayment.purchase_id == purchase_id)

    rows = db.scalars(stmt.order_by(desc(SupplierPayment.id)).limit(limit).offset(offset)).all()
    return rows


@router.post("/", response_model=SupplierPaymentOut)
def create_payment(
    payload: SupplierPaymentCreate,
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

    if payload.purchase_id is not None:
        purchase = db.get(SupplierPurchase, payload.purchase_id)
        if not purchase or purchase.company_id != current_user.company_id:
            raise HTTPException(status_code=400, detail="Compra inválida")
        if purchase.supplier_id != payload.supplier_id:
            raise HTTPException(status_code=400, detail="Compra não pertence ao fornecedor")

    payment = SupplierPayment(company_id=current_user.company_id, **payload.model_dump())
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


@router.put("/{payment_id}", response_model=SupplierPaymentOut)
def update_payment(
    payment_id: int,
    payload: SupplierPaymentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    payment = db.get(SupplierPayment, payment_id)
    if not payment or payment.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Pagamento não encontrado")

    supplier = db.get(Supplier, int(payment.supplier_id))
    if (
        not supplier
        or supplier.company_id != current_user.company_id
        or getattr(supplier, "branch_id", None) != int(current_user.branch_id)
    ):
        raise HTTPException(status_code=403, detail="Sem permissão para alterar este pagamento")

    if payload.purchase_id is not None:
        purchase = db.get(SupplierPurchase, payload.purchase_id)
        if not purchase or purchase.company_id != current_user.company_id:
            raise HTTPException(status_code=400, detail="Compra inválida")
        if purchase.supplier_id != payment.supplier_id:
            raise HTTPException(status_code=400, detail="Compra não pertence ao fornecedor")

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(payment, k, v)

    db.commit()
    db.refresh(payment)
    return payment


@router.delete("/{payment_id}")
def delete_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    payment = db.get(SupplierPayment, payment_id)
    if not payment or payment.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Pagamento não encontrado")

    supplier = db.get(Supplier, int(payment.supplier_id))
    if (
        not supplier
        or supplier.company_id != current_user.company_id
        or getattr(supplier, "branch_id", None) != int(current_user.branch_id)
    ):
        raise HTTPException(status_code=403, detail="Sem permissão para excluir este pagamento")

    db.delete(payment)
    db.commit()
    return {"ok": True}

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.deps import get_current_user
from app.models.branch import Branch
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.user import User
from app.schemas.orders import OrderClosePayload, OrderCreate, OrderItemOut, OrderOut, OrderUpdate

router = APIRouter()


def _get_order_out(db: Session, current_user: User, o: Order) -> OrderOut:
    items = db.scalars(
        select(OrderItem)
        .where(OrderItem.company_id == current_user.company_id)
        .where(OrderItem.branch_id == getattr(o, "branch_id", None))
        .where(OrderItem.order_id == o.id)
        .order_by(desc(OrderItem.id))
    ).all()

    return OrderOut(
        id=o.id,
        company_id=o.company_id,
        branch_id=getattr(o, "branch_id", 0) or 0,
        business_type=o.business_type,
        status=o.status,
        table_number=o.table_number,
        seat_number=o.seat_number,
        created_at=o.created_at,
        updated_at=o.updated_at,
        items=[OrderItemOut.model_validate(i) for i in items],
    )


@router.get("", response_model=list[OrderOut])
@router.get("/", response_model=list[OrderOut], include_in_schema=False)
def list_orders(
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    role = (getattr(current_user, "role", "") or "").strip().lower()
    is_admin = role in {"admin", "owner"}

    stmt = select(Order).where(Order.company_id == current_user.company_id)

    # Admin default: all branches, but only restaurant orders.
    if is_admin and branch_id is None:
        stmt = stmt.where(Order.business_type == "restaurant")
    else:
        effective_branch_id = int(branch_id) if (is_admin and branch_id is not None) else int(current_user.branch_id)
        branch = db.get(Branch, effective_branch_id)
        if not branch or branch.company_id != current_user.company_id:
            raise HTTPException(status_code=400, detail="Filial inválida")
        if (branch.business_type or "").strip().lower() != "restaurant":
            raise HTTPException(status_code=400, detail="Disponível apenas para restaurante")

        stmt = stmt.where(Order.branch_id == effective_branch_id).where(Order.business_type == "restaurant")

    if status:
        stmt = stmt.where(Order.status == status)

    rows = db.scalars(stmt.order_by(desc(Order.id)).limit(limit).offset(offset)).all()
    return [_get_order_out(db, current_user, r) for r in rows]


@router.post("", response_model=OrderOut)
def create_order(payload: OrderCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    branch = db.get(Branch, int(current_user.branch_id))
    if not branch or branch.company_id != current_user.company_id:
        raise HTTPException(status_code=400, detail="Filial inválida")
    if (branch.business_type or "").strip().lower() != "restaurant":
        raise HTTPException(status_code=400, detail="Disponível apenas para restaurante")

    if not payload.items:
        raise HTTPException(status_code=400, detail="Pedido deve ter itens")

    order = Order(
        company_id=current_user.company_id,
        branch_id=int(current_user.branch_id),
        business_type="restaurant",
        status="open",
        table_number=payload.table_number,
        seat_number=payload.seat_number,
    )
    db.add(order)
    db.flush()

    total = 0.0
    for it in payload.items:
        product = db.get(Product, it.product_id)
        if (
            not product
            or product.company_id != current_user.company_id
            or getattr(product, "branch_id", None) != current_user.branch_id
            or product.business_type != "restaurant"
        ):
            raise HTTPException(status_code=400, detail="Produto inválido")

        qty = float(it.qty or 0)
        if qty <= 0:
            raise HTTPException(status_code=400, detail="Quantidade inválida")

        price = float(it.price_at_order or 0)
        cost = float(it.cost_at_order or 0)
        line_total = round(price * qty, 2)
        total = round(total + line_total, 2)

        db.add(
            OrderItem(
                company_id=current_user.company_id,
                branch_id=int(current_user.branch_id),
                order_id=order.id,
                product_id=it.product_id,
                qty=qty,
                price_at_order=price,
                cost_at_order=cost,
                line_total=line_total,
            )
        )

    db.commit()
    db.refresh(order)
    return _get_order_out(db, current_user, order)


@router.put("/{order_id}", response_model=OrderOut)
def update_order(
    order_id: int, payload: OrderUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    o = db.get(Order, order_id)
    role = (getattr(current_user, "role", "") or "").strip().lower()
    is_admin = role in {"admin", "owner"}

    if not o or o.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    if not is_admin and getattr(o, "branch_id", None) != current_user.branch_id:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    data = payload.model_dump(exclude_unset=True)
    if "status" in data and data["status"] is not None:
        st = str(data["status"]).strip().lower()
        if st not in {"open", "in_progress", "closed", "cancelled"}:
            raise HTTPException(status_code=400, detail="Status inválido")
        o.status = st

    db.add(o)
    db.commit()
    db.refresh(o)
    return _get_order_out(db, current_user, o)


@router.post("/{order_id}/close", response_model=dict)
def close_order(
    order_id: int,
    payload: OrderClosePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    o = db.get(Order, order_id)
    role = (getattr(current_user, "role", "") or "").strip().lower()
    is_admin = role in {"admin", "owner"}

    if not o or o.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    if not is_admin and getattr(o, "branch_id", None) != current_user.branch_id:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    if o.status in {"closed", "cancelled"}:
        raise HTTPException(status_code=400, detail="Pedido já finalizado")

    items = db.scalars(
        select(OrderItem)
        .where(OrderItem.company_id == current_user.company_id)
        .where(OrderItem.branch_id == getattr(o, "branch_id", None))
        .where(OrderItem.order_id == o.id)
        .order_by(desc(OrderItem.id))
    ).all()

    if not items:
        raise HTTPException(status_code=400, detail="Pedido sem itens")

    total = float(sum(float(i.line_total) for i in items))
    paid = float(payload.paid or 0)
    change = round(max(0.0, paid - total), 2)

    sale = Sale(
        company_id=current_user.company_id,
        branch_id=int(getattr(o, "branch_id", current_user.branch_id) or current_user.branch_id),
        cashier_id=current_user.id,
        business_type="restaurant",
        total=total,
        paid=paid,
        change=change,
        payment_method=(payload.payment_method or "cash"),
        status="paid",
        sale_channel="table",
        table_number=o.table_number,
        seat_number=o.seat_number,
        created_at=datetime.utcnow(),
    )
    db.add(sale)
    db.flush()

    for i in items:
        db.add(
            SaleItem(
                company_id=current_user.company_id,
                branch_id=int(getattr(o, "branch_id", current_user.branch_id) or current_user.branch_id),
                sale_id=sale.id,
                product_id=i.product_id,
                qty=i.qty,
                price_at_sale=i.price_at_order,
                cost_at_sale=i.cost_at_order,
                line_total=i.line_total,
            )
        )

    o.status = "closed"
    db.add(o)
    db.commit()

    return {"status": "closed", "sale_id": sale.id}

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.deps import get_current_user
from app.models.branch import Branch
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.order_item_option import OrderItemOption
from app.models.product import Product
from app.models.product_stock import ProductStock
from app.models.recipe import Recipe
from app.models.recipe_item import RecipeItem
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.stock_movement import StockMovement
from app.models.user import User
from app.schemas.orders import OrderClosePayload, OrderCreate, OrderItemOut, OrderOut, OrderUpdate

router = APIRouter()


def _get_or_create_stock_row(db: Session, company_id: int, branch_id: int, product_id: int, location_id: int) -> ProductStock:
    row = db.scalar(
        select(ProductStock)
        .where(ProductStock.company_id == company_id)
        .where(ProductStock.branch_id == int(branch_id))
        .where(ProductStock.product_id == product_id)
        .where(ProductStock.location_id == location_id)
        .with_for_update()
    )
    if row:
        return row

    row = ProductStock(
        company_id=company_id,
        branch_id=int(branch_id),
        product_id=product_id,
        location_id=location_id,
        qty_on_hand=0,
    )
    db.add(row)
    db.flush()
    return row


def _convert_qty(qty: float, unit: str, base_unit: str) -> float:
    u = (unit or "").strip().lower()
    b = (base_unit or "").strip().lower()

    if not b:
        b = u

    if u == b:
        return float(qty)

    # Mass
    if u == "kg" and b == "g":
        return float(qty) * 1000.0
    if u == "g" and b == "kg":
        return float(qty) / 1000.0

    # Volume
    if u == "l" and b == "ml":
        return float(qty) * 1000.0
    if u == "ml" and b == "l":
        return float(qty) / 1000.0

    raise HTTPException(status_code=400, detail="Unidade do ingrediente incompatível com a unidade base")


def _consume_stock_for_order(db: Session, current_user: User, o: Order) -> None:
    if getattr(o, "stock_consumed_at", None) is not None:
        return
    if (getattr(o, "business_type", "") or "").strip().lower() != "restaurant":
        return

    order_items = db.scalars(
        select(OrderItem)
        .where(OrderItem.company_id == current_user.company_id)
        .where(OrderItem.branch_id == getattr(o, "branch_id", None))
        .where(OrderItem.order_id == o.id)
        .order_by(desc(OrderItem.id))
    ).all()
    if not order_items:
        o.stock_consumed_at = datetime.utcnow()
        db.add(o)
        return

    for oi in order_items:
        dish = db.get(Product, int(oi.product_id))
        if (
            not dish
            or dish.company_id != current_user.company_id
            or int(getattr(dish, "branch_id", 0) or 0) != int(getattr(o, "branch_id", 0) or 0)
        ):
            continue

        recipe = db.scalar(
            select(Recipe)
            .where(Recipe.company_id == current_user.company_id)
            .where(Recipe.branch_id == int(getattr(o, "branch_id", current_user.branch_id) or current_user.branch_id))
            .where(Recipe.product_id == int(dish.id))
            .where(Recipe.is_active.is_(True))
            .order_by(Recipe.id.desc())
            .limit(1)
        )
        if not recipe:
            continue

        recipe_items = db.scalars(
            select(RecipeItem).where(RecipeItem.recipe_id == recipe.id).order_by(RecipeItem.id.asc())
        ).all()
        if not recipe_items:
            continue

        yield_qty = float(getattr(recipe, "yield_qty", 1) or 1)
        if yield_qty <= 0:
            yield_qty = 1

        ordered_qty = float(getattr(oi, "qty", 0) or 0)
        if ordered_qty <= 0:
            continue

        scale = ordered_qty / yield_qty

        for ri in recipe_items:
            ingredient = db.get(Product, int(ri.ingredient_product_id))
            if (
                not ingredient
                or ingredient.company_id != current_user.company_id
                or int(getattr(ingredient, "branch_id", 0) or 0) != int(getattr(o, "branch_id", 0) or 0)
                or not bool(getattr(ingredient, "is_active", True))
            ):
                raise HTTPException(status_code=400, detail="Ingrediente inválido na ficha técnica")

            location_id = int(getattr(ingredient, "default_location_id", 0) or 0)
            if location_id <= 0:
                raise HTTPException(status_code=400, detail="Ingrediente sem local padrão de stock")

            base_unit = None
            attrs = getattr(ingredient, "attributes", None) or {}
            if isinstance(attrs, dict):
                base_unit = attrs.get("base_unit")

            recipe_unit = str(getattr(ri, "unit", "un") or "un")
            recipe_qty = float(getattr(ri, "qty", 0) or 0)
            if recipe_qty <= 0:
                continue

            waste = float(getattr(ri, "waste_percent", 0) or 0)
            if waste < 0:
                waste = 0

            qty_in_base = _convert_qty(recipe_qty, recipe_unit, str(base_unit or recipe_unit))
            qty_with_waste = qty_in_base * (1.0 + (waste / 100.0))
            consume_qty = round(qty_with_waste * scale, 3)
            if consume_qty <= 0:
                continue

            stock = _get_or_create_stock_row(
                db,
                company_id=current_user.company_id,
                branch_id=int(getattr(o, "branch_id", current_user.branch_id) or current_user.branch_id),
                product_id=int(ingredient.id),
                location_id=location_id,
            )
            before = float(getattr(stock, "qty_on_hand", 0) or 0)
            stock.qty_on_hand = round(before - consume_qty, 3)
            db.add(stock)

            db.add(
                StockMovement(
                    company_id=current_user.company_id,
                    branch_id=int(getattr(o, "branch_id", current_user.branch_id) or current_user.branch_id),
                    product_id=int(ingredient.id),
                    location_id=location_id,
                    movement_type="consume_recipe",
                    qty_delta=-consume_qty,
                    reference_type="order",
                    reference_id=int(o.id),
                    notes=f"Consumo por receita do produto {int(dish.id)} (pedido {int(o.id)})",
                    created_by=int(getattr(current_user, "id", 0) or 0) or None,
                )
            )

    o.stock_consumed_at = datetime.utcnow()
    db.add(o)


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
        order_uuid=getattr(o, "order_uuid", None),
        order_type=getattr(o, "order_type", "table") or "table",
        delivery_kind=getattr(o, "delivery_kind", None),
        customer_name=getattr(o, "customer_name", None),
        customer_phone=getattr(o, "customer_phone", None),
        delivery_address=getattr(o, "delivery_address", None),
        delivery_zone_name=getattr(o, "delivery_zone_name", None),
        delivery_fee=float(getattr(o, "delivery_fee", 0) or 0),
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
        order_type="table",
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

        # Criar OrderItem
        order_item = OrderItem(
            company_id=current_user.company_id,
            branch_id=int(current_user.branch_id),
            order_id=order.id,
            product_id=it.product_id,
            qty=qty,
            price_at_order=price,
            cost_at_order=cost,
            line_total=line_total,
        )
        db.add(order_item)
        db.flush()  # Para obter o ID do order_item

        # Salvar opções do item (se existirem)
        if hasattr(it, 'options') and it.options:
            for opt in it.options:
                order_item_option = OrderItemOption(
                    company_id=current_user.company_id,
                    branch_id=int(current_user.branch_id),
                    order_item_id=order_item.id,
                    option_group_id=opt.option_group_id,
                    option_id=opt.option_id,
                    option_name=opt.option_name,
                    price_adjustment=opt.price_adjustment,
                    ingredient_impact=opt.ingredient_impact,
                )
                db.add(order_item_option)

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
    prev_status = (getattr(o, "status", None) or "").strip().lower()
    if "status" in data and data["status"] is not None:
        st = str(data["status"]).strip().lower()
        if st not in {"open", "in_progress", "closed", "cancelled"}:
            raise HTTPException(status_code=400, detail="Status inválido")
        o.status = st

        if st == "in_progress" and prev_status != "in_progress":
            _consume_stock_for_order(db, current_user, o)

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

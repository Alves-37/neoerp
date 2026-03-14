from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.deps import get_current_user
from app.models.branch import Branch
from app.models.product import Product
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.user import User
from app.schemas.sales import SaleCreate, SaleItemOut, SaleOut

router = APIRouter()


@router.get("", response_model=list[SaleOut])
@router.get("/", response_model=list[SaleOut], include_in_schema=False)
def list_sales(
    limit: int = 50,
    offset: int = 0,
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    role = (getattr(current_user, "role", "") or "").strip().lower()
    is_admin = role in {"admin", "owner"}

    stmt = select(Sale).where(Sale.company_id == current_user.company_id)

    # Default: always scope to the current user's branch for isolation.
    # Admins can explicitly choose another branch via branch_id.
    effective_branch_id = int(branch_id) if (is_admin and branch_id is not None) else int(current_user.branch_id)
    stmt = stmt.where(Sale.branch_id == effective_branch_id)

    branch = db.get(Branch, effective_branch_id)
    if branch and branch.company_id == current_user.company_id:
        business_type = branch.business_type or "retail"
        stmt = stmt.where(Sale.business_type == business_type)

    if role == "cashier":
        stmt = stmt.where(Sale.cashier_id == current_user.id)

    rows = db.scalars(
        stmt.order_by(desc(Sale.id))
        .limit(limit)
        .offset(offset)
    ).all()

    # attach items
    out: list[SaleOut] = []
    for s in rows:
        cashier_name = None
        if getattr(s, "cashier_id", None):
            cashier = db.get(User, s.cashier_id)
            if cashier and cashier.company_id == current_user.company_id:
                cashier_name = cashier.name

        items = db.scalars(
            select(SaleItem)
            .where(SaleItem.company_id == current_user.company_id)
            .where(SaleItem.branch_id == getattr(s, "branch_id", None))
            .where(SaleItem.sale_id == s.id)
            .order_by(desc(SaleItem.id))
        ).all()

        product_ids = list({int(i.product_id) for i in items if i.product_id is not None})
        products = (
            db.scalars(
                select(Product)
                .where(Product.company_id == current_user.company_id)
                .where(Product.id.in_(product_ids))
            ).all()
            if product_ids
            else []
        )
        product_name_by_id = {int(p.id): p.name for p in products}

        out.append(
            SaleOut(
                id=s.id,
                company_id=s.company_id,
                branch_id=getattr(s, "branch_id", 0) or 0,
                business_type=s.business_type,
                cashier_id=getattr(s, "cashier_id", None),
                cashier_name=cashier_name,
                sale_channel=s.sale_channel,
                table_number=s.table_number,
                seat_number=s.seat_number,
                total=float(s.total),
                net_total=float(getattr(s, "net_total", 0) or 0),
                tax_total=float(getattr(s, "tax_total", 0) or 0),
                include_tax=bool(getattr(s, "include_tax", True)),
                paid=float(s.paid),
                change=float(s.change),
                payment_method=s.payment_method,
                status=s.status,
                created_at=s.created_at,
                items=[
                    SaleItemOut(
                        id=i.id,
                        sale_id=i.sale_id,
                        product_id=i.product_id,
                        product_name=product_name_by_id.get(int(i.product_id)) if i.product_id is not None else None,
                        qty=float(i.qty),
                        price_at_sale=float(i.price_at_sale),
                        cost_at_sale=float(i.cost_at_sale),
                        line_total=float(i.line_total),
                    )
                    for i in items
                ],
            )
        )

    return out


@router.post("", response_model=SaleOut)
def create_sale(
    payload: SaleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not payload.items:
        raise HTTPException(status_code=400, detail="Venda deve ter itens")

    branch = db.get(Branch, int(current_user.branch_id))
    if not branch or branch.company_id != current_user.company_id:
        raise HTTPException(status_code=400, detail="Filial inválida")
    business_type = (branch.business_type or "retail").strip().lower()

    sale_channel = (payload.sale_channel or "counter").strip().lower()
    if sale_channel not in {"counter", "table"}:
        raise HTTPException(status_code=400, detail="Canal de venda inválido")

    table_number = payload.table_number
    seat_number = payload.seat_number

    if business_type == "restaurant" and sale_channel == "table":
        if table_number is None or seat_number is None:
            raise HTTPException(status_code=400, detail="Informe mesa e cliente/assento")
    if sale_channel == "counter":
        table_number = None
        seat_number = None

    include_tax = bool(getattr(payload, "include_tax", True))
    net_total = 0.0
    tax_total = 0.0
    items_to_create: list[SaleItem] = []

    for it in payload.items:
        product = db.get(Product, it.product_id)
        if (
            not product
            or product.company_id != current_user.company_id
            or getattr(product, "branch_id", None) != current_user.branch_id
            or product.business_type != business_type
        ):
            raise HTTPException(status_code=400, detail="Produto inválido para este tipo de negócio")

        qty = float(it.qty or 0)
        if qty <= 0:
            raise HTTPException(status_code=400, detail="Quantidade inválida")

        price = float(it.price_at_sale or 0)
        cost = float(it.cost_at_sale or 0)

        line_net = round(price * qty, 2)
        rate = float(getattr(product, "tax_rate", 0) or 0)
        line_tax = round(line_net * (rate / 100.0), 2) if include_tax and rate > 0 else 0.0
        line_total = round(line_net + line_tax, 2)

        net_total = round(net_total + line_net, 2)
        tax_total = round(tax_total + line_tax, 2)

        items_to_create.append(
            SaleItem(
                company_id=current_user.company_id,
                branch_id=int(current_user.branch_id),
                sale_id=0,  # placeholder
                product_id=it.product_id,
                qty=qty,
                price_at_sale=price,
                cost_at_sale=cost,
                line_total=line_total,
            )
        )

    gross_total = round(net_total + tax_total, 2)

    paid = float(payload.paid or 0)
    change = round(max(0.0, paid - gross_total), 2)

    sale = Sale(
        company_id=current_user.company_id,
        branch_id=int(current_user.branch_id),
        cashier_id=current_user.id,
        business_type=business_type,
        total=gross_total,
        net_total=net_total,
        tax_total=tax_total,
        include_tax=include_tax,
        paid=paid,
        change=change,
        payment_method=(payload.payment_method or "cash"),
        status="paid",
        sale_channel=sale_channel,
        table_number=table_number,
        seat_number=seat_number,
        created_at=datetime.utcnow(),
    )

    db.add(sale)
    db.flush()

    for item in items_to_create:
        item.sale_id = sale.id
        db.add(item)

    db.commit()
    db.refresh(sale)

    saved_items = db.scalars(
        select(SaleItem)
        .where(SaleItem.company_id == current_user.company_id)
        .where(SaleItem.branch_id == getattr(sale, "branch_id", None))
        .where(SaleItem.sale_id == sale.id)
        .order_by(desc(SaleItem.id))
    ).all()

    product_ids = list({int(i.product_id) for i in saved_items if i.product_id is not None})
    products = (
        db.scalars(
            select(Product)
            .where(Product.company_id == current_user.company_id)
            .where(Product.id.in_(product_ids))
        ).all()
        if product_ids
        else []
    )
    product_name_by_id = {int(p.id): p.name for p in products}

    return SaleOut(
        id=sale.id,
        company_id=sale.company_id,
        branch_id=getattr(sale, "branch_id", 0) or 0,
        business_type=sale.business_type,
        cashier_id=getattr(sale, "cashier_id", None),
        cashier_name=current_user.name,
        sale_channel=sale.sale_channel,
        table_number=sale.table_number,
        seat_number=sale.seat_number,
        total=float(sale.total),
        net_total=float(getattr(sale, "net_total", 0) or 0),
        tax_total=float(getattr(sale, "tax_total", 0) or 0),
        include_tax=bool(getattr(sale, "include_tax", True)),
        paid=float(sale.paid),
        change=float(sale.change),
        payment_method=sale.payment_method,
        status=sale.status,
        created_at=sale.created_at,
        items=[
            SaleItemOut(
                id=i.id,
                sale_id=i.sale_id,
                product_id=i.product_id,
                product_name=product_name_by_id.get(int(i.product_id)) if i.product_id is not None else None,
                qty=float(i.qty),
                price_at_sale=float(i.price_at_sale),
                cost_at_sale=float(i.cost_at_sale),
                line_total=float(i.line_total),
            )
            for i in saved_items
        ],
    )

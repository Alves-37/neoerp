from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.deps import get_current_user
from app.models.branch import Branch
from app.models.cash_session import CashSession
from app.models.customer import Customer
from app.models.debt import Debt
from app.models.debt_item import DebtItem
from app.models.product import Product
from app.models.product_stock import ProductStock
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.stock_location import StockLocation
from app.models.stock_movement import StockMovement
from app.models.user import User
from app.schemas.debts import DebtCreate, DebtItemOut, DebtOut, DebtPayPayload

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

    row = db.scalar(
        select(ProductStock)
        .where(ProductStock.company_id == company_id)
        .where(ProductStock.branch_id == int(branch_id))
        .where(ProductStock.product_id == product_id)
        .where(ProductStock.location_id == location_id)
        .with_for_update()
    )
    return row


def _build_debt_out(db: Session, current_user: User, debt: Debt) -> DebtOut:
    items = db.scalars(
        select(DebtItem)
        .where(DebtItem.company_id == current_user.company_id)
        .where(DebtItem.branch_id == int(debt.branch_id))
        .where(DebtItem.debt_id == debt.id)
        .order_by(DebtItem.id.asc())
    ).all()

    out_items: list[DebtItemOut] = []
    for i in items:
        out_items.append(
            DebtItemOut(
                id=int(getattr(i, "id", 0) or 0),
                debt_id=int(getattr(i, "debt_id", 0) or 0),
                product_id=int(getattr(i, "product_id", 0) or 0),
                qty=float(getattr(i, "qty", 0) or 0),
                price_at_debt=float(getattr(i, "price_at_debt", 0) or 0),
                cost_at_debt=float(getattr(i, "cost_at_debt", 0) or 0),
                line_total=float(getattr(i, "line_total", 0) or 0),
            )
        )

    return DebtOut(
        id=debt.id,
        company_id=debt.company_id,
        branch_id=int(debt.branch_id),
        cashier_id=getattr(debt, "cashier_id", None),
        customer_id=getattr(debt, "customer_id", None),
        customer_name=getattr(debt, "customer_name", None),
        customer_nuit=getattr(debt, "customer_nuit", None),
        currency=getattr(debt, "currency", "MZN") or "MZN",
        total=float(debt.total),
        net_total=float(getattr(debt, "net_total", 0) or 0),
        tax_total=float(getattr(debt, "tax_total", 0) or 0),
        include_tax=bool(getattr(debt, "include_tax", True)),
        status=getattr(debt, "status", "open") or "open",
        sale_id=getattr(debt, "sale_id", None),
        created_at=debt.created_at,
        paid_at=getattr(debt, "paid_at", None),
        items=out_items,
    )


@router.get("", response_model=list[DebtOut])
@router.get("/", response_model=list[DebtOut], include_in_schema=False)
def list_debts(
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    branch = db.get(Branch, int(current_user.branch_id))
    if not branch or branch.company_id != current_user.company_id:
        raise HTTPException(status_code=400, detail="Filial inválida")
    business_type = (branch.business_type or "retail").strip().lower()
    if business_type == "restaurant":
        raise HTTPException(status_code=403, detail="Funcionalidade indisponível para restaurante")

    stmt = (
        select(Debt)
        .where(Debt.company_id == current_user.company_id)
        .where(Debt.branch_id == int(current_user.branch_id))
    )
    if status:
        stmt = stmt.where(Debt.status == status)

    rows = db.scalars(stmt.order_by(desc(Debt.id)).limit(limit).offset(offset)).all()
    return [_build_debt_out(db, current_user, d) for d in rows]


@router.post("", response_model=DebtOut)
@router.post("/", response_model=DebtOut, include_in_schema=False)
def create_debt(
    payload: DebtCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not payload.items:
        raise HTTPException(status_code=400, detail="Dívida deve ter itens")

    branch = db.get(Branch, int(current_user.branch_id))
    if not branch or branch.company_id != current_user.company_id:
        raise HTTPException(status_code=400, detail="Filial inválida")
    business_type = (branch.business_type or "retail").strip().lower()
    if business_type == "restaurant":
        raise HTTPException(status_code=403, detail="Funcionalidade indisponível para restaurante")

    include_tax = bool(getattr(payload, "include_tax", True))

    customer_id = None
    customer_name = None
    customer_nuit = None

    if payload.customer_id:
        cust = db.get(Customer, int(payload.customer_id))
        if not cust or cust.company_id != current_user.company_id or cust.branch_id != int(current_user.branch_id):
            raise HTTPException(status_code=404, detail="Cliente não encontrado")
        customer_id = cust.id
        customer_name = cust.name
        customer_nuit = cust.nuit
    else:
        customer_name = (payload.customer_name or "").strip() or None
        customer_nuit = (payload.customer_nuit or "").strip() or None

    if not customer_id and not customer_name:
        raise HTTPException(status_code=400, detail="Informe o cliente para registrar a dívida")

    net_total = 0.0
    tax_total = 0.0
    items_to_create: list[DebtItem] = []

    for it in payload.items:
        product = db.get(Product, it.product_id)
        if (
            not product
            or product.company_id != current_user.company_id
            or getattr(product, "branch_id", None) != current_user.branch_id
            or (product.business_type or "").strip().lower() != business_type
        ):
            raise HTTPException(status_code=400, detail="Produto inválido para este tipo de negócio")

        qty = float(it.qty or 0)
        if qty <= 0:
            raise HTTPException(status_code=400, detail="Quantidade inválida")

        price = float(it.price_at_debt or 0)
        cost = float(it.cost_at_debt or 0)

        line_net = round(price * qty, 2)
        rate = float(getattr(product, "tax_rate", 0) or 0)
        line_tax = round(line_net * (rate / 100.0), 2) if include_tax and rate > 0 else 0.0
        line_total = round(line_net + line_tax, 2)

        net_total = round(net_total + line_net, 2)
        tax_total = round(tax_total + line_tax, 2)

        items_to_create.append(
            DebtItem(
                company_id=current_user.company_id,
                branch_id=int(current_user.branch_id),
                debt_id=0,
                product_id=it.product_id,
                qty=qty,
                price_at_debt=price,
                cost_at_debt=cost,
                line_total=line_total,
            )
        )

    gross_total = round(net_total + tax_total, 2)

    debt = Debt(
        company_id=current_user.company_id,
        branch_id=int(current_user.branch_id),
        cashier_id=current_user.id,
        customer_id=customer_id,
        customer_name=customer_name,
        customer_nuit=customer_nuit,
        currency="MZN",
        total=gross_total,
        net_total=net_total,
        tax_total=tax_total,
        include_tax=include_tax,
        status="open",
        sale_id=None,
        created_at=datetime.utcnow(),
        paid_at=None,
    )

    try:
        db.add(debt)
        db.flush()
        for item in items_to_create:
            item.debt_id = debt.id
            db.add(item)
        db.commit()
        db.refresh(debt)
    except Exception:
        db.rollback()
        raise

    return _build_debt_out(db, current_user, debt)


@router.post("/{debt_id}/pay", response_model=DebtOut)
def pay_debt(
    debt_id: int,
    payload: DebtPayPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    branch = db.get(Branch, int(current_user.branch_id))
    if not branch or branch.company_id != current_user.company_id:
        raise HTTPException(status_code=400, detail="Filial inválida")
    business_type = (branch.business_type or "retail").strip().lower()
    if business_type == "restaurant":
        raise HTTPException(status_code=403, detail="Funcionalidade indisponível para restaurante")

    debt = db.get(Debt, debt_id)
    if not debt or debt.company_id != current_user.company_id or debt.branch_id != int(current_user.branch_id):
        raise HTTPException(status_code=404, detail="Dívida não encontrada")
    if (debt.status or "open") != "open":
        raise HTTPException(status_code=400, detail="Dívida já foi processada")

    if not getattr(current_user, "establishment_id", None):
        raise HTTPException(status_code=400, detail="Ponto inválido")

    if not getattr(debt, "customer_id", None) and not (getattr(debt, "customer_name", None) or "").strip():
        raise HTTPException(status_code=400, detail="Dívida sem cliente. Informe o cliente antes de pagar")

    cash_session = db.scalar(
        select(CashSession)
        .where(CashSession.company_id == current_user.company_id)
        .where(CashSession.branch_id == int(current_user.branch_id))
        .where(CashSession.establishment_id == int(current_user.establishment_id))
        .where(CashSession.opened_by == current_user.id)
        .where(CashSession.status == "open")
        .order_by(CashSession.id.desc())
        .limit(1)
    )
    if not cash_session:
        raise HTTPException(status_code=409, detail="Caixa fechado. Abra o caixa para registrar pagamentos de dívida")

    items = db.scalars(
        select(DebtItem)
        .where(DebtItem.company_id == current_user.company_id)
        .where(DebtItem.branch_id == int(current_user.branch_id))
        .where(DebtItem.debt_id == debt.id)
        .order_by(DebtItem.id.asc())
    ).all()
    if not items:
        raise HTTPException(status_code=400, detail="Dívida sem itens")

    paid = float(payload.paid or 0)
    gross_total = float(getattr(debt, "total", 0) or 0)
    change = round(max(0.0, paid - gross_total), 2)

    # Group stock deductions by (product_id, location_id)
    stock_deductions: dict[tuple[int, int], float] = {}

    for it in items:
        product = db.get(Product, int(it.product_id))
        if (
            not product
            or product.company_id != current_user.company_id
            or getattr(product, "branch_id", None) != current_user.branch_id
            or (product.business_type or "").strip().lower() != business_type
        ):
            raise HTTPException(status_code=400, detail="Produto inválido para este tipo de negócio")

        track_stock = bool(getattr(product, "track_stock", True))
        if not track_stock:
            continue

        loc_id = int(getattr(product, "default_location_id", 0) or 0)
        if loc_id <= 0:
            raise HTTPException(status_code=400, detail="Produto sem local padrão de stock")

        loc = db.get(StockLocation, loc_id)
        if not loc or loc.company_id != current_user.company_id or not loc.is_active:
            raise HTTPException(status_code=400, detail="Local padrão de stock inválido")
        if getattr(loc, "branch_id", None) != current_user.branch_id:
            raise HTTPException(status_code=400, detail="Local padrão de stock inválido")

        key = (int(product.id), int(loc.id))
        stock_deductions[key] = float(stock_deductions.get(key, 0.0)) + float(it.qty or 0)

    sale = Sale(
        company_id=current_user.company_id,
        branch_id=int(current_user.branch_id),
        establishment_id=int(current_user.establishment_id),
        cashier_id=current_user.id,
        cash_session_id=int(cash_session.id),
        business_type=business_type,
        total=float(getattr(debt, "total", 0) or 0),
        net_total=float(getattr(debt, "net_total", 0) or 0),
        tax_total=float(getattr(debt, "tax_total", 0) or 0),
        include_tax=bool(getattr(debt, "include_tax", True)),
        paid=paid,
        change=change,
        payment_method=(payload.payment_method or "cash"),
        status="paid",
        sale_channel="debt",
        table_number=None,
        seat_number=None,
        created_at=datetime.utcnow(),
    )

    try:
        db.add(sale)
        db.flush()

        for it in items:
            sale_item = SaleItem(
                company_id=current_user.company_id,
                branch_id=int(current_user.branch_id),
                sale_id=sale.id,
                product_id=int(it.product_id),
                qty=float(it.qty or 0),
                price_at_sale=float(it.price_at_debt or 0),
                cost_at_sale=float(it.cost_at_debt or 0),
                line_total=float(it.line_total or 0),
            )
            db.add(sale_item)

        for (product_id, location_id), qty_sum in stock_deductions.items():
            stock = _get_or_create_stock_row(db, current_user.company_id, int(current_user.branch_id), product_id, location_id)
            before = float(stock.qty_on_hand or 0)
            after = before - float(qty_sum or 0)
            if after < 0:
                raise HTTPException(status_code=400, detail="Stock insuficiente para processar a dívida")
            stock.qty_on_hand = after

            mv = StockMovement(
                company_id=current_user.company_id,
                branch_id=int(current_user.branch_id),
                product_id=product_id,
                location_id=location_id,
                movement_type="sale_out",
                qty_delta=-float(qty_sum or 0),
                reference_type="sale",
                reference_id=sale.id,
                notes=f"Debt #{debt.id}",
                created_by=current_user.id,
            )
            db.add(mv)

        debt.status = "paid"
        debt.paid_at = datetime.utcnow()
        debt.sale_id = sale.id
        db.add(debt)

        db.commit()
        db.refresh(debt)
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise

    return _build_debt_out(db, current_user, debt)

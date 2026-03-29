from datetime import datetime
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.deps import get_current_user
from app.models.cash_session import CashSession
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.expense import Expense
from app.models.user import User
from app.models.company import Company
from app.schemas.cash_sessions import CashSessionCloseRequest, CashSessionOpenRequest, CashSessionOut, CashSessionPaymentTotals, CashSessionSummaryOut
from app.utils.pdf import cash_session_close_pdf_elements, render_pdf

router = APIRouter()


def _is_admin(current_user: User) -> bool:
    role = (getattr(current_user, "role", "") or "").strip().lower()
    return role in {"admin", "owner"}


def _get_open_session(db: Session, current_user: User) -> CashSession | None:
    if not getattr(current_user, "branch_id", None):
        return None

    if not getattr(current_user, "establishment_id", None):
        return None

    return db.scalar(
        select(CashSession)
        .where(CashSession.company_id == current_user.company_id)
        .where(CashSession.branch_id == int(current_user.branch_id))
        .where(CashSession.establishment_id == int(current_user.establishment_id))
        .where(CashSession.opened_by == current_user.id)
        .where(CashSession.status == "open")
        .order_by(CashSession.id.desc())
        .limit(1)
    )


@router.get("/current", response_model=CashSessionOut | None)
def current_cash_session(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    row = _get_open_session(db, current_user)
    return row


@router.post("/open", response_model=CashSessionOut)
def open_cash_session(
    payload: CashSessionOpenRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not getattr(current_user, "branch_id", None):
        raise HTTPException(status_code=400, detail="Filial inválida")

    if not getattr(current_user, "establishment_id", None):
        raise HTTPException(status_code=400, detail="Ponto inválido")

    existing = _get_open_session(db, current_user)
    if existing:
        raise HTTPException(status_code=409, detail="Já existe um caixa aberto")

    opening = float(payload.opening_balance or 0)
    if opening < 0:
        raise HTTPException(status_code=400, detail="Valor de abertura inválido")

    row = CashSession(
        company_id=current_user.company_id,
        branch_id=int(current_user.branch_id),
        establishment_id=int(current_user.establishment_id),
        opened_by=current_user.id,
        opened_at=datetime.utcnow(),
        opening_balance=opening,
        status="open",
        closing_balance_expected=opening,
        closing_balance_counted=0,
        difference=0,
        notes=None,
    )

    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/{cash_session_id}/summary", response_model=CashSessionSummaryOut)
def cash_session_summary(
    cash_session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = db.get(CashSession, cash_session_id)
    if not row or row.company_id != current_user.company_id or row.branch_id != int(current_user.branch_id):
        raise HTTPException(status_code=404, detail="Caixa não encontrado")

    if not getattr(current_user, "establishment_id", None):
        raise HTTPException(status_code=400, detail="Ponto inválido")
    if int(getattr(row, "establishment_id", 0) or 0) != int(current_user.establishment_id):
        raise HTTPException(status_code=404, detail="Caixa não encontrado")

    if (not _is_admin(current_user)) and row.opened_by != current_user.id:
        raise HTTPException(status_code=403, detail="Sem permissão para ver este caixa")

    paid_statuses = ["paid", "completed", "closed"]

    totals_row = db.execute(
        select(
            func.count(Sale.id).label("sales_count"),
            func.coalesce(func.sum(Sale.total), 0).label("gross_total"),
            func.coalesce(func.sum(Sale.net_total), 0).label("net_total"),
            func.coalesce(func.sum(Sale.tax_total), 0).label("tax_total"),
        )
        .select_from(Sale)
        .where(Sale.company_id == current_user.company_id)
        .where(Sale.branch_id == int(current_user.branch_id))
        .where(Sale.establishment_id == int(current_user.establishment_id))
        .where(Sale.cash_session_id == row.id)
        .where(Sale.status.in_(paid_statuses))
    ).one()

    by_pay_rows = db.execute(
        select(
            Sale.payment_method.label("payment_method"),
            func.count(Sale.id).label("sales_count"),
            func.coalesce(func.sum(Sale.total), 0).label("gross_total"),
            func.coalesce(func.sum(Sale.net_total), 0).label("net_total"),
            func.coalesce(func.sum(Sale.tax_total), 0).label("tax_total"),
        )
        .select_from(Sale)
        .where(Sale.company_id == current_user.company_id)
        .where(Sale.branch_id == int(current_user.branch_id))
        .where(Sale.establishment_id == int(current_user.establishment_id))
        .where(Sale.cash_session_id == row.id)
        .where(Sale.status.in_(paid_statuses))
        .group_by(Sale.payment_method)
        .order_by(Sale.payment_method.asc())
    ).all()

    by_payment: list[CashSessionPaymentTotals] = []
    cash_sales_total = 0.0
    for pm, cnt, gross, net, tax in by_pay_rows:
        pm_s = (pm or "").strip() or "unknown"
        gross_f = float(gross or 0)
        net_f = float(net or 0)
        tax_f = float(tax or 0)
        if pm_s == "cash":
            cash_sales_total = gross_f
        by_payment.append(
            CashSessionPaymentTotals(
                payment_method=pm_s,
                sales_count=int(cnt or 0),
                gross_total=gross_f,
                net_total=net_f,
                tax_total=tax_f,
            )
        )

    opening_balance = float(row.opening_balance or 0)
    
    # Total geral de vendas (todos os métodos de pagamento)
    total_sales_all_methods = float(getattr(totals_row, "gross_total", 0) or 0)
    
    cash_expenses_total = db.scalar(
        select(func.coalesce(func.sum(Expense.amount), 0))
        .where(Expense.company_id == current_user.company_id)
        .where(Expense.branch_id == int(current_user.branch_id))
        .where(Expense.establishment_id == int(current_user.establishment_id))
        .where(Expense.paid_cash_session_id == row.id)
        .where(Expense.status == "paid")
        .where(Expense.is_void.is_(False))
    )
    
    # Esperado em dinheiro (só vendas em dinheiro)
    expected_cash = round(opening_balance + float(cash_sales_total or 0) - float(cash_expenses_total or 0), 2)

    return CashSessionSummaryOut(
        cash_session_id=row.id,
        company_id=row.company_id,
        branch_id=row.branch_id,
        establishment_id=getattr(row, "establishment_id", None),
        opened_by=row.opened_by,
        opened_at=row.opened_at,
        status=row.status,
        closed_at=row.closed_at,
        opening_balance=opening_balance,
        cash_sales_total=float(cash_sales_total or 0),
        cash_expenses_total=float(cash_expenses_total or 0),
        expected_cash=float(expected_cash),
        sales_count=int(getattr(totals_row, "sales_count", 0) or 0),
        gross_total=float(getattr(totals_row, "gross_total", 0) or 0),
        net_total=float(getattr(totals_row, "net_total", 0) or 0),
        tax_total=float(getattr(totals_row, "tax_total", 0) or 0),
        total_sales_all_methods=total_sales_all_methods,
        by_payment_method=by_payment,
    )


@router.post("/{cash_session_id}/close", response_model=CashSessionOut)
def close_cash_session(
    cash_session_id: int,
    payload: CashSessionCloseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = db.get(CashSession, cash_session_id)
    if not row or row.company_id != current_user.company_id or row.branch_id != int(current_user.branch_id):
        raise HTTPException(status_code=404, detail="Caixa não encontrado")

    if not getattr(current_user, "establishment_id", None):
        raise HTTPException(status_code=400, detail="Ponto inválido")
    if int(getattr(row, "establishment_id", 0) or 0) != int(current_user.establishment_id):
        raise HTTPException(status_code=404, detail="Caixa não encontrado")

    if row.status != "open":
        raise HTTPException(status_code=409, detail="Caixa já está fechado")

    if (not _is_admin(current_user)) and row.opened_by != current_user.id:
        raise HTTPException(status_code=403, detail="Sem permissão para fechar este caixa")

    counted = float(payload.closing_balance_counted or 0)
    if counted < 0:
        raise HTTPException(status_code=400, detail="Valor de fecho inválido")

    paid_statuses = ["paid", "completed", "closed"]

    cash_sales_total = db.scalar(
        select(func.coalesce(func.sum(Sale.total), 0))
        .where(Sale.company_id == current_user.company_id)
        .where(Sale.branch_id == int(current_user.branch_id))
        .where(Sale.establishment_id == int(current_user.establishment_id))
        .where(Sale.cashier_id == row.opened_by)
        .where(Sale.cash_session_id == row.id)
        .where(Sale.payment_method == "cash")
        .where(Sale.status.in_(paid_statuses))
    )

    cash_expenses_total = db.scalar(
        select(func.coalesce(func.sum(Expense.amount), 0))
        .where(Expense.company_id == current_user.company_id)
        .where(Expense.branch_id == int(current_user.branch_id))
        .where(Expense.establishment_id == int(current_user.establishment_id))
        .where(Expense.paid_cash_session_id == row.id)
        .where(Expense.status == "paid")
        .where(Expense.is_void.is_(False))
    )
    expected = float(row.opening_balance or 0) + float(cash_sales_total or 0) - float(cash_expenses_total or 0)
    diff = round(counted - expected, 2)

    row.closing_balance_expected = expected
    row.closing_balance_counted = counted
    row.difference = diff
    row.closed_at = datetime.utcnow()
    row.closed_by = current_user.id
    row.status = "closed"
    row.notes = (payload.notes or "").strip() or None

    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/{cash_session_id}/items")
def cash_session_items(
    cash_session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retorna todos os itens vendidos na sessão de caixa."""
    row = db.get(CashSession, cash_session_id)
    if not row or row.company_id != current_user.company_id or row.branch_id != int(current_user.branch_id):
        raise HTTPException(status_code=404, detail="Caixa não encontrado")

    if not getattr(current_user, "establishment_id", None):
        raise HTTPException(status_code=400, detail="Ponto inválido")
    if int(getattr(row, "establishment_id", 0) or 0) != int(current_user.establishment_id):
        raise HTTPException(status_code=404, detail="Caixa não encontrado")

    if (not _is_admin(current_user)) and row.opened_by != current_user.id:
        raise HTTPException(status_code=403, detail="Sem permissão para ver este caixa")

    paid_statuses = ["paid", "completed", "closed"]

    # Buscar itens vendidos nesta sessão
    items_query = (
        select(
            SaleItem.product_id,
            func.coalesce(SaleItem.product_name, "Produto #" + SaleItem.product_id.cast(str)).label("product_name"),
            func.sum(SaleItem.quantity).label("quantity"),
            func.coalesce(SaleItem.unit_price, 0).label("unit_price"),
            func.sum(SaleItem.total).label("total"),
        )
        .select_from(SaleItem)
        .join(Sale, SaleItem.sale_id == Sale.id)
        .where(Sale.company_id == current_user.company_id)
        .where(Sale.branch_id == int(current_user.branch_id))
        .where(Sale.establishment_id == int(current_user.establishment_id))
        .where(Sale.cash_session_id == row.id)
        .where(Sale.status.in_(paid_statuses))
        .group_by(SaleItem.product_id, SaleItem.product_name, SaleItem.unit_price)
        .order_by(SaleItem.product_name.asc())
    )

    items = []
    for product_id, product_name, quantity, unit_price, total in db.execute(items_query):
        items.append({
            "product_id": int(product_id),
            "product_name": product_name or f"Produto #{product_id}",
            "quantity": float(quantity or 0),
            "unit_price": float(unit_price or 0),
            "total": float(total or 0),
        })

    return items


@router.get("/{cash_session_id}/close-pdf")
def cash_session_close_pdf(
    cash_session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Gera PDF do relatório de fecho de caixa (igual PDV3)."""
    row = db.get(CashSession, cash_session_id)
    if not row or row.company_id != current_user.company_id or row.branch_id != int(current_user.branch_id):
        raise HTTPException(status_code=404, detail="Caixa não encontrado")

    if not getattr(current_user, "establishment_id", None):
        raise HTTPException(status_code=400, detail="Ponto inválido")
    if int(getattr(row, "establishment_id", 0) or 0) != int(current_user.establishment_id):
        raise HTTPException(status_code=404, detail="Caixa não encontrado")

    if (not _is_admin(current_user)) and row.opened_by != current_user.id:
        raise HTTPException(status_code=403, detail="Sem permissão para ver este caixa")

    company = db.get(Company, current_user.company_id)
    company_data = company.__dict__ if company else {}

    # Buscar dados do usuário que abriu o caixa
    cashier = db.get(User, row.opened_by)
    cashier_name = (getattr(cashier, "name", None) or getattr(cashier, "username", "-")).strip() if cashier else "-"

    # Calcular totais de vendas
    paid_statuses = ["paid", "completed", "closed"]
    cash_sales_total = db.scalar(
        select(func.coalesce(func.sum(Sale.total), 0))
        .where(Sale.company_id == current_user.company_id)
        .where(Sale.branch_id == int(current_user.branch_id))
        .where(Sale.establishment_id == int(current_user.establishment_id))
        .where(Sale.cash_session_id == row.id)
        .where(Sale.payment_method == "cash")
        .where(Sale.status.in_(paid_statuses))
    )

    # Calcular totais de despesas pagas neste caixa
    cash_expenses_total = db.scalar(
        select(func.coalesce(func.sum(Expense.amount), 0))
        .where(Expense.company_id == current_user.company_id)
        .where(Expense.branch_id == int(current_user.branch_id))
        .where(Expense.establishment_id == int(current_user.establishment_id))
        .where(Expense.paid_cash_session_id == row.id)
        .where(Expense.status == "paid")
        .where(Expense.is_void.is_(False))
    )

    # Buscar detalhes das despesas
    expenses = db.execute(
        select(Expense)
        .where(Expense.company_id == current_user.company_id)
        .where(Expense.branch_id == int(current_user.branch_id))
        .where(Expense.establishment_id == int(current_user.establishment_id))
        .where(Expense.paid_cash_session_id == row.id)
        .where(Expense.status == "paid")
        .where(Expense.is_void.is_(False))
    ).scalars().all()

    opening = float(row.opening_balance or 0)
    expected = opening + float(cash_sales_total or 0) - float(cash_expenses_total or 0)
    counted = float(row.closing_balance_counted or 0)
    difference = round(counted - expected, 2)

    closed_at_str = "-"
    if row.closed_at:
        closed_at_str = row.closed_at.strftime('%d/%m/%Y %H:%M')
    elif row.status == "open":
        closed_at_str = "Caixa ainda aberto"

    pdf_data = {
        "id": int(row.id),
        "status": row.status,
        "closed_at": closed_at_str,
        "cashier_name": cashier_name,
        "opening": opening,
        "cash_sales_total": float(cash_sales_total or 0),
        "cash_expenses_total": float(cash_expenses_total or 0),
        "expected": expected,
        "counted": counted,
        "difference": float(difference or 0),
        "expenses": [
            {
                "category": getattr(exp.category, 'name', '-') if hasattr(exp, 'category') and exp.category else '-',
                "description": (getattr(exp, 'description', '') or ''),
                "amount": float(getattr(exp, 'amount', 0) or 0),
            }
            for exp in (expenses or [])
        ],
        "notes": row.notes,
    }

    elements = cash_session_close_pdf_elements(pdf_data, company_data)
    pdf_bytes = render_pdf("Fechamento de Caixa", elements)
    filename = f"fechamento_caixa_{cashier_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )

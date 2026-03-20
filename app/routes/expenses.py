from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.deps import get_current_user
from app.models.branch import Branch
from app.models.cash_session import CashSession
from app.models.expense import Expense
from app.models.expense_category import ExpenseCategory
from app.models.user import User
from app.schemas.expenses import ExpenseCreate, ExpenseOut, ExpensePayRequest, ExpenseUpdate

router = APIRouter()


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


@router.get("", response_model=list[ExpenseOut])
@router.get("/", response_model=list[ExpenseOut], include_in_schema=False)
def list_expenses(
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    branch = db.get(Branch, int(current_user.branch_id))
    if not branch or branch.company_id != current_user.company_id:
        raise HTTPException(status_code=400, detail="Filial inválida")

    stmt = (
        select(Expense)
        .where(Expense.company_id == current_user.company_id)
        .where(Expense.branch_id == int(current_user.branch_id))
        .where(Expense.is_void.is_(False))
    )
    if status:
        stmt = stmt.where(Expense.status == status)

    rows = db.scalars(stmt.order_by(desc(Expense.id)).limit(limit).offset(offset)).all()
    return rows


@router.post("", response_model=ExpenseOut)
@router.post("/", response_model=ExpenseOut, include_in_schema=False)
def create_expense(
    payload: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    branch = db.get(Branch, int(current_user.branch_id))
    if not branch or branch.company_id != current_user.company_id:
        raise HTTPException(status_code=400, detail="Filial inválida")

    description = (payload.description or "").strip()
    if not description:
        raise HTTPException(status_code=400, detail="Descrição inválida")

    amount = float(payload.amount or 0)
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Valor inválido")

    category_id = payload.category_id
    category_name = None
    if category_id is not None:
        cat = db.get(ExpenseCategory, int(category_id))
        if not cat or cat.company_id != current_user.company_id or cat.branch_id != int(current_user.branch_id):
            raise HTTPException(status_code=404, detail="Categoria não encontrada")
        category_name = cat.name

    row = Expense(
        company_id=current_user.company_id,
        branch_id=int(current_user.branch_id),
        establishment_id=int(current_user.establishment_id) if getattr(current_user, "establishment_id", None) else None,
        category_id=int(category_id) if category_id is not None else None,
        category_name=category_name,
        description=description,
        amount=amount,
        due_date=payload.due_date,
        status="pending",
        paid_at=None,
        paid_cash_session_id=None,
        paid_by=None,
        is_void=False,
        voided_at=None,
        voided_by=None,
        void_reason=None,
        created_at=datetime.now(tz=timezone.utc),
    )

    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.put("/{expense_id}", response_model=ExpenseOut)
def update_expense(
    expense_id: int,
    payload: ExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = db.get(Expense, expense_id)
    if not row or row.company_id != current_user.company_id or row.branch_id != int(current_user.branch_id) or row.is_void:
        raise HTTPException(status_code=404, detail="Despesa não encontrada")

    if (row.status or "pending") != "pending":
        raise HTTPException(status_code=409, detail="Não é possível editar uma despesa paga")

    if payload.description is not None:
        description = (payload.description or "").strip()
        if not description:
            raise HTTPException(status_code=400, detail="Descrição inválida")
        row.description = description

    if payload.amount is not None:
        amount = float(payload.amount or 0)
        if amount <= 0:
            raise HTTPException(status_code=400, detail="Valor inválido")
        row.amount = amount

    if payload.due_date is not None:
        row.due_date = payload.due_date

    if "category_id" in getattr(payload, "__fields_set__", set()):
        if payload.category_id is None:
            row.category_id = None
            row.category_name = None
        else:
            cat = db.get(ExpenseCategory, int(payload.category_id))
            if not cat or cat.company_id != current_user.company_id or cat.branch_id != int(current_user.branch_id):
                raise HTTPException(status_code=404, detail="Categoria não encontrada")
            row.category_id = int(cat.id)
            row.category_name = cat.name

    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.post("/{expense_id}/pay", response_model=ExpenseOut)
def pay_expense(
    expense_id: int,
    payload: ExpensePayRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = db.get(Expense, expense_id)
    if not row or row.company_id != current_user.company_id or row.branch_id != int(current_user.branch_id) or row.is_void:
        raise HTTPException(status_code=404, detail="Despesa não encontrada")

    if (row.status or "pending") == "paid":
        return row

    cash_session = _get_open_session(db, current_user)
    if not cash_session:
        raise HTTPException(status_code=409, detail="Caixa fechado. Abra o caixa para pagar despesas")

    paid_at = payload.paid_at
    if paid_at is None:
        paid_at = datetime.now(tz=timezone.utc)

    row.status = "paid"
    row.paid_at = paid_at
    row.paid_cash_session_id = int(cash_session.id)
    row.paid_by = int(current_user.id)

    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{expense_id}")
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = db.get(Expense, expense_id)
    if not row or row.company_id != current_user.company_id or row.branch_id != int(current_user.branch_id) or row.is_void:
        raise HTTPException(status_code=404, detail="Despesa não encontrada")

    if (row.status or "pending") != "pending":
        raise HTTPException(status_code=409, detail="Não é possível remover uma despesa paga")

    row.is_void = True
    row.voided_at = datetime.now(tz=timezone.utc)
    row.voided_by = int(current_user.id)
    row.void_reason = "deleted"

    db.add(row)
    db.commit()

    return {"ok": True}

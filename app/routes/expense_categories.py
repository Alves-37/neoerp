from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import asc, select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.deps import get_current_user
from app.models.branch import Branch
from app.models.expense_category import ExpenseCategory
from app.models.user import User
from app.schemas.expense_categories import ExpenseCategoryCreate, ExpenseCategoryOut, ExpenseCategoryUpdate

router = APIRouter()


@router.get("", response_model=list[ExpenseCategoryOut])
@router.get("/", response_model=list[ExpenseCategoryOut], include_in_schema=False)
def list_expense_categories(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    branch = db.get(Branch, int(current_user.branch_id))
    if not branch or branch.company_id != current_user.company_id:
        raise HTTPException(status_code=400, detail="Filial inválida")

    rows = db.scalars(
        select(ExpenseCategory)
        .where(ExpenseCategory.company_id == current_user.company_id)
        .where(ExpenseCategory.branch_id == int(current_user.branch_id))
        .order_by(asc(ExpenseCategory.name))
    ).all()
    return rows


@router.post("", response_model=ExpenseCategoryOut)
@router.post("/", response_model=ExpenseCategoryOut, include_in_schema=False)
def create_expense_category(
    payload: ExpenseCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    name = (payload.name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Nome inválido")

    branch = db.get(Branch, int(current_user.branch_id))
    if not branch or branch.company_id != current_user.company_id:
        raise HTTPException(status_code=400, detail="Filial inválida")

    existing = db.scalar(
        select(ExpenseCategory)
        .where(ExpenseCategory.company_id == current_user.company_id)
        .where(ExpenseCategory.branch_id == int(current_user.branch_id))
        .where(ExpenseCategory.name == name)
        .limit(1)
    )
    if existing:
        return existing

    row = ExpenseCategory(company_id=current_user.company_id, branch_id=int(current_user.branch_id), name=name)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.put("/{category_id}", response_model=ExpenseCategoryOut)
def update_expense_category(
    category_id: int,
    payload: ExpenseCategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = db.get(ExpenseCategory, category_id)
    if not row or row.company_id != current_user.company_id or row.branch_id != int(current_user.branch_id):
        raise HTTPException(status_code=404, detail="Categoria não encontrada")

    name = (payload.name or "").strip() if payload.name is not None else None
    if name is not None and not name:
        raise HTTPException(status_code=400, detail="Nome inválido")

    if name is not None:
        dup = db.scalar(
            select(ExpenseCategory)
            .where(ExpenseCategory.company_id == current_user.company_id)
            .where(ExpenseCategory.branch_id == int(current_user.branch_id))
            .where(ExpenseCategory.name == name)
            .where(ExpenseCategory.id != row.id)
            .limit(1)
        )
        if dup:
            raise HTTPException(status_code=409, detail="Já existe uma categoria com este nome")
        row.name = name

    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{category_id}")
def delete_expense_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = db.get(ExpenseCategory, category_id)
    if not row or row.company_id != current_user.company_id or row.branch_id != int(current_user.branch_id):
        raise HTTPException(status_code=404, detail="Categoria não encontrada")

    db.delete(row)
    db.commit()
    return {"ok": True}

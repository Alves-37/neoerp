from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.deps import get_current_user
from app.models.branch import Branch
from app.models.user import User
from app.schemas.branches import BranchCreate, BranchOut, BranchUpdate

router = APIRouter()


class SwitchBranchRequest(BaseModel):
    branch_id: int


@router.get("", response_model=list[BranchOut])
@router.get("/", response_model=list[BranchOut])
@router.get("/", response_model=list[BranchOut], include_in_schema=False)
def list_branches(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = db.scalars(
        select(Branch)
        .where(Branch.company_id == current_user.company_id)
        .order_by(Branch.name.asc(), Branch.id.asc())
    ).all()
    return rows


@router.get("/me", response_model=BranchOut)
@router.get("/me/", response_model=BranchOut, include_in_schema=False)
def get_my_branch(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not getattr(current_user, "branch_id", None):
        raise HTTPException(status_code=404, detail="Filial não encontrada")

    b = db.get(Branch, current_user.branch_id)
    if not b or b.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Filial não encontrada")
    return b


@router.get("/{branch_id}", response_model=BranchOut)
@router.get("/{branch_id}/", response_model=BranchOut, include_in_schema=False)
def get_branch(
    branch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    b = db.get(Branch, branch_id)
    if not b or b.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Filial não encontrada")
    return b


@router.post("", response_model=BranchOut)
@router.post("/", response_model=BranchOut)
@router.post("/", response_model=BranchOut, include_in_schema=False)
def create_branch(
    payload: BranchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    b = Branch(company_id=current_user.company_id, **payload.model_dump())
    db.add(b)
    db.commit()
    db.refresh(b)
    return b


@router.post("/switch", response_model=BranchOut)
@router.post("/switch/", response_model=BranchOut, include_in_schema=False)
def switch_my_branch(
    payload: SwitchBranchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    b = db.get(Branch, payload.branch_id)
    if not b or b.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Filial não encontrada")
    if not getattr(b, "is_active", True):
        raise HTTPException(status_code=400, detail="Filial inativa")

    current_user.branch_id = b.id
    db.add(current_user)
    db.commit()
    return b


@router.put("/{branch_id}", response_model=BranchOut)
@router.put("/{branch_id}/", response_model=BranchOut, include_in_schema=False)
def update_branch(
    branch_id: int,
    payload: BranchUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    b = db.get(Branch, branch_id)
    if not b or b.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Filial não encontrada")

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(b, k, v)

    db.add(b)
    db.commit()
    db.refresh(b)
    return b

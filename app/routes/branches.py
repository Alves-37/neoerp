from fastapi import APIRouter, Depends, HTTPException
from urllib.parse import urlparse
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
    role = (getattr(current_user, "role", "") or "").strip().lower()
    if role not in {"admin", "owner"}:
        raise HTTPException(status_code=403, detail="Apenas admin pode trocar de filial")

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

    role = (getattr(current_user, "role", "") or "").strip().lower()
    is_admin = role in {"admin", "owner"}

    public_fields = {"public_menu_enabled", "public_menu_subdomain", "public_menu_custom_domain"}
    touching_public = any(k in data for k in public_fields)
    if touching_public and not is_admin:
        raise HTTPException(status_code=403, detail="Apenas admin pode configurar o menu público")

    # Validate uniqueness (global) for subdomain and custom domain.
    if "public_menu_subdomain" in data and data.get("public_menu_subdomain"):
        sub = str(data["public_menu_subdomain"]).strip().lower()
        if sub in {"www"}:
            raise HTTPException(status_code=400, detail="Subdomínio inválido")
        exists = db.scalar(select(Branch).where(Branch.public_menu_subdomain == sub).where(Branch.id != b.id))
        if exists:
            raise HTTPException(status_code=400, detail="Subdomínio já está em uso")
        data["public_menu_subdomain"] = sub

    if "public_menu_custom_domain" in data and data.get("public_menu_custom_domain"):
        raw = str(data["public_menu_custom_domain"]).strip()
        parsed = urlparse(raw if "://" in raw else f"https://{raw}")
        dom = (parsed.netloc or parsed.path or "").strip().lower()
        if ":" in dom:
            dom = dom.split(":", 1)[0]
        dom = dom.strip("/ ")
        if not dom:
            raise HTTPException(status_code=400, detail="Domínio inválido")
        exists = db.scalar(select(Branch).where(Branch.public_menu_custom_domain == dom).where(Branch.id != b.id))
        if exists:
            raise HTTPException(status_code=400, detail="Domínio já está em uso")
        data["public_menu_custom_domain"] = dom
    for k, v in data.items():
        setattr(b, k, v)

    db.add(b)
    db.commit()
    db.refresh(b)
    return b

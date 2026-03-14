import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.deps import get_current_user
from app.models.branch import Branch
from app.models.company import Company
from app.models.user import User
from app.schemas.companies import CompanyCreate, CompanyOut, CompanyUpdate
from app.services.default_branches import get_default_branches
from app.settings import Settings

router = APIRouter()
settings = Settings()


@router.get("", response_model=list[CompanyOut])
@router.get("/", response_model=list[CompanyOut], include_in_schema=False)
def list_companies(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = db.scalars(select(Company).where(Company.id == current_user.company_id)).all()
    return rows


@router.post("", response_model=CompanyOut)
def create_company(payload: CompanyCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    company = Company(name=payload.name, owner_id=current_user.id)
    db.add(company)
    db.commit()
    db.refresh(company)

    existing_branches = db.scalars(select(Branch).where(Branch.company_id == company.id)).all()
    if not existing_branches:
        for name, bt in get_default_branches():
            db.add(Branch(company_id=company.id, name=name, business_type=bt, is_active=True))
        db.commit()
    return company


@router.post("/me/logo", response_model=CompanyOut)
@router.post("/me/logo/", response_model=CompanyOut, include_in_schema=False)
def upload_my_company_logo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = db.get(Company, current_user.company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    filename = file.filename or "logo"
    _, ext = os.path.splitext(filename)
    ext = (ext or "").lower()
    if ext not in {".png", ".jpg", ".jpeg", ".webp"}:
        raise HTTPException(status_code=400, detail="Formato inválido. Use PNG/JPG/WEBP")

    os.makedirs(settings.upload_dir, exist_ok=True)
    safe_name = f"company_{company.id}_logo_{uuid.uuid4().hex}{ext}"
    full_path = os.path.join(settings.upload_dir, safe_name)

    content = file.file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Arquivo vazio")
    with open(full_path, "wb") as f:
        f.write(content)

    company.logo_url = f"/uploads/{safe_name}"
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.put("/me", response_model=CompanyOut)
@router.put("/me/", response_model=CompanyOut, include_in_schema=False)
def update_my_company(
    payload: CompanyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = db.get(Company, current_user.company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(company, k, v)

    db.add(company)
    db.commit()
    db.refresh(company)
    return company

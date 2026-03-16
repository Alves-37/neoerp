import os
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.deps import get_current_user
from app.models.branch import Branch
from app.models.company import Company
from app.models.user import User
from app.schemas.companies import CompanyCreate, CompanyOut, CompanyUpdate
from app.services.default_branches import get_default_branches
from app.services.company_reset import run_company_reset
from app.settings import Settings

router = APIRouter()
settings = Settings()


class ResetCompanyRequest(BaseModel):
    confirm: str


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


@router.post("/me/reset")
def reset_my_company(
    payload: ResetCompanyRequest,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    role = (getattr(current_user, "role", "") or "").strip().lower()
    if role not in {"admin", "owner"}:
        raise HTTPException(status_code=403, detail="Apenas admin pode fazer reset")
    if (payload.confirm or "").strip().upper() != "RESET":
        raise HTTPException(status_code=400, detail="Confirmação inválida")

    row = db.execute(
        select(Company).where(Company.id == current_user.company_id)
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    existing = db.execute(
        text(
            """
            SELECT id, status
            FROM company_reset_jobs
            WHERE company_id = :cid
            ORDER BY id DESC
            LIMIT 1
            """
        ),
        {"cid": int(current_user.company_id)},
    ).mappings().first()
    if existing and str(existing.get("status") or "").lower() in {"pending", "running"}:
        raise HTTPException(status_code=409, detail="Já existe um reset em andamento")

    new_id = db.execute(
        text(
            """
            INSERT INTO company_reset_jobs (company_id, created_by, status, progress, message)
            VALUES (:cid, :uid, 'pending', 0, 'Aguardando')
            RETURNING id
            """
        ),
        {"cid": int(current_user.company_id), "uid": int(current_user.id)},
    ).scalar()
    db.commit()

    background.add_task(run_company_reset, int(new_id), int(current_user.company_id))
    return {"job_id": int(new_id), "status": "started"}


@router.get("/me/reset/status")
def reset_status(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    role = (getattr(current_user, "role", "") or "").strip().lower()
    if role not in {"admin", "owner"}:
        raise HTTPException(status_code=403, detail="Apenas admin")

    row = db.execute(
        text(
            """
            SELECT id, status, progress, message, error
            FROM company_reset_jobs
            WHERE company_id = :cid
            ORDER BY id DESC
            LIMIT 1
            """
        ),
        {"cid": int(current_user.company_id)},
    ).mappings().first()
    if not row:
        return {"status": "idle", "progress": 0}
    return {
        "job_id": int(row.get("id")),
        "status": row.get("status"),
        "progress": int(row.get("progress") or 0),
        "message": row.get("message"),
        "error": row.get("error"),
    }


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

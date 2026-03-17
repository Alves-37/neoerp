from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.deps import get_current_user
from app.models.branch import Branch
from app.models.printer import Printer, PrinterContract, PrinterCounterType, PrinterReading
from app.models.user import User
from app.schemas.printers import (
    PrinterContractCreate,
    PrinterContractOut,
    PrinterContractUpdate,
    PrinterCounterTypeCreate,
    PrinterCounterTypeOut,
    PrinterCounterTypeUpdate,
    PrinterCreate,
    PrinterOut,
    PrinterReadingCreate,
    PrinterReadingOut,
    PrinterUpdate,
)

router = APIRouter()


def _ensure_reprography_branch(db: Session, current_user: User) -> None:
    branch = db.get(Branch, int(current_user.branch_id))
    if not branch or branch.company_id != current_user.company_id:
        raise HTTPException(status_code=400, detail="Filial inválida")
    bt = (branch.business_type or "retail").strip().lower()
    if bt != "reprography":
        raise HTTPException(status_code=400, detail="Módulo disponível apenas para reprografia")


def _ensure_admin(current_user: User) -> None:
    role = (getattr(current_user, "role", "") or "").strip().lower()
    if role not in {"admin", "owner"}:
        raise HTTPException(status_code=403, detail="Sem permissão")


def _get_effective_establishment_id(*, current_user: User, establishment_id: int | None) -> int:
    role = (getattr(current_user, "role", "") or "").strip().lower()
    is_admin = role in {"admin", "owner"}

    if is_admin and establishment_id is not None:
        return int(establishment_id)

    if getattr(current_user, "establishment_id", None) is None:
        raise HTTPException(status_code=400, detail="Ponto inválido")

    return int(current_user.establishment_id)


@router.get("/", response_model=list[PrinterOut])
def list_printers(
    establishment_id: int | None = None,
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_reprography_branch(db, current_user)
    est_id = _get_effective_establishment_id(current_user=current_user, establishment_id=establishment_id)

    stmt = (
        select(Printer)
        .where(Printer.company_id == current_user.company_id)
        .where(Printer.branch_id == int(current_user.branch_id))
        .where(Printer.establishment_id == est_id)
    )
    if not include_inactive:
        stmt = stmt.where(Printer.is_active.is_(True))

    rows = db.scalars(stmt.order_by(Printer.serial_number.asc(), Printer.id.asc())).all()
    return rows


@router.post("/", response_model=PrinterOut)
def create_printer(
    payload: PrinterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_reprography_branch(db, current_user)
    _ensure_admin(current_user)

    serial = (payload.serial_number or "").strip()
    if not serial:
        raise HTTPException(status_code=400, detail="Número de série inválido")

    est_id = _get_effective_establishment_id(current_user=current_user, establishment_id=payload.establishment_id)

    row = Printer(
        company_id=current_user.company_id,
        branch_id=int(current_user.branch_id),
        establishment_id=est_id,
        serial_number=serial,
        brand=(payload.brand or "").strip() or None,
        model=(payload.model or "").strip() or None,
        is_active=bool(payload.is_active),
    )
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Já existe uma impressora com este número de série")
    db.refresh(row)
    return row


@router.put("/{printer_id}", response_model=PrinterOut)
def update_printer(
    printer_id: int,
    payload: PrinterUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_reprography_branch(db, current_user)
    _ensure_admin(current_user)

    row = db.get(Printer, int(printer_id))
    if not row or row.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Impressora não encontrada")

    data = payload.model_dump(exclude_unset=True)

    if "serial_number" in data and data["serial_number"] is not None:
        serial = (data["serial_number"] or "").strip()
        if not serial:
            raise HTTPException(status_code=400, detail="Número de série inválido")
        row.serial_number = serial

    if "brand" in data:
        row.brand = (data.get("brand") or "").strip() or None
    if "model" in data:
        row.model = (data.get("model") or "").strip() or None
    if "is_active" in data and data["is_active"] is not None:
        row.is_active = bool(data["is_active"])

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Já existe uma impressora com este número de série")
    db.refresh(row)
    return row


@router.delete("/{printer_id}")
def delete_printer(
    printer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_reprography_branch(db, current_user)
    _ensure_admin(current_user)

    row = db.get(Printer, int(printer_id))
    if not row or row.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Impressora não encontrada")

    db.delete(row)
    db.commit()
    return {"ok": True}


@router.get("/counter-types", response_model=list[PrinterCounterTypeOut])
def list_counter_types(
    establishment_id: int | None = None,
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_reprography_branch(db, current_user)
    est_id = _get_effective_establishment_id(current_user=current_user, establishment_id=establishment_id)

    stmt = (
        select(PrinterCounterType)
        .where(PrinterCounterType.company_id == current_user.company_id)
        .where(PrinterCounterType.branch_id == int(current_user.branch_id))
        .where(PrinterCounterType.establishment_id == est_id)
    )
    if not include_inactive:
        stmt = stmt.where(PrinterCounterType.is_active.is_(True))

    rows = db.scalars(stmt.order_by(PrinterCounterType.name.asc(), PrinterCounterType.id.asc())).all()
    return rows


@router.post("/counter-types", response_model=PrinterCounterTypeOut)
def create_counter_type(
    payload: PrinterCounterTypeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_reprography_branch(db, current_user)
    _ensure_admin(current_user)

    code = (payload.code or "").strip().upper()
    name = (payload.name or "").strip()
    if not code or not name:
        raise HTTPException(status_code=400, detail="Dados inválidos")

    est_id = _get_effective_establishment_id(current_user=current_user, establishment_id=payload.establishment_id)

    exists = db.scalar(
        select(PrinterCounterType)
        .where(PrinterCounterType.company_id == current_user.company_id)
        .where(PrinterCounterType.branch_id == int(current_user.branch_id))
        .where(PrinterCounterType.establishment_id == est_id)
        .where(func.upper(PrinterCounterType.code) == code)
    )
    if exists:
        return exists

    row = PrinterCounterType(
        company_id=current_user.company_id,
        branch_id=int(current_user.branch_id),
        establishment_id=est_id,
        code=code,
        name=name,
        is_active=bool(payload.is_active),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.put("/counter-types/{counter_type_id}", response_model=PrinterCounterTypeOut)
def update_counter_type(
    counter_type_id: int,
    payload: PrinterCounterTypeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_reprography_branch(db, current_user)
    _ensure_admin(current_user)

    row = db.get(PrinterCounterType, int(counter_type_id))
    if not row or row.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Tipo não encontrado")

    data = payload.model_dump(exclude_unset=True)

    if "code" in data and data["code"] is not None:
        code = (data["code"] or "").strip().upper()
        if not code:
            raise HTTPException(status_code=400, detail="Código inválido")
        dup = db.scalar(
            select(PrinterCounterType)
            .where(PrinterCounterType.company_id == current_user.company_id)
            .where(PrinterCounterType.branch_id == row.branch_id)
            .where(PrinterCounterType.establishment_id == row.establishment_id)
            .where(func.upper(PrinterCounterType.code) == code)
            .where(PrinterCounterType.id != row.id)
        )
        if dup:
            raise HTTPException(status_code=409, detail="Já existe um tipo com este código")
        row.code = code

    if "name" in data and data["name"] is not None:
        name = (data["name"] or "").strip()
        if not name:
            raise HTTPException(status_code=400, detail="Nome inválido")
        row.name = name

    if "is_active" in data and data["is_active"] is not None:
        row.is_active = bool(data["is_active"])

    db.commit()
    db.refresh(row)
    return row


@router.get("/contracts", response_model=list[PrinterContractOut])
def list_contracts(
    establishment_id: int | None = None,
    printer_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_reprography_branch(db, current_user)
    est_id = _get_effective_establishment_id(current_user=current_user, establishment_id=establishment_id)

    stmt = (
        select(PrinterContract)
        .where(PrinterContract.company_id == current_user.company_id)
        .where(PrinterContract.branch_id == int(current_user.branch_id))
        .where(PrinterContract.establishment_id == est_id)
    )
    if printer_id is not None:
        stmt = stmt.where(PrinterContract.printer_id == int(printer_id))

    rows = db.scalars(stmt.order_by(PrinterContract.id.desc())).all()
    return rows


@router.post("/contracts", response_model=PrinterContractOut)
def create_contract(
    payload: PrinterContractCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_reprography_branch(db, current_user)
    _ensure_admin(current_user)

    est_id = _get_effective_establishment_id(current_user=current_user, establishment_id=payload.establishment_id)

    printer = db.get(Printer, int(payload.printer_id))
    if not printer or printer.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Impressora não encontrada")
    if printer.branch_id != int(current_user.branch_id) or printer.establishment_id != est_id:
        raise HTTPException(status_code=400, detail="Impressora não pertence ao ponto")

    ctype = db.get(PrinterCounterType, int(payload.counter_type_id))
    if not ctype or ctype.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Tipo não encontrado")
    if ctype.branch_id != int(current_user.branch_id) or ctype.establishment_id != est_id:
        raise HTTPException(status_code=400, detail="Tipo não pertence ao ponto")

    row = db.scalar(
        select(PrinterContract)
        .where(PrinterContract.company_id == current_user.company_id)
        .where(PrinterContract.branch_id == int(current_user.branch_id))
        .where(PrinterContract.establishment_id == est_id)
        .where(PrinterContract.printer_id == int(payload.printer_id))
        .where(PrinterContract.counter_type_id == int(payload.counter_type_id))
    )
    if row:
        row.monthly_allowance = int(payload.monthly_allowance or 0)
        row.price_per_page = float(payload.price_per_page or 0)
        row.is_active = bool(payload.is_active)
        db.commit()
        db.refresh(row)
        return row

    row = PrinterContract(
        company_id=current_user.company_id,
        branch_id=int(current_user.branch_id),
        establishment_id=est_id,
        printer_id=int(payload.printer_id),
        counter_type_id=int(payload.counter_type_id),
        monthly_allowance=int(payload.monthly_allowance or 0),
        price_per_page=float(payload.price_per_page or 0),
        is_active=bool(payload.is_active),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.put("/contracts/{contract_id}", response_model=PrinterContractOut)
def update_contract(
    contract_id: int,
    payload: PrinterContractUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_reprography_branch(db, current_user)
    _ensure_admin(current_user)

    row = db.get(PrinterContract, int(contract_id))
    if not row or row.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Contrato não encontrado")

    data = payload.model_dump(exclude_unset=True)
    if "monthly_allowance" in data and data["monthly_allowance"] is not None:
        row.monthly_allowance = int(data["monthly_allowance"] or 0)
    if "price_per_page" in data and data["price_per_page"] is not None:
        row.price_per_page = float(data["price_per_page"] or 0)
    if "is_active" in data and data["is_active"] is not None:
        row.is_active = bool(data["is_active"])

    db.commit()
    db.refresh(row)
    return row


@router.get("/readings", response_model=list[PrinterReadingOut])
def list_readings(
    establishment_id: int | None = None,
    printer_id: int | None = None,
    counter_type_id: int | None = None,
    limit: int = 200,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_reprography_branch(db, current_user)
    est_id = _get_effective_establishment_id(current_user=current_user, establishment_id=establishment_id)

    stmt = (
        select(PrinterReading)
        .where(PrinterReading.company_id == current_user.company_id)
        .where(PrinterReading.branch_id == int(current_user.branch_id))
        .where(PrinterReading.establishment_id == est_id)
    )
    if printer_id is not None:
        stmt = stmt.where(PrinterReading.printer_id == int(printer_id))
    if counter_type_id is not None:
        stmt = stmt.where(PrinterReading.counter_type_id == int(counter_type_id))

    rows = db.scalars(
        stmt.order_by(PrinterReading.reading_date.desc(), PrinterReading.id.desc()).limit(int(limit or 200)).offset(int(offset or 0))
    ).all()
    return rows


@router.post("/readings", response_model=PrinterReadingOut)
def create_reading(
    payload: PrinterReadingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_reprography_branch(db, current_user)

    est_id = _get_effective_establishment_id(current_user=current_user, establishment_id=payload.establishment_id)

    printer = db.get(Printer, int(payload.printer_id))
    if not printer or printer.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Impressora não encontrada")
    if printer.branch_id != int(current_user.branch_id) or printer.establishment_id != est_id:
        raise HTTPException(status_code=400, detail="Impressora não pertence ao ponto")

    ctype = db.get(PrinterCounterType, int(payload.counter_type_id))
    if not ctype or ctype.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Tipo não encontrado")
    if ctype.branch_id != int(current_user.branch_id) or ctype.establishment_id != est_id:
        raise HTTPException(status_code=400, detail="Tipo não pertence ao ponto")

    if payload.counter_value < 0:
        raise HTTPException(status_code=400, detail="Contador inválido")

    # Validate monotonic counter
    last_counter = db.scalar(
        select(PrinterReading.counter_value)
        .where(PrinterReading.company_id == current_user.company_id)
        .where(PrinterReading.branch_id == int(current_user.branch_id))
        .where(PrinterReading.establishment_id == est_id)
        .where(PrinterReading.printer_id == int(payload.printer_id))
        .where(PrinterReading.counter_type_id == int(payload.counter_type_id))
        .order_by(PrinterReading.reading_date.desc(), PrinterReading.id.desc())
        .limit(1)
    )
    if last_counter is not None and int(payload.counter_value) < int(last_counter):
        raise HTTPException(status_code=400, detail="Contador atual não pode ser menor que o anterior")

    row = PrinterReading(
        company_id=current_user.company_id,
        branch_id=int(current_user.branch_id),
        establishment_id=est_id,
        printer_id=int(payload.printer_id),
        counter_type_id=int(payload.counter_type_id),
        reading_date=payload.reading_date,
        counter_value=int(payload.counter_value),
    )
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Já existe uma leitura para este dia")

    db.refresh(row)
    return row

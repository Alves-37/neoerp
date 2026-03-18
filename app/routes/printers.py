from __future__ import annotations

from calendar import monthrange
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.deps import get_current_user
from app.models.branch import Branch
from app.models.cash_session import CashSession
from app.models.printer import Printer, PrinterBillingRegistry, PrinterContract, PrinterCounterType, PrinterReading
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.product_stock import ProductStock
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.stock_location import StockLocation
from app.models.user import User
from app.schemas.printers import (
    PrinterBillingGenerateLaunchOut,
    PrinterBillingGenerateLaunchPayload,
    PrinterBillingLineOut,
    PrinterBillingOut,
    PrinterBillingPrinterOut,
    PrinterContractCreate,
    PrinterContractOut,
    PrinterContractUpdate,
    PrinterCounterTypeCreate,
    PrinterCounterTypeOut,
    PrinterCounterTypeUpdate,
    PrinterCreate,
    PrinterOut,
    PrinterPdv3BillingOut,
    PrinterPdv3BillingRowOut,
    PrinterPdv3GenerateLaunchOut,
    PrinterPdv3GenerateLaunchPayload,
    PrinterPdv3ReadingCreate,
    PrinterReadingCreate,
    PrinterReadingOut,
    PrinterUpdate,
)

router = APIRouter()


def _month_window(year: int, month: int) -> tuple[datetime, datetime]:
    if year < 2000 or year > 2100:
        raise HTTPException(status_code=400, detail="Ano inválido")
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Mês inválido")
    start = datetime(year, month, 1, tzinfo=timezone.utc)
    last_day = monthrange(year, month)[1]
    end = datetime(year, month, last_day, 23, 59, 59, 999999, tzinfo=timezone.utc)
    return start, end


def _get_default_location_id(db: Session, *, company_id: int, branch_id: int) -> int:
    loc = db.scalar(
        select(StockLocation)
        .where(StockLocation.company_id == company_id)
        .where(StockLocation.branch_id == int(branch_id))
        .where(StockLocation.is_active.is_(True))
        .order_by(StockLocation.is_default.desc(), StockLocation.id.asc())
        .limit(1)
    )
    if not loc:
        raise HTTPException(status_code=400, detail="Sem local de stock para a filial")
    return int(loc.id)


def _get_or_create_excess_service_product(
    db: Session,
    *,
    company_id: int,
    branch_id: int,
    establishment_id: int,
    business_type: str,
    counter_type: PrinterCounterType,
) -> Product:
    code = (counter_type.code or '').strip().upper()
    name = (counter_type.name or '').strip() or code
    product_name = f"Excedente Impressão - {name}"

    existing = db.scalar(
        select(Product)
        .where(Product.company_id == company_id)
        .where(Product.branch_id == int(branch_id))
        .where(Product.establishment_id == int(establishment_id))
        .where(func.lower(Product.name) == product_name.lower())
        .where(Product.is_service.is_(True))
        .limit(1)
    )
    if existing:
        return existing

    default_location_id = _get_default_location_id(db, company_id=company_id, branch_id=branch_id)
    row = Product(
        company_id=company_id,
        branch_id=int(branch_id),
        establishment_id=int(establishment_id),
        category_id=None,
        supplier_id=None,
        default_location_id=int(default_location_id),
        business_type=business_type,
        name=product_name,
        sku=None,
        barcode=None,
        unit="un",
        price=0,
        cost=0,
        tax_rate=0,
        min_stock=0,
        track_stock=False,
        is_service=True,
        is_active=True,
        show_in_menu=False,
        attributes={},
    )
    db.add(row)
    db.flush()
    db.refresh(row)
    return row


def _get_or_create_pdv3_total_counter_type(
    db: Session,
    *,
    current_user: User,
    establishment_id: int,
) -> PrinterCounterType:
    # PDV3 uses a single counter. We emulate it with a fixed counter type.
    row = db.scalar(
        select(PrinterCounterType)
        .where(PrinterCounterType.company_id == current_user.company_id)
        .where(PrinterCounterType.branch_id == int(current_user.branch_id))
        .where(PrinterCounterType.establishment_id == int(establishment_id))
        .where(func.upper(PrinterCounterType.code) == 'TOTAL')
        .limit(1)
    )
    if row:
        return row

    row = PrinterCounterType(
        company_id=current_user.company_id,
        branch_id=int(current_user.branch_id),
        establishment_id=int(establishment_id),
        code='TOTAL',
        name='Total',
        is_active=True,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _get_or_create_pdv3_print_service_product(
    db: Session,
    *,
    company_id: int,
    branch_id: int,
    establishment_id: int,
    business_type: str,
) -> Product:
    # PDV3 uses a single service product: SERVICO_IMPRESSAO
    # In PDV3, services are grouped under category "Serviços".
    category = db.scalar(
        select(ProductCategory)
        .where(ProductCategory.company_id == int(company_id))
        .where(ProductCategory.business_type == (business_type or "reprography"))
        .where(func.lower(func.coalesce(ProductCategory.name, "")) == "serviços")
        .limit(1)
    )
    if not category:
        category = ProductCategory(
            company_id=int(company_id),
            business_type=(business_type or "reprography"),
            name="Serviços",
        )
        db.add(category)
        db.commit()
        db.refresh(category)

    existing = db.scalar(
        select(Product)
        .where(Product.company_id == company_id)
        .where(Product.branch_id == int(branch_id))
        .where(Product.establishment_id == int(establishment_id))
        .where(func.upper(func.coalesce(Product.sku, '')) == 'SERVICO_IMPRESSAO')
        .where(Product.is_service.is_(True))
        .limit(1)
    )
    if existing:
        return existing

    default_location_id = _get_default_location_id(db, company_id=company_id, branch_id=branch_id)
    row = Product(
        company_id=company_id,
        branch_id=int(branch_id),
        establishment_id=int(establishment_id),
        category_id=int(category.id),
        supplier_id=None,
        default_location_id=int(default_location_id),
        business_type=business_type,
        name='Serviço de Impressão',
        sku='SERVICO_IMPRESSAO',
        barcode=None,
        unit='serv',
        price=0,
        cost=0,
        tax_rate=0,
        min_stock=0,
        track_stock=False,
        is_service=True,
        is_active=True,
        show_in_menu=False,
        attributes={},
    )
    db.add(row)
    db.flush()
    db.refresh(row)
    return row


def _compute_monthly_billing(
    db: Session,
    *,
    current_user: User,
    establishment_id: int,
    year: int,
    month: int,
) -> PrinterBillingOut:
    start_dt, end_dt = _month_window(year, month)
    branch_id = int(current_user.branch_id)

    total_counter_type = _get_or_create_pdv3_total_counter_type(
        db,
        current_user=current_user,
        establishment_id=int(establishment_id),
    )

    printers = db.scalars(
        select(Printer)
        .where(Printer.company_id == current_user.company_id)
        .where(Printer.branch_id == branch_id)
        .where(Printer.establishment_id == int(establishment_id))
        .order_by(Printer.serial_number.asc(), Printer.id.asc())
    ).all()
    printers_by_id = {int(p.id): p for p in printers}

    ctypes = db.scalars(
        select(PrinterCounterType)
        .where(PrinterCounterType.company_id == current_user.company_id)
        .where(PrinterCounterType.branch_id == branch_id)
        .where(PrinterCounterType.establishment_id == int(establishment_id))
        .order_by(PrinterCounterType.name.asc(), PrinterCounterType.id.asc())
    ).all()
    ctype_by_id = {int(c.id): c for c in ctypes}

    contracts = db.scalars(
        select(PrinterContract)
        .where(PrinterContract.company_id == current_user.company_id)
        .where(PrinterContract.branch_id == branch_id)
        .where(PrinterContract.establishment_id == int(establishment_id))
        .where(PrinterContract.is_active.is_(True))
        .order_by(PrinterContract.id.asc())
    ).all()

    per_printer: dict[int, PrinterBillingPrinterOut] = {}
    total_pages = 0
    total_amount = 0.0

    for c in contracts:
        pid = int(c.printer_id)
        tid = int(c.counter_type_id)
        printer = printers_by_id.get(pid)
        ctype = ctype_by_id.get(tid)
        if not printer or not ctype:
            continue

        start_row = db.scalar(
            select(PrinterReading)
            .where(PrinterReading.company_id == current_user.company_id)
            .where(PrinterReading.branch_id == branch_id)
            .where(PrinterReading.establishment_id == int(establishment_id))
            .where(PrinterReading.printer_id == pid)
            .where(PrinterReading.counter_type_id == tid)
            .where(PrinterReading.reading_date < start_dt)
            .order_by(PrinterReading.reading_date.desc(), PrinterReading.id.desc())
            .limit(1)
        )

        end_row = db.scalar(
            select(PrinterReading)
            .where(PrinterReading.company_id == current_user.company_id)
            .where(PrinterReading.branch_id == branch_id)
            .where(PrinterReading.establishment_id == int(establishment_id))
            .where(PrinterReading.printer_id == pid)
            .where(PrinterReading.counter_type_id == tid)
            .where(PrinterReading.reading_date <= end_dt)
            .order_by(PrinterReading.reading_date.desc(), PrinterReading.id.desc())
            .limit(1)
        )

        pages_used = 0
        if start_row and end_row:
            pages_used = max(0, int(end_row.counter_value) - int(start_row.counter_value))
        elif end_row:
            # No reading before the month; try to use first reading inside the month as start.
            first_in_month = db.scalar(
                select(PrinterReading)
                .where(PrinterReading.company_id == current_user.company_id)
                .where(PrinterReading.branch_id == branch_id)
                .where(PrinterReading.establishment_id == int(establishment_id))
                .where(PrinterReading.printer_id == pid)
                .where(PrinterReading.counter_type_id == tid)
                .where(PrinterReading.reading_date >= start_dt)
                .where(PrinterReading.reading_date <= end_dt)
                .order_by(PrinterReading.reading_date.asc(), PrinterReading.id.asc())
                .limit(1)
            )
            if first_in_month and int(end_row.id) != int(first_in_month.id):
                pages_used = max(0, int(end_row.counter_value) - int(first_in_month.counter_value))
                start_row = first_in_month

        allowance = int(c.monthly_allowance or 0)
        excess_pages = max(0, int(pages_used) - allowance)
        price = float(c.price_per_page or 0)
        excess_total = round(float(excess_pages) * price, 2)

        line = PrinterBillingLineOut(
            printer_id=pid,
            counter_type_id=tid,
            counter_type_code=ctype.code,
            counter_type_name=ctype.name,
            start_reading_date=(start_row.reading_date if start_row else None),
            start_counter_value=(int(start_row.counter_value) if start_row else None),
            end_reading_date=(end_row.reading_date if end_row else None),
            end_counter_value=(int(end_row.counter_value) if end_row else None),
            pages_used=int(pages_used),
            monthly_allowance=allowance,
            excess_pages=int(excess_pages),
            price_per_page=float(price),
            excess_total=float(excess_total),
        )

        bucket = per_printer.get(pid)
        if not bucket:
            bucket = PrinterBillingPrinterOut(
                printer_id=pid,
                serial_number=printer.serial_number,
                brand=printer.brand,
                model=printer.model,
                lines=[],
                total_excess_pages=0,
                total_excess_amount=0,
            )
            per_printer[pid] = bucket

        bucket.lines.append(line)
        bucket.total_excess_pages = int(bucket.total_excess_pages) + int(excess_pages)
        bucket.total_excess_amount = round(float(bucket.total_excess_amount) + float(excess_total), 2)

        total_pages += int(excess_pages)
        total_amount = round(float(total_amount) + float(excess_total), 2)

    printers_out = list(per_printer.values())
    printers_out.sort(key=lambda x: (x.serial_number or "", x.printer_id))

    return PrinterBillingOut(
        year=int(year),
        month=int(month),
        company_id=int(current_user.company_id),
        branch_id=branch_id,
        establishment_id=int(establishment_id),
        printers=printers_out,
        total_excess_pages=int(total_pages),
        total_excess_amount=float(total_amount),
    )


def _ensure_reprography_branch(db: Session, current_user: User) -> None:
    branch = db.get(Branch, int(current_user.branch_id))
    if not branch or branch.company_id != current_user.company_id:
        raise HTTPException(status_code=400, detail="Filial inválida")
    bt = (branch.business_type or "retail").strip().lower()
    if bt == "reprografia":
        bt = "reprography"
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

    serial = (payload.serial_number or "").strip().upper()
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
        initial_counter=int(getattr(payload, "initial_counter", 0) or 0),
        installation_date=payload.installation_date or datetime.utcnow().date(),
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


@router.put("/readings/{reading_id}", response_model=PrinterReadingOut)
def update_reading(
    reading_id: int,
    payload: PrinterReadingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_reprography_branch(db, current_user)
    _ensure_admin(current_user)

    row = db.get(PrinterReading, int(reading_id))
    if not row or row.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Leitura não encontrada")

    est_id = _get_effective_establishment_id(current_user=current_user, establishment_id=payload.establishment_id)

    if row.branch_id != int(current_user.branch_id) or row.establishment_id != est_id:
        raise HTTPException(status_code=400, detail="Leitura não pertence ao ponto")

    if payload.counter_value < 0:
        raise HTTPException(status_code=400, detail="Contador inválido")

    # Validate monotonic counter against nearest readings excluding current row
    prev_counter = db.scalar(
        select(PrinterReading.counter_value)
        .where(PrinterReading.company_id == current_user.company_id)
        .where(PrinterReading.branch_id == int(current_user.branch_id))
        .where(PrinterReading.establishment_id == est_id)
        .where(PrinterReading.printer_id == int(payload.printer_id))
        .where(PrinterReading.counter_type_id == int(payload.counter_type_id))
        .where(PrinterReading.reading_date < payload.reading_date)
        .where(PrinterReading.id != row.id)
        .order_by(PrinterReading.reading_date.desc(), PrinterReading.id.desc())
        .limit(1)
    )
    if prev_counter is not None and int(payload.counter_value) < int(prev_counter):
        raise HTTPException(status_code=400, detail="Contador atual não pode ser menor que o anterior")

    next_counter = db.scalar(
        select(PrinterReading.counter_value)
        .where(PrinterReading.company_id == current_user.company_id)
        .where(PrinterReading.branch_id == int(current_user.branch_id))
        .where(PrinterReading.establishment_id == est_id)
        .where(PrinterReading.printer_id == int(payload.printer_id))
        .where(PrinterReading.counter_type_id == int(payload.counter_type_id))
        .where(PrinterReading.reading_date > payload.reading_date)
        .where(PrinterReading.id != row.id)
        .order_by(PrinterReading.reading_date.asc(), PrinterReading.id.asc())
        .limit(1)
    )
    if next_counter is not None and int(payload.counter_value) > int(next_counter):
        raise HTTPException(status_code=400, detail="Contador atual não pode ser maior que o próximo")

    row.printer_id = int(payload.printer_id)
    row.counter_type_id = int(payload.counter_type_id)
    row.reading_date = payload.reading_date
    row.counter_value = int(payload.counter_value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Já existe uma leitura para este dia")

    db.refresh(row)
    return row


@router.delete("/readings/{reading_id}")
def delete_reading(
    reading_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_reprography_branch(db, current_user)
    _ensure_admin(current_user)

    row = db.get(PrinterReading, int(reading_id))
    if not row or row.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Leitura não encontrada")

    db.delete(row)
    db.commit()
    return {"ok": True}


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
        serial = (data["serial_number"] or "").strip().upper()
        if not serial:
            raise HTTPException(status_code=400, detail="Número de série inválido")
        row.serial_number = serial

    if "brand" in data:
        row.brand = (data.get("brand") or "").strip() or None
    if "model" in data:
        row.model = (data.get("model") or "").strip() or None
    if "initial_counter" in data and data["initial_counter"] is not None:
        row.initial_counter = int(data["initial_counter"] or 0)
    if "installation_date" in data and data["installation_date"] is not None:
        row.installation_date = data["installation_date"]
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

    # PDV3 behavior: do not delete; just inactivate
    row.is_active = False
    db.add(row)
    db.commit()
    return {"ok": True}


def _pdv3_month_label(year: int, month: int) -> str:
    return f"{str(int(month)).zfill(2)}/{int(year)}"


def _pdv3_compute_monthly_copies(
    db: Session,
    *,
    current_user: User,
    establishment_id: int,
    year: int,
    month: int,
) -> list[PrinterPdv3BillingRowOut]:
    start_dt, end_dt = _month_window(year, month)
    branch_id = int(current_user.branch_id)

    total_counter_type = _get_or_create_pdv3_total_counter_type(
        db,
        current_user=current_user,
        establishment_id=int(establishment_id),
    )

    printers = db.scalars(
        select(Printer)
        .where(Printer.company_id == current_user.company_id)
        .where(Printer.branch_id == branch_id)
        .where(Printer.establishment_id == int(establishment_id))
        .where(Printer.is_active.is_(True))
        .order_by(Printer.serial_number.asc(), Printer.id.asc())
    ).all()

    month_year = _pdv3_month_label(year, month)

    # Load registry in one query
    reg_rows = db.scalars(
        select(PrinterBillingRegistry)
        .where(PrinterBillingRegistry.company_id == current_user.company_id)
        .where(PrinterBillingRegistry.branch_id == branch_id)
        .where(PrinterBillingRegistry.establishment_id == int(establishment_id))
        .where(PrinterBillingRegistry.year == int(year))
        .where(PrinterBillingRegistry.month == int(month))
    ).all()
    billed_to_by_printer = {int(r.printer_id): int(r.copies_to or 0) for r in reg_rows}

    out: list[PrinterPdv3BillingRowOut] = []
    for p in printers:
        pid = int(p.id)

        start_reading = db.scalar(
            select(PrinterReading)
            .where(PrinterReading.company_id == current_user.company_id)
            .where(PrinterReading.branch_id == branch_id)
            .where(PrinterReading.establishment_id == int(establishment_id))
            .where(PrinterReading.printer_id == pid)
            .where(PrinterReading.counter_type_id == int(total_counter_type.id))
            .where(PrinterReading.reading_date < start_dt)
            .order_by(PrinterReading.reading_date.desc(), PrinterReading.id.desc())
            .limit(1)
        )
        start_value = int(start_reading.counter_value) if start_reading else int(getattr(p, 'initial_counter', 0) or 0)

        end_reading = db.scalar(
            select(PrinterReading)
            .where(PrinterReading.company_id == current_user.company_id)
            .where(PrinterReading.branch_id == branch_id)
            .where(PrinterReading.establishment_id == int(establishment_id))
            .where(PrinterReading.printer_id == pid)
            .where(PrinterReading.counter_type_id == int(total_counter_type.id))
            .where(PrinterReading.reading_date <= end_dt)
            .order_by(PrinterReading.reading_date.desc(), PrinterReading.id.desc())
            .limit(1)
        )
        end_value = int(end_reading.counter_value) if end_reading else int(start_value)

        copies_total = max(0, int(end_value) - int(start_value))
        billed_to = int(billed_to_by_printer.get(pid, 0) or 0)
        copies_new = max(0, int(copies_total) - int(billed_to))

        out.append(
            PrinterPdv3BillingRowOut(
                printer_id=pid,
                serial_number=p.serial_number,
                brand=p.brand,
                model=p.model,
                month=int(month),
                year=int(year),
                month_year=month_year,
                copies_total=int(copies_total),
                copies_billed_to=int(billed_to),
                copies_new=int(copies_new),
                has_launch=bool(copies_new <= 0 and copies_total > 0),
            )
        )

    return out


@router.get("/pdv3/billing", response_model=PrinterPdv3BillingOut)
def get_pdv3_monthly_billing(
    year: int,
    month: int,
    establishment_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_reprography_branch(db, current_user)
    est_id = _get_effective_establishment_id(current_user=current_user, establishment_id=establishment_id)

    rows = _pdv3_compute_monthly_copies(db, current_user=current_user, establishment_id=est_id, year=int(year), month=int(month))
    total_copies = sum(int(r.copies_total or 0) for r in rows)

    return PrinterPdv3BillingOut(
        month=int(month),
        year=int(year),
        company_id=int(current_user.company_id),
        branch_id=int(current_user.branch_id),
        establishment_id=int(est_id),
        rows=rows,
        total_copies=int(total_copies),
        total_printers=int(len(rows)),
    )


@router.post("/pdv3/billing/generate-launch", response_model=PrinterPdv3GenerateLaunchOut)
def generate_pdv3_billing_launch(
    payload: PrinterPdv3GenerateLaunchPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_reprography_branch(db, current_user)

    est_id = _get_effective_establishment_id(current_user=current_user, establishment_id=payload.establishment_id)

    # Ensure cash session open (ERP invariant)
    cash_session = db.scalar(
        select(CashSession)
        .where(CashSession.company_id == current_user.company_id)
        .where(CashSession.branch_id == int(current_user.branch_id))
        .where(CashSession.establishment_id == int(est_id))
        .where(CashSession.opened_by == current_user.id)
        .where(CashSession.status == "open")
        .order_by(CashSession.id.desc())
        .limit(1)
    )
    if not cash_session:
        raise HTTPException(status_code=409, detail="Caixa fechado. Abra o caixa para gerar o lançamento")

    # Compute copies for this printer
    computed = _pdv3_compute_monthly_copies(
        db,
        current_user=current_user,
        establishment_id=int(est_id),
        year=int(payload.year),
        month=int(payload.month),
    )
    row = next((r for r in computed if int(r.printer_id) == int(payload.printer_id)), None)
    if not row:
        raise HTTPException(status_code=404, detail="Impressora não encontrada")

    if int(row.copies_new or 0) <= 0:
        raise HTTPException(status_code=400, detail="Nada novo para faturar")

    price = float(payload.price_per_copy or 0)
    cost = float(payload.cost_per_copy or 0)
    if price < 0 or cost < 0:
        raise HTTPException(status_code=400, detail="Valores inválidos")

    total = round(float(row.copies_new) * price, 2)
    cost_total = round(float(row.copies_new) * cost, 2)

    branch = db.get(Branch, int(current_user.branch_id))
    business_type = (branch.business_type or "reprography").strip().lower() if branch else "reprography"
    if business_type == "reprografia":
        business_type = "reprography"

    product = _get_or_create_pdv3_print_service_product(
        db,
        company_id=current_user.company_id,
        branch_id=int(current_user.branch_id),
        establishment_id=int(est_id),
        business_type=business_type,
    )

    sale = Sale(
        company_id=current_user.company_id,
        branch_id=int(current_user.branch_id),
        establishment_id=int(est_id),
        cashier_id=current_user.id,
        cash_session_id=int(cash_session.id),
        business_type=business_type,
        total=float(total),
        net_total=float(total),
        tax_total=0.0,
        include_tax=False,
        paid=float(total),
        change=0.0,
        payment_method="internal",
        status="paid",
        sale_channel="counter",
        table_number=None,
        seat_number=None,
        created_at=datetime.utcnow(),
    )
    db.add(sale)
    db.flush()

    db.add(
        SaleItem(
            company_id=current_user.company_id,
            branch_id=int(current_user.branch_id),
            sale_id=int(sale.id),
            product_id=int(product.id),
            qty=1.0,
            price_at_sale=float(total),
            cost_at_sale=float(cost_total),
            line_total=float(total),
        )
    )

    # Upsert registry
    reg = db.scalar(
        select(PrinterBillingRegistry)
        .where(PrinterBillingRegistry.company_id == current_user.company_id)
        .where(PrinterBillingRegistry.branch_id == int(current_user.branch_id))
        .where(PrinterBillingRegistry.establishment_id == int(est_id))
        .where(PrinterBillingRegistry.printer_id == int(payload.printer_id))
        .where(PrinterBillingRegistry.year == int(payload.year))
        .where(PrinterBillingRegistry.month == int(payload.month))
        .limit(1)
    )
    new_copies_to = int(row.copies_billed_to or 0) + int(row.copies_new or 0)
    if reg:
        reg.copies_to = int(new_copies_to)
        db.add(reg)
    else:
        db.add(
            PrinterBillingRegistry(
                company_id=current_user.company_id,
                branch_id=int(current_user.branch_id),
                establishment_id=int(est_id),
                printer_id=int(payload.printer_id),
                year=int(payload.year),
                month=int(payload.month),
                copies_to=int(new_copies_to),
            )
        )

    db.commit()
    db.refresh(sale)

    return PrinterPdv3GenerateLaunchOut(
        ok=True,
        sale_id=int(sale.id),
        total=float(total),
        copies_new=int(row.copies_new or 0),
        copies_billed_to=int(new_copies_to),
    )


@router.get("/pdv3/readings", response_model=list[PrinterReadingOut])
def list_pdv3_readings(
    establishment_id: int | None = None,
    printer_id: int | None = None,
    limit: int = 200,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_reprography_branch(db, current_user)
    est_id = _get_effective_establishment_id(current_user=current_user, establishment_id=establishment_id)

    total_counter_type = _get_or_create_pdv3_total_counter_type(
        db,
        current_user=current_user,
        establishment_id=int(est_id),
    )

    stmt = (
        select(PrinterReading)
        .where(PrinterReading.company_id == current_user.company_id)
        .where(PrinterReading.branch_id == int(current_user.branch_id))
        .where(PrinterReading.establishment_id == int(est_id))
        .where(PrinterReading.counter_type_id == int(total_counter_type.id))
    )
    if printer_id is not None:
        stmt = stmt.where(PrinterReading.printer_id == int(printer_id))

    rows = db.scalars(
        stmt.order_by(PrinterReading.reading_date.desc(), PrinterReading.id.desc()).limit(int(limit or 200)).offset(int(offset or 0))
    ).all()
    return rows


@router.post("/pdv3/readings", response_model=PrinterReadingOut)
def create_pdv3_reading(
    payload: PrinterPdv3ReadingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_reprography_branch(db, current_user)

    est_id = _get_effective_establishment_id(current_user=current_user, establishment_id=payload.establishment_id)
    total_counter_type = _get_or_create_pdv3_total_counter_type(
        db,
        current_user=current_user,
        establishment_id=int(est_id),
    )

    # Reuse existing create_reading validations by calling logic inline
    printer = db.get(Printer, int(payload.printer_id))
    if not printer or printer.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Impressora não encontrada")
    if printer.branch_id != int(current_user.branch_id) or printer.establishment_id != est_id:
        raise HTTPException(status_code=400, detail="Impressora não pertence ao ponto")

    if payload.counter_value < 0:
        raise HTTPException(status_code=400, detail="Contador inválido")

    last_counter = db.scalar(
        select(PrinterReading.counter_value)
        .where(PrinterReading.company_id == current_user.company_id)
        .where(PrinterReading.branch_id == int(current_user.branch_id))
        .where(PrinterReading.establishment_id == est_id)
        .where(PrinterReading.printer_id == int(payload.printer_id))
        .where(PrinterReading.counter_type_id == int(total_counter_type.id))
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
        counter_type_id=int(total_counter_type.id),
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


@router.get("/billing", response_model=PrinterBillingOut)
def get_monthly_billing(
    year: int,
    month: int,
    establishment_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_reprography_branch(db, current_user)
    est_id = _get_effective_establishment_id(current_user=current_user, establishment_id=establishment_id)
    return _compute_monthly_billing(db, current_user=current_user, establishment_id=est_id, year=int(year), month=int(month))


@router.post("/billing/generate-launch", response_model=PrinterBillingGenerateLaunchOut)
def generate_billing_launch(
    payload: PrinterBillingGenerateLaunchPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_reprography_branch(db, current_user)
    _ensure_admin(current_user)

    est_id = _get_effective_establishment_id(current_user=current_user, establishment_id=payload.establishment_id)
    bill = _compute_monthly_billing(db, current_user=current_user, establishment_id=est_id, year=int(payload.year), month=int(payload.month))

    if not getattr(current_user, "establishment_id", None) and est_id is None:
        raise HTTPException(status_code=400, detail="Ponto inválido")

    branch = db.get(Branch, int(current_user.branch_id))
    if not branch or branch.company_id != current_user.company_id:
        raise HTTPException(status_code=400, detail="Filial inválida")
    business_type = (branch.business_type or "reprography").strip().lower()
    if business_type == "reprografia":
        business_type = "reprography"

    cash_session = db.scalar(
        select(CashSession)
        .where(CashSession.company_id == current_user.company_id)
        .where(CashSession.branch_id == int(current_user.branch_id))
        .where(CashSession.establishment_id == int(est_id))
        .where(CashSession.opened_by == current_user.id)
        .where(CashSession.status == "open")
        .order_by(CashSession.id.desc())
        .limit(1)
    )
    if not cash_session:
        raise HTTPException(status_code=409, detail="Caixa fechado. Abra o caixa para gerar o lançamento")

    # Build sale items from billing lines (only excess)
    contracts_by_key: dict[tuple[int, int], PrinterContract] = {
        (int(c.printer_id), int(c.counter_type_id)): c
        for c in db.scalars(
            select(PrinterContract)
            .where(PrinterContract.company_id == current_user.company_id)
            .where(PrinterContract.branch_id == int(current_user.branch_id))
            .where(PrinterContract.establishment_id == int(est_id))
            .where(PrinterContract.is_active.is_(True))
        ).all()
    }

    ctype_by_id: dict[int, PrinterCounterType] = {
        int(c.id): c
        for c in db.scalars(
            select(PrinterCounterType)
            .where(PrinterCounterType.company_id == current_user.company_id)
            .where(PrinterCounterType.branch_id == int(current_user.branch_id))
            .where(PrinterCounterType.establishment_id == int(est_id))
        ).all()
    }

    items: list[SaleItem] = []
    net_total = 0.0

    for p in bill.printers:
        for ln in p.lines:
            if not payload.include_zero and int(ln.excess_pages or 0) <= 0:
                continue
            ctype = ctype_by_id.get(int(ln.counter_type_id))
            if not ctype:
                continue
            contract = contracts_by_key.get((int(ln.printer_id), int(ln.counter_type_id)))
            price = float(contract.price_per_page or 0) if contract else float(ln.price_per_page or 0)
            qty = int(ln.excess_pages or 0)
            line_total = round(float(qty) * float(price), 2)
            if not payload.include_zero and line_total <= 0:
                continue

            prod = _get_or_create_excess_service_product(
                db,
                company_id=current_user.company_id,
                branch_id=int(current_user.branch_id),
                establishment_id=int(est_id),
                business_type=business_type,
                counter_type=ctype,
            )

            items.append(
                SaleItem(
                    company_id=current_user.company_id,
                    branch_id=int(current_user.branch_id),
                    sale_id=0,
                    product_id=int(prod.id),
                    qty=float(qty),
                    price_at_sale=float(price),
                    cost_at_sale=0.0,
                    line_total=float(line_total),
                )
            )
            net_total = round(float(net_total) + float(line_total), 2)

    if not items:
        raise HTTPException(status_code=400, detail="Sem excedentes para lançar")

    sale = Sale(
        company_id=current_user.company_id,
        branch_id=int(current_user.branch_id),
        establishment_id=int(est_id),
        cashier_id=current_user.id,
        cash_session_id=int(cash_session.id),
        business_type=business_type,
        total=float(net_total),
        net_total=float(net_total),
        tax_total=0.0,
        include_tax=False,
        paid=float(net_total),
        change=0.0,
        payment_method="internal",
        status="paid",
        sale_channel="counter",
        table_number=None,
        seat_number=None,
        created_at=datetime.utcnow(),
    )

    db.add(sale)
    db.flush()
    for it in items:
        it.sale_id = int(sale.id)
        db.add(it)
    db.commit()
    db.refresh(sale)

    return PrinterBillingGenerateLaunchOut(ok=True, sale_id=int(sale.id), total=float(sale.total))


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


@router.delete("/contracts/{contract_id}")
def delete_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_reprography_branch(db, current_user)
    _ensure_admin(current_user)

    row = db.get(PrinterContract, int(contract_id))
    if not row or row.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Contrato não encontrado")

    db.delete(row)
    db.commit()
    return {"ok": True}


@router.delete("/counter-types/{counter_type_id}")
def delete_counter_type(
    counter_type_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_reprography_branch(db, current_user)
    _ensure_admin(current_user)

    row = db.get(PrinterCounterType, int(counter_type_id))
    if not row or row.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Tipo não encontrado")

    in_contract = db.scalar(
        select(PrinterContract.id)
        .where(PrinterContract.company_id == current_user.company_id)
        .where(PrinterContract.counter_type_id == row.id)
        .limit(1)
    )
    if in_contract:
        raise HTTPException(status_code=409, detail="Tipo possui contratos")

    in_reading = db.scalar(
        select(PrinterReading.id)
        .where(PrinterReading.company_id == current_user.company_id)
        .where(PrinterReading.counter_type_id == row.id)
        .limit(1)
    )
    if in_reading:
        raise HTTPException(status_code=409, detail="Tipo possui leituras")

    db.delete(row)
    db.commit()
    return {"ok": True}


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

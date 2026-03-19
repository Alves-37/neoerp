from datetime import date

from fastapi import APIRouter, Depends, Response
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.deps import get_current_user
from app.models.company import Company
from app.models.fiscal_document import FiscalDocument
from app.models.fiscal_document_line import FiscalDocumentLine
from app.models.printer import Printer, PrinterCounterType, PrinterSaleLine
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.user import User
from app.utils.pdf import (
    cash_closure_pdf_elements,
    daily_z_pdf_elements,
    render_pdf,
    sales_by_period_pdf_elements,
    vat_by_rate_pdf_elements,
)

router = APIRouter()


def _doc_local_day_expr():
    # Mozambique local day based on Africa/Maputo
    return func.date(func.timezone("Africa/Maputo", FiscalDocument.issued_at))


@router.get("/daily-z")
def daily_z_report(
    day: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    local_day = _doc_local_day_expr()

    effective_establishment_id: int | None = None
    if getattr(current_user, "establishment_id", None) is not None:
        effective_establishment_id = int(current_user.establishment_id)

    base_where = [
        FiscalDocument.company_id == current_user.company_id,
        FiscalDocument.branch_id == int(current_user.branch_id),
        local_day == day,
    ]

    totals_stmt = (
        select(
            func.coalesce(func.sum(FiscalDocument.net_total), 0).label("net_total"),
            func.coalesce(func.sum(FiscalDocument.tax_total), 0).label("tax_total"),
            func.coalesce(func.sum(FiscalDocument.gross_total), 0).label("gross_total"),
            func.coalesce(func.count(FiscalDocument.id), 0).label("docs_count"),
        )
        .where(*base_where)
        .where(FiscalDocument.status == "issued")
    )
    if effective_establishment_id is not None:
        totals_stmt = totals_stmt.select_from(FiscalDocument).join(Sale, Sale.id == FiscalDocument.sale_id).where(
            or_(Sale.establishment_id == effective_establishment_id, Sale.establishment_id.is_(None))
        )
    totals = db.execute(totals_stmt).one()

    cancelled_stmt = (
        select(func.coalesce(func.count(FiscalDocument.id), 0).label("cancelled_count"))
        .where(*base_where)
        .where(FiscalDocument.status == "cancelled")
    )
    if effective_establishment_id is not None:
        cancelled_stmt = cancelled_stmt.select_from(FiscalDocument).join(Sale, Sale.id == FiscalDocument.sale_id).where(
            or_(Sale.establishment_id == effective_establishment_id, Sale.establishment_id.is_(None))
        )
    cancelled = db.execute(cancelled_stmt).one()

    by_type_stmt = (
        select(
            FiscalDocument.document_type,
            func.coalesce(func.count(FiscalDocument.id), 0).label("count"),
            func.coalesce(func.sum(FiscalDocument.gross_total), 0).label("gross_total"),
        )
        .where(*base_where)
        .where(FiscalDocument.status == "issued")
        .group_by(FiscalDocument.document_type)
        .order_by(FiscalDocument.document_type.asc())
    )
    if effective_establishment_id is not None:
        by_type_stmt = by_type_stmt.select_from(FiscalDocument).join(Sale, Sale.id == FiscalDocument.sale_id).where(
            or_(Sale.establishment_id == effective_establishment_id, Sale.establishment_id.is_(None))
        )
    by_type_rows = db.execute(by_type_stmt).all()

    vat_stmt = (
        select(
            FiscalDocumentLine.tax_rate,
            func.coalesce(func.sum(FiscalDocumentLine.line_net), 0).label("net_total"),
            func.coalesce(func.sum(FiscalDocumentLine.line_tax), 0).label("tax_total"),
            func.coalesce(func.sum(FiscalDocumentLine.line_gross), 0).label("gross_total"),
        )
        .select_from(FiscalDocumentLine)
        .join(FiscalDocument, FiscalDocument.id == FiscalDocumentLine.fiscal_document_id)
        .where(FiscalDocumentLine.company_id == current_user.company_id)
        .where(local_day == day)
        .where(FiscalDocument.status == "issued")
        .group_by(FiscalDocumentLine.tax_rate)
        .order_by(FiscalDocumentLine.tax_rate.asc())
    )
    if effective_establishment_id is not None:
        vat_stmt = vat_stmt.join(Sale, Sale.id == FiscalDocument.sale_id).where(
            or_(Sale.establishment_id == effective_establishment_id, Sale.establishment_id.is_(None))
        )
    vat_rows = db.execute(vat_stmt).all()

    return {
        "day": str(day),
        "docs_issued": int(totals.docs_count or 0),
        "docs_cancelled": int(cancelled.cancelled_count or 0),
        "net_total": float(totals.net_total or 0),
        "tax_total": float(totals.tax_total or 0),
        "gross_total": float(totals.gross_total or 0),
        "by_type": [
            {
                "document_type": r.document_type,
                "count": int(r.count or 0),
                "gross_total": float(r.gross_total or 0),
            }
            for r in by_type_rows
        ],
        "vat_by_rate": [
            {
                "tax_rate": float(r.tax_rate or 0),
                "net_total": float(r.net_total or 0),
                "tax_total": float(r.tax_total or 0),
                "gross_total": float(r.gross_total or 0),
            }
            for r in vat_rows
        ],
    }


@router.get("/daily-z.pdf")
def daily_z_report_pdf(
    day: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = daily_z_report(day, db, current_user)
    company = db.get(Company, current_user.company_id)
    elements = daily_z_pdf_elements(data, company.__dict__ if company else {})
    pdf_bytes = render_pdf("Fecho Diário Z", elements)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="fecho_z_{day}.pdf"'},
    )


@router.get("/vat-by-rate")
def vat_by_rate_report(
    start_day: date,
    end_day: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    local_day = _doc_local_day_expr()

    rows = db.execute(
        select(
            FiscalDocumentLine.tax_rate,
            func.coalesce(func.sum(FiscalDocumentLine.line_net), 0).label("net_total"),
            func.coalesce(func.sum(FiscalDocumentLine.line_tax), 0).label("tax_total"),
            func.coalesce(func.sum(FiscalDocumentLine.line_gross), 0).label("gross_total"),
        )
        .select_from(FiscalDocumentLine)
        .join(FiscalDocument, FiscalDocument.id == FiscalDocumentLine.fiscal_document_id)
        .where(FiscalDocumentLine.company_id == current_user.company_id)
        .where(FiscalDocument.company_id == current_user.company_id)
        .where(FiscalDocument.branch_id == int(current_user.branch_id))
        .where(FiscalDocument.status == "issued")
        .where(local_day >= start_day)
        .where(local_day <= end_day)
        .group_by(FiscalDocumentLine.tax_rate)
        .order_by(FiscalDocumentLine.tax_rate.asc())
    ).all()

    return {
        "start_day": str(start_day),
        "end_day": str(end_day),
        "rows": [
            {
                "tax_rate": float(r.tax_rate or 0),
                "net_total": float(r.net_total or 0),
                "tax_total": float(r.tax_total or 0),
                "gross_total": float(r.gross_total or 0),
            }
            for r in rows
        ],
    }


@router.get("/vat-by-rate.pdf")
def vat_by_rate_report_pdf(
    start_day: date,
    end_day: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = vat_by_rate_report(start_day, end_day, db, current_user)
    company = db.get(Company, current_user.company_id)
    elements = vat_by_rate_pdf_elements(data, company.__dict__ if company else {})
    pdf_bytes = render_pdf("IVA por Taxa", elements)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="iva_por_taxa_{start_day}_a_{end_day}.pdf"'},
    )


def _sale_local_day_expr():
    return func.date(func.timezone("Africa/Maputo", Sale.created_at))


@router.get("/sales-by-period")
def sales_by_period(
    start_day: date,
    end_day: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    local_day = _sale_local_day_expr()
    paid_statuses = ["paid", "completed", "closed"]
    effective_establishment_id: int | None = None
    if getattr(current_user, "establishment_id", None) is not None:
        effective_establishment_id = int(current_user.establishment_id)
    base_where = [
        Sale.company_id == current_user.company_id,
        Sale.branch_id == int(current_user.branch_id),
        Sale.status.in_(paid_statuses),
        local_day >= start_day,
        local_day <= end_day,
    ]
    if effective_establishment_id is not None:
        base_where.append(or_(Sale.establishment_id == effective_establishment_id, Sale.establishment_id.is_(None)))

    sales_rows = db.execute(
        select(
            Sale,
            func.coalesce(Sale.total, 0).label("gross_total"),
            func.coalesce(getattr(Sale, "net_total", 0), 0).label("net_total"),
            func.coalesce(getattr(Sale, "tax_total", 0), 0).label("tax_total"),
            func.coalesce(getattr(Sale, "discount_value", 0), 0).label("discount_value"),
        )
        .select_from(Sale)
        .where(*base_where)
        .order_by(Sale.created_at.asc())
    ).all()

    sale_ids = [int(sale.id) for sale, _s_gross, _s_net, _s_tax, _s_disc in sales_rows]
    printer_lines_by_sale: dict[int, list[dict]] = {}
    if sale_ids:
        pl_rows = db.execute(
            select(
                PrinterSaleLine.sale_id,
                PrinterSaleLine.printer_id,
                Printer.serial_number,
                Printer.brand,
                Printer.model,
                PrinterSaleLine.counter_type_id,
                PrinterCounterType.code,
                PrinterCounterType.name,
                PrinterSaleLine.copies,
                PrinterSaleLine.unit_price,
                PrinterSaleLine.line_total,
            )
            .select_from(PrinterSaleLine)
            .join(Printer, Printer.id == PrinterSaleLine.printer_id)
            .outerjoin(PrinterCounterType, PrinterCounterType.id == PrinterSaleLine.counter_type_id)
            .where(PrinterSaleLine.company_id == current_user.company_id)
            .where(PrinterSaleLine.branch_id == int(current_user.branch_id))
            .where(PrinterSaleLine.sale_id.in_(sale_ids))
            .order_by(PrinterSaleLine.sale_id.asc(), PrinterSaleLine.id.asc())
        ).all()
        for (
            sale_id,
            printer_id,
            serial_number,
            brand,
            model,
            counter_type_id,
            counter_code,
            counter_name,
            copies,
            unit_price,
            line_total,
        ) in pl_rows:
            sid = int(sale_id)
            printer_lines_by_sale.setdefault(sid, []).append(
                {
                    "printer_id": int(printer_id),
                    "serial_number": serial_number,
                    "brand": brand,
                    "model": model,
                    "counter_type_id": int(counter_type_id) if counter_type_id is not None else None,
                    "counter_type_code": counter_code,
                    "counter_type_name": counter_name,
                    "copies": int(copies or 0),
                    "unit_price": float(unit_price or 0),
                    "line_total": float(line_total or 0),
                }
            )

    sales = []
    net_total = tax_total = gross_total = discount_total = 0.0
    for sale, s_gross, s_net, s_tax, s_disc in sales_rows:
        s_gross_f = float(s_gross or 0)
        s_net_f = float(s_net or 0)
        s_tax_f = float(s_tax or 0)
        s_disc_f = float(s_disc or 0)
        net_total += s_net_f
        tax_total += s_tax_f
        gross_total += s_gross_f
        discount_total += s_disc_f
        sales.append({
            "id": sale.id,
            "created_at": sale.created_at.isoformat(),
            "payment_method": sale.payment_method,
            "status": sale.status,
            "sale_channel": sale.sale_channel,
            "net_total": s_net_f,
            "tax_total": s_tax_f,
            "discount_value": s_disc_f,
            "gross_total": s_gross_f,
            "printer_lines": printer_lines_by_sale.get(int(sale.id), []),
        })

    return {
        "start_day": str(start_day),
        "end_day": str(end_day),
        "sales_count": len(sales),
        "net_total": net_total,
        "tax_total": tax_total,
        "discount_total": discount_total,
        "gross_total": gross_total,
        "sales": sales,
    }


@router.get("/sales-by-period.pdf")
def sales_by_period_pdf(
    start_day: date,
    end_day: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = sales_by_period(start_day, end_day, db, current_user)
    company = db.get(Company, current_user.company_id)
    elements = sales_by_period_pdf_elements(data, company.__dict__ if company else {}, start_day, end_day)
    pdf_bytes = render_pdf("Vendas por Período", elements)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="vendas_{start_day}_a_{end_day}.pdf"'},
    )


@router.get("/cash-closure")
def cash_closure(
    day: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    local_day = _sale_local_day_expr()
    paid_statuses = ["paid", "completed", "closed"]
    effective_establishment_id: int | None = None
    if getattr(current_user, "establishment_id", None) is not None:
        effective_establishment_id = int(current_user.establishment_id)
    base_where = [
        Sale.company_id == current_user.company_id,
        Sale.branch_id == int(current_user.branch_id),
        Sale.cashier_id == current_user.id,
        Sale.status.in_(paid_statuses),
        local_day == day,
    ]
    if effective_establishment_id is not None:
        base_where.append(or_(Sale.establishment_id == effective_establishment_id, Sale.establishment_id.is_(None)))

    sales_rows = db.execute(
        select(
            Sale,
            func.coalesce(Sale.total, 0).label("gross_total"),
            func.coalesce(Sale.net_total, 0).label("net_total"),
            func.coalesce(Sale.tax_total, 0).label("tax_total"),
        )
        .select_from(Sale)
        .where(*base_where)
        .order_by(Sale.created_at.asc())
    ).all()

    sale_ids = [int(sale.id) for sale, _s_gross, _s_net, _s_tax in sales_rows]
    printer_lines_by_sale: dict[int, list[dict]] = {}
    if sale_ids:
        pl_rows = db.execute(
            select(
                PrinterSaleLine.sale_id,
                PrinterSaleLine.printer_id,
                Printer.serial_number,
                Printer.brand,
                Printer.model,
                PrinterSaleLine.counter_type_id,
                PrinterCounterType.code,
                PrinterCounterType.name,
                PrinterSaleLine.copies,
                PrinterSaleLine.unit_price,
                PrinterSaleLine.line_total,
            )
            .select_from(PrinterSaleLine)
            .join(Printer, Printer.id == PrinterSaleLine.printer_id)
            .outerjoin(PrinterCounterType, PrinterCounterType.id == PrinterSaleLine.counter_type_id)
            .where(PrinterSaleLine.company_id == current_user.company_id)
            .where(PrinterSaleLine.branch_id == int(current_user.branch_id))
            .where(PrinterSaleLine.sale_id.in_(sale_ids))
            .order_by(PrinterSaleLine.sale_id.asc(), PrinterSaleLine.id.asc())
        ).all()
        for (
            sale_id,
            printer_id,
            serial_number,
            brand,
            model,
            counter_type_id,
            counter_code,
            counter_name,
            copies,
            unit_price,
            line_total,
        ) in pl_rows:
            sid = int(sale_id)
            printer_lines_by_sale.setdefault(sid, []).append(
                {
                    "printer_id": int(printer_id),
                    "serial_number": serial_number,
                    "brand": brand,
                    "model": model,
                    "counter_type_id": int(counter_type_id) if counter_type_id is not None else None,
                    "counter_type_code": counter_code,
                    "counter_type_name": counter_name,
                    "copies": int(copies or 0),
                    "unit_price": float(unit_price or 0),
                    "line_total": float(line_total or 0),
                }
            )

    sales = []
    net_total = tax_total = gross_total = 0.0
    for sale, s_gross, s_net, s_tax in sales_rows:
        s_gross_f = float(s_gross or 0)
        s_net_f = float(s_net or 0)
        s_tax_f = float(s_tax or 0)
        net_total += s_net_f
        tax_total += s_tax_f
        gross_total += s_gross_f
        sales.append({
            "id": sale.id,
            "created_at": sale.created_at.isoformat(),
            "payment_method": sale.payment_method,
            "status": sale.status,
            "sale_channel": sale.sale_channel,
            "net_total": s_net_f,
            "tax_total": s_tax_f,
            "gross_total": s_gross_f,
            "printer_lines": printer_lines_by_sale.get(int(sale.id), []),
        })

    return {
        "day": str(day),
        "sales_count": len(sales),
        "net_total": net_total,
        "tax_total": tax_total,
        "gross_total": gross_total,
        "sales": sales,
    }


@router.get("/cash-closure.pdf")
def cash_closure_pdf(
    day: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = cash_closure(day, db, current_user)
    company = db.get(Company, current_user.company_id)
    elements = cash_closure_pdf_elements(data, company.__dict__ if company else {}, current_user.__dict__, day)
    pdf_bytes = render_pdf("Fecho de Caixa", elements)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="fecho_caixa_{day}.pdf"'},
    )

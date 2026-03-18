from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response
import os
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.deps import get_current_user
from app.models.company import Company
from app.models.customer import Customer
from app.models.product import Product
from app.models.quote import Quote
from app.models.quote_item import QuoteItem
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.user import User
from app.schemas.quotes import ConvertQuotePayload, CreateQuotePayload, QuoteItemOut, QuoteOut, QuoteUpdatePayload
from app.utils.pdf import quote_pdf_elements, render_pdf
from app.settings import Settings

router = APIRouter()
settings = Settings()


def _next_quote_number(db: Session, company_id: int, series: str) -> int:
    max_number = db.scalar(
        select(func.max(Quote.number)).where(Quote.company_id == company_id).where(Quote.series == series)
    )
    return int(max_number or 0) + 1


def _build_quote_out(db: Session, current_user: User, quote: Quote) -> QuoteOut:
    items = db.scalars(
        select(QuoteItem)
        .where(QuoteItem.company_id == current_user.company_id)
        .where(QuoteItem.quote_id == quote.id)
        .order_by(QuoteItem.id.asc())
    ).all()

    return QuoteOut(
        id=quote.id,
        company_id=quote.company_id,
        cashier_id=quote.cashier_id,
        series=quote.series,
        number=quote.number,
        status=quote.status,
        customer_name=quote.customer_name,
        customer_nuit=quote.customer_nuit,
        currency=quote.currency,
        net_total=float(quote.net_total),
        tax_total=float(quote.tax_total),
        gross_total=float(quote.gross_total),
        include_tax=bool(getattr(quote, "include_tax", True)),
        discount_value=float(getattr(quote, "discount_value", 0) or 0),
        sale_id=quote.sale_id,
        created_at=quote.created_at,
        updated_at=quote.updated_at,
        items=[QuoteItemOut.model_validate(i) for i in items],
    )


@router.get("", response_model=list[QuoteOut])
@router.get("/", response_model=list[QuoteOut], include_in_schema=False)
def list_quotes(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = db.scalars(
        select(Quote)
        .where(Quote.company_id == current_user.company_id)
        .order_by(desc(Quote.id))
        .limit(limit)
        .offset(offset)
    ).all()
    return [_build_quote_out(db, current_user, q) for q in rows]


@router.post("", response_model=QuoteOut)
@router.post("/", response_model=QuoteOut, include_in_schema=False)
def create_quote(
    payload: CreateQuotePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not payload.items:
        raise HTTPException(status_code=400, detail="Informe itens da cotação")

    series = (payload.series or "A").strip().upper() or "A"

    number = _next_quote_number(db, current_user.company_id, series)

    include_tax = bool(getattr(payload, "include_tax", True))
    discount_value = round(max(0.0, float(getattr(payload, "discount_value", 0) or 0)), 2)

    net_total = 0.0
    tax_total = 0.0
    gross_total = 0.0

    quote = Quote(
        company_id=current_user.company_id,
        cashier_id=current_user.id,
        series=series,
        number=number,
        status="open",
        customer_name=(payload.customer_name.strip() if payload.customer_name else None),
        customer_nuit=(payload.customer_nuit.strip() if payload.customer_nuit else None),
        currency=(payload.currency or "MZN"),
        net_total=0,
        tax_total=0,
        gross_total=0,
        include_tax=include_tax,
        discount_value=discount_value,
        sale_id=None,
    )
    db.add(quote)
    db.flush()

    for it in payload.items:
        tax_rate = 0.0
        if it.product_id:
            p = db.get(Product, it.product_id)
            if p and p.company_id == current_user.company_id:
                tax_rate = float(getattr(p, "tax_rate", 0) or 0)

        qty = float(it.qty or 0)
        unit_price = float(it.unit_price or 0)
        line_net = qty * unit_price
        line_tax = line_net * (tax_rate / 100.0) if include_tax and tax_rate > 0 else 0.0
        line_gross = line_net + line_tax

        net_total += line_net
        tax_total += line_tax
        gross_total += line_gross

        row = QuoteItem(
            company_id=current_user.company_id,
            quote_id=quote.id,
            product_id=it.product_id,
            product_name=it.product_name,
            qty=qty,
            unit_price=unit_price,
            line_net=line_net,
            tax_rate=tax_rate,
            line_tax=line_tax,
            line_gross=line_gross,
        )
        db.add(row)

    quote.net_total = net_total
    quote.tax_total = tax_total
    quote.gross_total = max(0.0, gross_total - discount_value)

    db.commit()
    db.refresh(quote)
    return _build_quote_out(db, current_user, quote)


@router.put("/{quote_id}", response_model=QuoteOut)
def update_quote(
    quote_id: int,
    payload: QuoteUpdatePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    quote = db.get(Quote, quote_id)
    if not quote or quote.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Cotação não encontrada")
    if quote.status != "open":
        raise HTTPException(status_code=400, detail="Só é possível editar cotações em aberto")
    if quote.sale_id:
        raise HTTPException(status_code=400, detail="Cotação já foi convertida")

    data = payload.model_dump(exclude_unset=True)

    if "series" in data and data["series"] is not None:
        quote.series = (data["series"] or "A").strip().upper() or "A"
    if "customer_name" in data:
        quote.customer_name = data["customer_name"].strip() if data["customer_name"] else None
    if "customer_nuit" in data:
        quote.customer_nuit = data["customer_nuit"].strip() if data["customer_nuit"] else None
    if "currency" in data and data["currency"] is not None:
        quote.currency = data["currency"] or "MZN"

    if "include_tax" in data and data["include_tax"] is not None:
        quote.include_tax = bool(data["include_tax"])
    if "discount_value" in data and data["discount_value"] is not None:
        quote.discount_value = round(max(0.0, float(data["discount_value"] or 0)), 2)

    if "items" in data and data["items"] is not None:
        items_in = data["items"]
        if not items_in:
            raise HTTPException(status_code=400, detail="Informe itens da cotação")

        # remove itens atuais
        db.query(QuoteItem).filter(QuoteItem.company_id == current_user.company_id).filter(QuoteItem.quote_id == quote.id).delete()

        net_total = 0.0
        tax_total = 0.0
        gross_total = 0.0

        include_tax = bool(getattr(quote, "include_tax", True))
        for it in items_in:
            tax_rate = 0.0
            if it.get("product_id"):
                p = db.get(Product, it["product_id"])
                if p and p.company_id == current_user.company_id:
                    tax_rate = float(getattr(p, "tax_rate", 0) or 0)

            qty = float(it.get("qty", 0))
            unit_price = float(it.get("unit_price", 0))
            line_net = qty * unit_price
            line_tax = line_net * (tax_rate / 100.0) if include_tax and tax_rate > 0 else 0.0
            line_gross = line_net + line_tax

            net_total += line_net
            tax_total += line_tax
            gross_total += line_gross

            row = QuoteItem(
                company_id=current_user.company_id,
                quote_id=quote.id,
                product_id=it.get("product_id"),
                product_name=it.get("product_name"),
                qty=qty,
                unit_price=unit_price,
                line_net=line_net,
                tax_rate=tax_rate,
                line_tax=line_tax,
                line_gross=line_gross,
            )
            db.add(row)

        discount_value = float(getattr(quote, "discount_value", 0) or 0)
        quote.net_total = net_total
        quote.tax_total = tax_total
        quote.gross_total = max(0.0, gross_total - discount_value)

    db.add(quote)
    db.commit()
    db.refresh(quote)
    return _build_quote_out(db, current_user, quote)


@router.delete("/{quote_id}", response_model=dict)
def delete_quote(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    quote = db.get(Quote, quote_id)
    if not quote or quote.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Cotação não encontrada")
    if quote.status != "open":
        raise HTTPException(status_code=400, detail="Só é possível eliminar cotações em aberto")
    if quote.sale_id:
        raise HTTPException(status_code=400, detail="Cotação já foi convertida")

    db.query(QuoteItem).filter(QuoteItem.company_id == current_user.company_id).filter(QuoteItem.quote_id == quote.id).delete()
    db.delete(quote)
    db.commit()
    return {"deleted": True}


@router.post("/{quote_id}/convert", response_model=dict)
def convert_quote_to_sale(
    quote_id: int,
    payload: ConvertQuotePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    quote = db.get(Quote, quote_id)
    if not quote or quote.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Cotação não encontrada")
    if quote.status != "open":
        raise HTTPException(status_code=400, detail="Cotação já foi convertida/cancelada")

    items = db.scalars(
        select(QuoteItem)
        .where(QuoteItem.company_id == current_user.company_id)
        .where(QuoteItem.quote_id == quote.id)
        .order_by(QuoteItem.id.asc())
    ).all()
    if not items:
        raise HTTPException(status_code=400, detail="Cotação sem itens")

    quote_total = float(quote.gross_total or 0)
    paid = float(payload.paid) if payload.paid is not None else quote_total

    sale = Sale(
        company_id=current_user.company_id,
        branch_id=int(getattr(current_user, "branch_id", 0) or 0),
        establishment_id=(
            int(getattr(current_user, "establishment_id", 0) or 0)
            if getattr(current_user, "establishment_id", None) is not None
            else None
        ),
        cashier_id=current_user.id,
        cash_session_id=None,
        business_type="retail",
        total=quote_total,
        net_total=float(getattr(quote, "net_total", 0) or 0),
        tax_total=float(getattr(quote, "tax_total", 0) or 0),
        discount_value=float(getattr(quote, "discount_value", 0) or 0),
        include_tax=bool(getattr(quote, "include_tax", True)),
        paid=paid,
        change=max(0.0, paid - quote_total),
        payment_method=(payload.payment_method or "cash"),
        status="paid",
        sale_channel="counter",
        table_number=None,
        seat_number=None,
        created_at=datetime.utcnow(),
    )
    db.add(sale)
    db.flush()

    for it in items:
        si = SaleItem(
            sale_id=sale.id,
            product_id=it.product_id,
            qty=float(it.qty),
            price=float(it.unit_price),
        )
        db.add(si)

    quote.status = "converted"
    quote.sale_id = sale.id

    db.commit()

    return {"quote_id": quote.id, "sale_id": sale.id}


@router.get("/{quote_id}/pdf")
def quote_pdf(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    quote = db.get(Quote, quote_id)
    if not quote or quote.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Cotação não encontrada")

    items = db.scalars(
        select(QuoteItem)
        .where(QuoteItem.company_id == current_user.company_id)
        .where(QuoteItem.quote_id == quote.id)
        .order_by(QuoteItem.id.asc())
    ).all()

    company = db.get(Company, current_user.company_id)
    company_dict = company.__dict__ if company else {}
    logo_url = (company_dict.get("logo_url") or "").strip()
    if logo_url.startswith("/uploads/"):
        fn = logo_url.split("/uploads/", 1)[1]
        company_dict["logo_path"] = os.path.join(settings.upload_dir, fn)

    quote_dict = {
        "id": int(quote.id),
        "series": quote.series,
        "number": int(quote.number),
        "status": quote.status,
        "customer_name": quote.customer_name,
        "customer_nuit": quote.customer_nuit,
        "currency": quote.currency,
        "net_total": float(quote.net_total or 0),
        "tax_total": float(quote.tax_total or 0),
        "gross_total": float(quote.gross_total or 0),
        "created_at": quote.created_at.isoformat() if quote.created_at else None,
    }

    customer = None
    branch_id = getattr(current_user, "branch_id", None)
    q_nuit = (quote.customer_nuit or "").strip()
    q_name = (quote.customer_name or "").strip()
    if q_nuit:
        stmt = (
            select(Customer)
            .where(Customer.company_id == current_user.company_id)
            .where(func.coalesce(Customer.nuit, "") == q_nuit)
            .limit(1)
        )
        if branch_id is not None:
            stmt = stmt.where(Customer.branch_id == int(branch_id))
        customer = db.scalar(stmt)
    if not customer and q_name:
        stmt = (
            select(Customer)
            .where(Customer.company_id == current_user.company_id)
            .where(func.lower(func.coalesce(Customer.name, "")) == q_name.lower())
            .limit(1)
        )
        if branch_id is not None:
            stmt = stmt.where(Customer.branch_id == int(branch_id))
        customer = db.scalar(stmt)

    customer_dict = {}
    if customer is not None:
        customer_dict = {
            "id": int(customer.id),
            "name": customer.name,
            "nuit": customer.nuit,
            "email": customer.email,
            "phone": customer.phone,
            "address": customer.address,
        }

    item_dicts = [
        {
            "product_id": int(i.product_id) if i.product_id is not None else None,
            "product_name": i.product_name,
            "qty": float(i.qty or 0),
            "unit_price": float(i.unit_price or 0),
            "line_net": float(i.line_net or 0),
            "tax_rate": float(i.tax_rate or 0),
            "line_tax": float(i.line_tax or 0),
            "line_gross": float(i.line_gross or 0),
        }
        for i in (items or [])
    ]

    pdf_data = {"quote": quote_dict, "items": item_dicts, "customer": customer_dict}
    elements = quote_pdf_elements(pdf_data, company_dict)
    pdf_bytes = render_pdf(f"Cotação {quote.series}/{quote.number}", elements, on_page=pdf_data.get("on_page"))
    filename = f"cotacao_{quote.series}_{quote.number}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.deps import get_current_user
from app.models.customer import Customer
from app.models.fiscal_document import FiscalDocument
from app.models.fiscal_document_line import FiscalDocumentLine
from app.models.product import Product
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.user import User
from app.schemas.fiscal_documents import CancelFiscalDocumentPayload, FiscalDocumentLineOut, FiscalDocumentOut, IssueFromSalePayload

router = APIRouter()


_ALLOWED_TYPES = {"invoice", "receipt", "ticket"}


def _get_cashier_name(db: Session, current_user: User, cashier_id: int | None) -> str | None:
    if not cashier_id:
        return None
    u = db.get(User, cashier_id)
    if not u or u.company_id != current_user.company_id:
        return None
    return u.name


def _build_doc_out(db: Session, current_user: User, doc: FiscalDocument) -> FiscalDocumentOut:
    lines = db.scalars(
        select(FiscalDocumentLine)
        .where(FiscalDocumentLine.company_id == current_user.company_id)
        .where(FiscalDocumentLine.fiscal_document_id == doc.id)
        .order_by(FiscalDocumentLine.id.asc())
    ).all()

    return FiscalDocumentOut(
        id=doc.id,
        company_id=doc.company_id,
        branch_id=getattr(doc, "branch_id", 0) or 0,
        sale_id=doc.sale_id,
        cashier_id=doc.cashier_id,
        document_type=doc.document_type,
        series=doc.series,
        number=doc.number,
        status=doc.status,
        customer_id=doc.customer_id,
        customer_name=doc.customer_name,
        customer_nuit=doc.customer_nuit,
        currency=doc.currency,
        net_total=float(doc.net_total),
        tax_total=float(doc.tax_total),
        gross_total=float(doc.gross_total),
        issued_at=doc.issued_at,
        cancelled_at=doc.cancelled_at,
        cancelled_by=doc.cancelled_by,
        cancel_reason=doc.cancel_reason,
        lines=[FiscalDocumentLineOut.model_validate(l) for l in lines],
    )


@router.get("", response_model=list[FiscalDocumentOut])
@router.get("/", response_model=list[FiscalDocumentOut], include_in_schema=False)
def list_fiscal_documents(
    limit: int = 50,
    offset: int = 0,
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    role = (getattr(current_user, "role", "") or "").strip().lower()
    is_admin = role in {"admin", "owner"}

    stmt = select(FiscalDocument).where(FiscalDocument.company_id == current_user.company_id)
    if is_admin:
        if branch_id is not None:
            stmt = stmt.where(FiscalDocument.branch_id == int(branch_id))
    else:
        stmt = stmt.where(FiscalDocument.branch_id == int(current_user.branch_id))

    rows = db.scalars(stmt.order_by(desc(FiscalDocument.id)).limit(limit).offset(offset)).all()

    return [_build_doc_out(db, current_user, d) for d in rows]


@router.get("/by-sale/{sale_id}", response_model=list[FiscalDocumentOut])
def list_fiscal_documents_by_sale(
    sale_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sale = db.get(Sale, sale_id)
    role = (getattr(current_user, "role", "") or "").strip().lower()
    is_admin = role in {"admin", "owner"}

    if not sale or sale.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Venda não encontrada")
    if not is_admin and getattr(sale, "branch_id", None) != current_user.branch_id:
        raise HTTPException(status_code=404, detail="Venda não encontrada")

    rows = db.scalars(
        select(FiscalDocument)
        .where(FiscalDocument.company_id == current_user.company_id)
        .where(FiscalDocument.sale_id == sale_id)
        .order_by(desc(FiscalDocument.id))
    ).all()

    return [_build_doc_out(db, current_user, d) for d in rows]


@router.post("/issue-from-sale", response_model=FiscalDocumentOut)
def issue_from_sale(
    payload: IssueFromSalePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc_type = (payload.document_type or "").strip().lower()
    if doc_type not in _ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Tipo de documento inválido")

    series = (payload.series or "A").strip().upper()
    if not series:
        series = "A"

    role = (getattr(current_user, "role", "") or "").strip().lower()
    is_admin = role in {"admin", "owner"}

    sale = db.get(Sale, payload.sale_id)
    if not sale or sale.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Venda não encontrada")
    if not is_admin and getattr(sale, "branch_id", None) != current_user.branch_id:
        raise HTTPException(status_code=404, detail="Venda não encontrada")

    existing = db.scalar(
        select(func.count(FiscalDocument.id))
        .where(FiscalDocument.company_id == current_user.company_id)
        .where(FiscalDocument.sale_id == sale.id)
        .where(FiscalDocument.status == "issued")
    )
    if int(existing or 0) > 0:
        raise HTTPException(status_code=400, detail="Já existe documento emitido para esta venda")

    next_number = db.scalar(
        select(func.coalesce(func.max(FiscalDocument.number), 0))
        .where(FiscalDocument.company_id == current_user.company_id)
        .where(FiscalDocument.document_type == doc_type)
        .where(FiscalDocument.series == series)
    )
    next_number = int(next_number or 0) + 1

    customer_id = None
    customer_name = None
    customer_nuit = None

    if payload.customer_id:
        existing_customer = db.get(Customer, int(payload.customer_id))
        if (
            not existing_customer
            or existing_customer.company_id != current_user.company_id
            or getattr(existing_customer, "branch_id", None) != getattr(sale, "branch_id", None)
        ):
            raise HTTPException(status_code=404, detail="Cliente não encontrado")
        customer_id = existing_customer.id
        customer_name = existing_customer.name
        customer_nuit = existing_customer.nuit
    elif payload.customer:
        customer_name = (payload.customer.name or "").strip() or None
        customer_nuit = (payload.customer.nuit or "").strip() or None

        if customer_name:
            customer = Customer(
                company_id=current_user.company_id,
                branch_id=int(getattr(sale, "branch_id", current_user.branch_id) or current_user.branch_id),
                name=customer_name,
                nuit=customer_nuit,
                email=(payload.customer.email or None),
                phone=(payload.customer.phone or None),
                address=(payload.customer.address or None),
            )
            db.add(customer)
            db.flush()
            customer_id = customer.id

    sale_items = db.scalars(
        select(SaleItem)
        .where(SaleItem.company_id == current_user.company_id)
        .where(SaleItem.sale_id == sale.id)
        .order_by(SaleItem.id.asc())
    ).all()

    if not sale_items:
        raise HTTPException(status_code=400, detail="Venda sem itens")

    product_ids = list({int(i.product_id) for i in sale_items if i.product_id is not None})
    products = (
        db.scalars(
            select(Product)
            .where(Product.company_id == current_user.company_id)
            .where(Product.id.in_(product_ids))
        ).all()
        if product_ids
        else []
    )
    product_by_id = {int(p.id): p for p in products}

    lines_to_create: list[FiscalDocumentLine] = []
    net_total = 0.0
    tax_total = 0.0

    for it in sale_items:
        qty = float(it.qty or 0)
        unit_price = float(it.price_at_sale or 0)
        line_net = float(it.line_total or 0)

        p = product_by_id.get(int(it.product_id)) if it.product_id is not None else None
        tax_rate = float(getattr(p, "tax_rate", 0) or 0)
        line_tax = round(line_net * (tax_rate / 100.0), 2)
        line_gross = round(line_net + line_tax, 2)

        net_total = round(net_total + line_net, 2)
        tax_total = round(tax_total + line_tax, 2)

        lines_to_create.append(
            FiscalDocumentLine(
                company_id=current_user.company_id,
                fiscal_document_id=0,
                product_id=it.product_id,
                description=(getattr(p, "name", None) or f"Produto #{it.product_id}"),
                qty=qty,
                unit_price=unit_price,
                line_net=line_net,
                tax_rate=tax_rate,
                line_tax=line_tax,
                line_gross=line_gross,
            )
        )

    gross_total = round(net_total + tax_total, 2)

    doc = FiscalDocument(
        company_id=current_user.company_id,
        branch_id=int(getattr(sale, "branch_id", current_user.branch_id) or current_user.branch_id),
        sale_id=sale.id,
        cashier_id=getattr(sale, "cashier_id", None) or current_user.id,
        document_type=doc_type,
        series=series,
        number=next_number,
        status="issued",
        customer_id=customer_id,
        customer_name=customer_name,
        customer_nuit=customer_nuit,
        currency="MZN",
        net_total=net_total,
        tax_total=tax_total,
        gross_total=gross_total,
        issued_at=datetime.utcnow(),
    )
    db.add(doc)
    db.flush()

    for l in lines_to_create:
        l.fiscal_document_id = doc.id
        db.add(l)

    db.commit()
    db.refresh(doc)

    return _build_doc_out(db, current_user, doc)


@router.post("/{doc_id}/cancel", response_model=FiscalDocumentOut)
def cancel_fiscal_document(
    doc_id: int,
    payload: CancelFiscalDocumentPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = db.get(FiscalDocument, doc_id)
    if not doc or doc.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Documento não encontrado")

    if doc.status == "cancelled":
        return _build_doc_out(db, current_user, doc)

    doc.status = "cancelled"
    doc.cancelled_at = datetime.utcnow()
    doc.cancelled_by = current_user.id
    doc.cancel_reason = (payload.reason or "").strip() or None

    db.add(doc)
    db.commit()
    db.refresh(doc)

    return _build_doc_out(db, current_user, doc)

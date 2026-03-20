from datetime import datetime
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.deps import get_current_user
from app.models.cash_session import CashSession
from app.models.sale import Sale
from app.models.expense import Expense
from app.models.user import User
from app.models.company import Company
from app.schemas.cash_sessions import CashSessionCloseRequest, CashSessionOpenRequest, CashSessionOut, CashSessionPaymentTotals, CashSessionSummaryOut
from app.utils.pdf import render_pdf
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

router = APIRouter()


def _is_admin(current_user: User) -> bool:
    role = (getattr(current_user, "role", "") or "").strip().lower()
    return role in {"admin", "owner"}


def _get_open_session(db: Session, current_user: User) -> CashSession | None:
    if not getattr(current_user, "branch_id", None):
        return None

    if not getattr(current_user, "establishment_id", None):
        return None

    return db.scalar(
        select(CashSession)
        .where(CashSession.company_id == current_user.company_id)
        .where(CashSession.branch_id == int(current_user.branch_id))
        .where(CashSession.establishment_id == int(current_user.establishment_id))
        .where(CashSession.opened_by == current_user.id)
        .where(CashSession.status == "open")
        .order_by(CashSession.id.desc())
        .limit(1)
    )


@router.get("/current", response_model=CashSessionOut | None)
def current_cash_session(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    row = _get_open_session(db, current_user)
    return row


@router.post("/open", response_model=CashSessionOut)
def open_cash_session(
    payload: CashSessionOpenRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not getattr(current_user, "branch_id", None):
        raise HTTPException(status_code=400, detail="Filial inválida")

    if not getattr(current_user, "establishment_id", None):
        raise HTTPException(status_code=400, detail="Ponto inválido")

    existing = _get_open_session(db, current_user)
    if existing:
        raise HTTPException(status_code=409, detail="Já existe um caixa aberto")

    opening = float(payload.opening_balance or 0)
    if opening < 0:
        raise HTTPException(status_code=400, detail="Valor de abertura inválido")

    row = CashSession(
        company_id=current_user.company_id,
        branch_id=int(current_user.branch_id),
        establishment_id=int(current_user.establishment_id),
        opened_by=current_user.id,
        opened_at=datetime.utcnow(),
        opening_balance=opening,
        status="open",
        closing_balance_expected=opening,
        closing_balance_counted=0,
        difference=0,
        notes=None,
    )

    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/{cash_session_id}/summary", response_model=CashSessionSummaryOut)
def cash_session_summary(
    cash_session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = db.get(CashSession, cash_session_id)
    if not row or row.company_id != current_user.company_id or row.branch_id != int(current_user.branch_id):
        raise HTTPException(status_code=404, detail="Caixa não encontrado")

    if not getattr(current_user, "establishment_id", None):
        raise HTTPException(status_code=400, detail="Ponto inválido")
    if int(getattr(row, "establishment_id", 0) or 0) != int(current_user.establishment_id):
        raise HTTPException(status_code=404, detail="Caixa não encontrado")

    if (not _is_admin(current_user)) and row.opened_by != current_user.id:
        raise HTTPException(status_code=403, detail="Sem permissão para ver este caixa")

    paid_statuses = ["paid", "completed", "closed"]

    totals_row = db.execute(
        select(
            func.count(Sale.id).label("sales_count"),
            func.coalesce(func.sum(Sale.total), 0).label("gross_total"),
            func.coalesce(func.sum(Sale.net_total), 0).label("net_total"),
            func.coalesce(func.sum(Sale.tax_total), 0).label("tax_total"),
        )
        .select_from(Sale)
        .where(Sale.company_id == current_user.company_id)
        .where(Sale.branch_id == int(current_user.branch_id))
        .where(Sale.establishment_id == int(current_user.establishment_id))
        .where(Sale.cash_session_id == row.id)
        .where(Sale.status.in_(paid_statuses))
    ).one()

    by_pay_rows = db.execute(
        select(
            Sale.payment_method.label("payment_method"),
            func.count(Sale.id).label("sales_count"),
            func.coalesce(func.sum(Sale.total), 0).label("gross_total"),
            func.coalesce(func.sum(Sale.net_total), 0).label("net_total"),
            func.coalesce(func.sum(Sale.tax_total), 0).label("tax_total"),
        )
        .select_from(Sale)
        .where(Sale.company_id == current_user.company_id)
        .where(Sale.branch_id == int(current_user.branch_id))
        .where(Sale.establishment_id == int(current_user.establishment_id))
        .where(Sale.cash_session_id == row.id)
        .where(Sale.status.in_(paid_statuses))
        .group_by(Sale.payment_method)
        .order_by(Sale.payment_method.asc())
    ).all()

    by_payment: list[CashSessionPaymentTotals] = []
    cash_sales_total = 0.0
    for pm, cnt, gross, net, tax in by_pay_rows:
        pm_s = (pm or "").strip() or "unknown"
        gross_f = float(gross or 0)
        net_f = float(net or 0)
        tax_f = float(tax or 0)
        if pm_s == "cash":
            cash_sales_total = gross_f
        by_payment.append(
            CashSessionPaymentTotals(
                payment_method=pm_s,
                sales_count=int(cnt or 0),
                gross_total=gross_f,
                net_total=net_f,
                tax_total=tax_f,
            )
        )

    opening_balance = float(row.opening_balance or 0)
    cash_expenses_total = db.scalar(
        select(func.coalesce(func.sum(Expense.amount), 0))
        .where(Expense.company_id == current_user.company_id)
        .where(Expense.branch_id == int(current_user.branch_id))
        .where(Expense.establishment_id == int(current_user.establishment_id))
        .where(Expense.paid_cash_session_id == row.id)
        .where(Expense.status == "paid")
        .where(Expense.is_void.is_(False))
    )
    expected_cash = round(opening_balance + float(cash_sales_total or 0) - float(cash_expenses_total or 0), 2)

    return CashSessionSummaryOut(
        cash_session_id=row.id,
        company_id=row.company_id,
        branch_id=row.branch_id,
        establishment_id=getattr(row, "establishment_id", None),
        opened_by=row.opened_by,
        opened_at=row.opened_at,
        status=row.status,
        closed_at=row.closed_at,
        opening_balance=opening_balance,
        cash_sales_total=float(cash_sales_total or 0),
        cash_expenses_total=float(cash_expenses_total or 0),
        expected_cash=float(expected_cash),
        sales_count=int(getattr(totals_row, "sales_count", 0) or 0),
        gross_total=float(getattr(totals_row, "gross_total", 0) or 0),
        net_total=float(getattr(totals_row, "net_total", 0) or 0),
        tax_total=float(getattr(totals_row, "tax_total", 0) or 0),
        by_payment_method=by_payment,
    )


@router.post("/{cash_session_id}/close", response_model=CashSessionOut)
def close_cash_session(
    cash_session_id: int,
    payload: CashSessionCloseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = db.get(CashSession, cash_session_id)
    if not row or row.company_id != current_user.company_id or row.branch_id != int(current_user.branch_id):
        raise HTTPException(status_code=404, detail="Caixa não encontrado")

    if not getattr(current_user, "establishment_id", None):
        raise HTTPException(status_code=400, detail="Ponto inválido")
    if int(getattr(row, "establishment_id", 0) or 0) != int(current_user.establishment_id):
        raise HTTPException(status_code=404, detail="Caixa não encontrado")

    if row.status != "open":
        raise HTTPException(status_code=409, detail="Caixa já está fechado")

    if (not _is_admin(current_user)) and row.opened_by != current_user.id:
        raise HTTPException(status_code=403, detail="Sem permissão para fechar este caixa")

    counted = float(payload.closing_balance_counted or 0)
    if counted < 0:
        raise HTTPException(status_code=400, detail="Valor de fecho inválido")

    paid_statuses = ["paid", "completed", "closed"]

    cash_sales_total = db.scalar(
        select(func.coalesce(func.sum(Sale.total), 0))
        .where(Sale.company_id == current_user.company_id)
        .where(Sale.branch_id == int(current_user.branch_id))
        .where(Sale.establishment_id == int(current_user.establishment_id))
        .where(Sale.cashier_id == row.opened_by)
        .where(Sale.cash_session_id == row.id)
        .where(Sale.payment_method == "cash")
        .where(Sale.status.in_(paid_statuses))
    )

    cash_expenses_total = db.scalar(
        select(func.coalesce(func.sum(Expense.amount), 0))
        .where(Expense.company_id == current_user.company_id)
        .where(Expense.branch_id == int(current_user.branch_id))
        .where(Expense.establishment_id == int(current_user.establishment_id))
        .where(Expense.paid_cash_session_id == row.id)
        .where(Expense.status == "paid")
        .where(Expense.is_void.is_(False))
    )
    expected = float(row.opening_balance or 0) + float(cash_sales_total or 0) - float(cash_expenses_total or 0)
    diff = round(counted - expected, 2)

    row.closing_balance_expected = expected
    row.closing_balance_counted = counted
    row.difference = diff
    row.closed_at = datetime.utcnow()
    row.closed_by = current_user.id
    row.status = "closed"
    row.notes = (payload.notes or "").strip() or None

    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/{cash_session_id}/close-pdf")
def cash_session_close_pdf(
    cash_session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Gera PDF do relatório de fecho de caixa (igual PDV3)."""
    row = db.get(CashSession, cash_session_id)
    if not row or row.company_id != current_user.company_id or row.branch_id != int(current_user.branch_id):
        raise HTTPException(status_code=404, detail="Caixa não encontrado")

    if not getattr(current_user, "establishment_id", None):
        raise HTTPException(status_code=400, detail="Ponto inválido")
    if int(getattr(row, "establishment_id", 0) or 0) != int(current_user.establishment_id):
        raise HTTPException(status_code=404, detail="Caixa não encontrado")

    if (not _is_admin(current_user)) and row.opened_by != current_user.id:
        raise HTTPException(status_code=403, detail="Sem permissão para ver este caixa")

    # Buscar dados da empresa
    company = db.get(Company, current_user.company_id)
    company_data = {
        "name": getattr(company, "name", "") or "",
        "nuit": getattr(company, "nuit", "") or "",
        "address": getattr(company, "address", "") or "",
        "city": getattr(company, "city", "") or "",
        "phone": getattr(company, "phone", "") or "",
        "email": getattr(company, "email", "") or "",
        "logo_url": getattr(company, "logo_url", "") or "",
        "currency": "MZN",
    }

    # Buscar dados do usuário que abriu o caixa
    cashier = db.get(User, row.opened_by)
    cashier_name = (getattr(cashier, "name", None) or getattr(cashier, "username", "-")).strip() if cashier else "-"

    # Calcular totais de vendas
    paid_statuses = ["paid", "completed", "closed"]
    cash_sales_total = db.scalar(
        select(func.coalesce(func.sum(Sale.total), 0))
        .where(Sale.company_id == current_user.company_id)
        .where(Sale.branch_id == int(current_user.branch_id))
        .where(Sale.establishment_id == int(current_user.establishment_id))
        .where(Sale.cash_session_id == row.id)
        .where(Sale.payment_method == "cash")
        .where(Sale.status.in_(paid_statuses))
    )

    # Calcular totais de despesas pagas neste caixa
    cash_expenses_total = db.scalar(
        select(func.coalesce(func.sum(Expense.amount), 0))
        .where(Expense.company_id == current_user.company_id)
        .where(Expense.branch_id == int(current_user.branch_id))
        .where(Expense.establishment_id == int(current_user.establishment_id))
        .where(Expense.paid_cash_session_id == row.id)
        .where(Expense.status == "paid")
        .where(Expense.is_void.is_(False))
    )

    # Buscar detalhes das despesas
    expenses = db.execute(
        select(Expense)
        .where(Expense.company_id == current_user.company_id)
        .where(Expense.branch_id == int(current_user.branch_id))
        .where(Expense.establishment_id == int(current_user.establishment_id))
        .where(Expense.paid_cash_session_id == row.id)
        .where(Expense.status == "paid")
        .where(Expense.is_void.is_(False))
    ).scalars().all()

    opening = float(row.opening_balance or 0)
    expected = opening + float(cash_sales_total or 0) - float(cash_expenses_total or 0)
    counted = float(row.closing_balance_counted or 0)
    difference = round(counted - expected, 2)

    # Gerar PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    styles = getSampleStyleSheet()
    elements = []

    # Título
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=18,
        alignment=1,  # Centro
        spaceAfter=10,
        textColor=colors.HexColor('#1a237e'),
    )
    elements.append(Paragraph("FECHAMENTO DE CAIXA", title_style))
    elements.append(Spacer(0, 5 * mm))

    # Informações do fechamento
    closed_at_str = "-"
    if row.closed_at:
        closed_at_str = row.closed_at.strftime('%d/%m/%Y %H:%M')
    elif row.status == "open":
        closed_at_str = "Caixa ainda aberto"

    info_data = [
        ['Data do Fechamento:', closed_at_str],
        ['Funcionário:', cashier_name],
        ['Nº do Fechamento:', str(row.id)],
        ['Estado:', 'Fechado' if row.status == 'closed' else row.status],
    ]
    info_table = Table(info_data, colWidths=[45 * mm, None])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#424242')),
    ]))
    elements.append(info_table)
    elements.append(Spacer(0, 8 * mm))

    # Resumo Financeiro
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=8,
        textColor=colors.HexColor('#283593'),
    )
    elements.append(Paragraph("RESUMO FINANCEIRO", subtitle_style))
    elements.append(Spacer(0, 4 * mm))

    resumo_data = [
        ['Abertura (fundo de caixa)', f"{opening:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') + " MZN"],
        ['Vendas em Dinheiro', f"{float(cash_sales_total or 0):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') + " MZN"],
        ['Despesas em Dinheiro', "-" + f"{float(cash_expenses_total or 0):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') + " MZN"],
        ['', ''],
        ['ESPERADO (dinheiro)', f"{expected:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') + " MZN"],
        ['CONTADO', f"{counted:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') + " MZN"],
        ['DIFERENÇA', f"{difference:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') + " MZN"],
    ]

    resumo_table = Table(resumo_data, colWidths=[60 * mm, None])
    resumo_styles = [
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#424242')),
        ('LINEBELOW', (0, 2), (-1, 2), 0.5, colors.HexColor('#ddd')),
    ]

    # Destacar ESPERADO, CONTADO e DIFERENÇA
    for i in [4, 5, 6]:
        resumo_styles.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f5f5f5')))
        resumo_styles.append(('FONTNAME', (0, i), (0, i), 'Helvetica-Bold'))

    # Cor da diferença
    if difference < 0:
        resumo_styles.append(('TEXTCOLOR', (1, 6), (1, 6), colors.HexColor('#d32f2f')))  # Vermelho
    elif difference > 0:
        resumo_styles.append(('TEXTCOLOR', (1, 6), (1, 6), colors.HexColor('#388e3c')))  # Verde

    resumo_table.setStyle(TableStyle(resumo_styles))
    elements.append(resumo_table)
    elements.append(Spacer(0, 8 * mm))

    # Despesas do período
    if expenses:
        elements.append(Paragraph("DESPESAS DO PERÍODO", subtitle_style))
        elements.append(Spacer(0, 4 * mm))

        despesas_data = [['Categoria', 'Descrição', 'Valor (MZN)']]
        total_despesas = 0.0
        for exp in expenses:
            cat_name = getattr(exp.category, 'name', '-') if hasattr(exp, 'category') and exp.category else '-'
            despesas_data.append([
                cat_name,
                str(getattr(exp, 'description', '') or '')[:40],
                f"{float(getattr(exp, 'amount', 0) or 0):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
            ])
            total_despesas += float(getattr(exp, 'amount', 0) or 0)

        despesas_table = Table(despesas_data, colWidths=[40 * mm, None, 35 * mm])
        despesas_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#b71c1c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#ddd')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(despesas_table)
        elements.append(Spacer(0, 5 * mm))
        elements.append(Paragraph(f"Total de despesas: {total_despesas:,.2f} MZN".replace(',', 'X').replace('.', ',').replace('X', '.'), styles['Normal']))
        elements.append(Spacer(0, 8 * mm))

    # Observações
    if row.notes:
        elements.append(Paragraph("OBSERVAÇÕES", subtitle_style))
        elements.append(Spacer(0, 4 * mm))
        elements.append(Paragraph(str(row.notes), styles['Normal']))
        elements.append(Spacer(0, 10 * mm))

    # Assinaturas
    sig_data = [
        ['_' * 30, '_' * 30],
        ['Assinatura do Funcionário', 'Assinatura do Supervisor'],
    ]
    sig_table = Table(sig_data, colWidths=[80 * mm, 80 * mm])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, 1), 10),
        ('TOPPADDING', (0, 1), (-1, 1), 5),
        ('TEXTCOLOR', (0, 1), (-1, 1), colors.HexColor('#424242')),
    ]))
    elements.append(sig_table)

    # Rodapé com dados da empresa
    if company_data.get('name') or company_data.get('nuit'):
        elements.append(Spacer(0, 10 * mm))
        footer_text = f"{company_data.get('name', '')}"
        if company_data.get('nuit'):
            footer_text += f" · NUIT: {company_data.get('nuit')}"
        footer_para = Paragraph(
            footer_text,
            ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.HexColor('#666'),
                alignment=1,  # Centro
            )
        )
        elements.append(footer_para)

    doc.build(elements)
    buffer.seek(0)
    pdf_bytes = buffer.getvalue()

    filename = f"fechamento_caixa_{cashier_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )

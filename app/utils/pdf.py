from datetime import date, datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image


def _default_on_page(title: str):
    def _on_page(canvas, doc):
        canvas.saveState()
        width, _height = A4

        canvas.setStrokeColor(colors.HexColor('#d1d5db'))
        canvas.setLineWidth(0.5)
        canvas.line(15 * mm, 13 * mm, width - 15 * mm, 13 * mm)

        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor('#6b7280'))
        ts = datetime.now().strftime('%Y-%m-%d %H:%M')
        canvas.drawString(15 * mm, 8.5 * mm, f"{title} · Gerado em {ts}")
        canvas.drawRightString(width - 15 * mm, 8.5 * mm, f"Página {doc.page}")
        canvas.restoreState()

    return _on_page


def render_pdf(title: str, elements: list, on_page=None) -> bytes:
    """Render a list of Platypus elements to PDF bytes using ReportLab."""
    buffer = BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=15*mm, leftMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
    page_cb = on_page or _default_on_page(title)
    pdf.build(elements, onFirstPage=page_cb, onLaterPages=page_cb)
    buffer.seek(0)
    return buffer.getvalue()


def _company_info_table(company: dict) -> Table:
    data = [
        ['Empresa:', company.get('name', '-')],
        ['NUIT:', company.get('nuit', '-')],
    ]
    table = Table(data, colWidths=[30*mm, None])
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    return table


def _header_block(title: str, subtitle: str, company: dict) -> Table:
    styles = getSampleStyleSheet()
    title_p = Paragraph(f"<b>{title}</b>", ParagraphStyle('hdrTitle', parent=styles['Normal'], fontSize=14, leading=16))
    sub_p = Paragraph(subtitle, ParagraphStyle('hdrSub', parent=styles['Normal'], fontSize=10, textColor=colors.grey))

    left = [title_p, Spacer(0, 1.5 * mm), sub_p]
    right = [_company_info_table(company)]

    logo = None
    logo_url = company.get('logo_url') or company.get('logo')
    if logo_url:
        try:
            logo = Image(logo_url)
            logo.drawHeight = 16 * mm
            logo.drawWidth = 16 * mm
        except Exception:
            logo = None

    if logo is not None:
        data = [[logo, left, right]]
        widths = [18 * mm, None, 70 * mm]
    else:
        data = [[left, right]]
        widths = [None, 70 * mm]

    t = Table(data, colWidths=widths)
    t.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
    ]))
    return t


def _metric_cards(items: list[tuple[str, str]]) -> Table:
    """Two-row grid of metric cards (4 metrics recommended)."""
    # Layout as 2 columns x 2 rows by default.
    pairs = list(items or [])
    while len(pairs) < 4:
        pairs.append(("", ""))

    def _card(label: str, value: str):
        styles = getSampleStyleSheet()
        label_p = Paragraph(
            label or "&nbsp;",
            ParagraphStyle('mLabel', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#6b7280')),
        )
        value_p = Paragraph(
            f"<b>{value or ''}</b>",
            ParagraphStyle('mValue', parent=styles['Normal'], fontSize=14, textColor=colors.HexColor('#111827'), leading=16),
        )
        t = Table([[label_p], [value_p]], colWidths=[None], rowHeights=[6.5 * mm, 9 * mm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('BOX', (0, 0), (-1, -1), 0.6, colors.HexColor('#d1d5db')),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        return t

    grid = [
        [_card(*pairs[0]), _card(*pairs[1])],
        [_card(*pairs[2]), _card(*pairs[3])],
    ]
    t = Table(grid, colWidths=[None, None], rowHeights=[None, None])
    t.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('INNERGRID', (0, 0), (-1, -1), 0, colors.white),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [None, None]),
    ]))
    return t


def _fmt_money(value, currency: str = '') -> str:
    try:
        v = float(value or 0)
    except Exception:
        v = 0.0
    s = f"{v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    return f"{s} {currency}".strip()


def _payment_label(value: str | None) -> str:
    k = (value or '').strip().lower()
    return {
        'cash': 'Dinheiro',
        'card': 'Cartão (POS)',
        'mpesa': 'M-Pesa',
        'emola': 'e-Mola',
        'mkesh': 'mKesh',
        'transfer': 'Transferência',
        'cheque': 'Cheque',
        'other': 'Outro',
        'debt': 'Dívida (Fiado)',
    }.get(k, value or '-')


def _status_label(value: str | None) -> str:
    k = (value or '').strip().lower()
    return {
        'paid': 'Pago',
        'void': 'Anulado',
        'open': 'Aberto',
        'pending': 'Pendente',
        'completed': 'Concluído',
        'closed': 'Fechado',
    }.get(k, value or '-')


def _channel_label(value: str | None) -> str:
    k = (value or '').strip().lower()
    return {
        'counter': 'Balcão',
        'table': 'Mesa',
        'debt': 'Dívida',
        'printer': 'Impressora',
    }.get(k, value or '-')


def _table_from_list(headers: list, rows: list, aligns: list = None) -> Table:
    data = [headers] + rows
    col_widths = [None] * len(headers)
    table = Table(data, colWidths=col_widths, repeatRows=1)
    styles = [
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
    ]
    if aligns:
        for i, align in enumerate(aligns):
            styles.append(('ALIGN', (i, 0), (i, -1), align))
    table.setStyle(TableStyle(styles))
    return table


def _styled_table(headers: list, rows: list, col_widths: list, aligns: list) -> Table:
    t = Table([headers] + rows, colWidths=col_widths, repeatRows=1)
    styles = [
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#111827')),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#111827')),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#d1d5db')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]
    for i, a in enumerate(aligns):
        styles.append(('ALIGN', (i, 0), (i, -1), a))
    t.setStyle(TableStyle(styles))
    return t


def daily_z_pdf_elements(data: dict, company: dict) -> list:
    styles = getSampleStyleSheet()
    currency = (company.get('currency') or '').strip()
    elements = [
        _header_block('Fecho Diário (Z)', f"Data: {data.get('day', '')} (Africa/Maputo)", company),
        Spacer(0, 6 * mm),
        _metric_cards([
            ('Documentos emitidos', str(data.get('docs_issued', 0))),
            ('Documentos anulados', str(data.get('docs_cancelled', 0))),
            ('IVA', _fmt_money(data.get('tax_total', 0), currency)),
            ('Total', _fmt_money(data.get('gross_total', 0), currency)),
        ]),
        Spacer(0, 8 * mm),
        Paragraph('Por tipo de documento', ParagraphStyle('sec', parent=styles['Normal'], fontSize=11, textColor=colors.HexColor('#e2e8f0'))),
        Spacer(0, 3 * mm),
        _styled_table(
            ['Tipo', 'Qtd', 'Total'],
            [[r.get('document_type') or '-', str(r.get('count') or 0), _fmt_money(r.get('gross_total', 0), currency)] for r in data.get('by_type', [])],
            col_widths=[None, 20 * mm, 35 * mm],
            aligns=['LEFT', 'CENTER', 'RIGHT'],
        ),
        Spacer(0, 8 * mm),
        Paragraph('IVA por taxa', ParagraphStyle('sec2', parent=styles['Normal'], fontSize=11, textColor=colors.HexColor('#e2e8f0'))),
        Spacer(0, 3 * mm),
        _styled_table(
            ['Taxa', 'Incidência', 'IVA', 'Total'],
            [
                [
                    f"{float(r.get('tax_rate') or 0):.2f}%",
                    _fmt_money(r.get('net_total', 0), currency),
                    _fmt_money(r.get('tax_total', 0), currency),
                    _fmt_money(r.get('gross_total', 0), currency),
                ]
                for r in data.get('vat_by_rate', [])
            ],
            col_widths=[18 * mm, None, None, None],
            aligns=['RIGHT', 'RIGHT', 'RIGHT', 'RIGHT'],
        ),
    ]
    return elements


def quote_pdf_elements(data: dict, company: dict) -> list:
    styles = getSampleStyleSheet()

    quote = data.get("quote") or {}
    items = data.get("items") or []
    customer = data.get("customer") or {}

    def _fmt_date(v: str | None) -> str:
        if not v:
            return ""
        s = str(v)
        if "T" in s:
            s = s.split("T", 1)[0]
        return s

    customer_name = (quote.get("customer_name") or "").strip() or (customer.get("name") or "").strip()
    customer_nuit = (quote.get("customer_nuit") or "").strip() or (customer.get("nuit") or "").strip()
    customer_address = (customer.get("address") or "").strip()
    customer_city = (customer.get("city") or "").strip()
    customer_phone = (customer.get("phone") or "").strip()
    customer_email = (customer.get("email") or "").strip()
    created_day = _fmt_date(quote.get("created_at"))

    title_style = ParagraphStyle(
        "QuoteTitle",
        parent=styles["Normal"],
        fontSize=28,
        leading=30,
        textColor=colors.HexColor("#0b2a3b"),
        spaceAfter=6 * mm,
    )
    label_style = ParagraphStyle(
        "QuoteLabel",
        parent=styles["Normal"],
        fontSize=10,
        leading=12,
        textColor=colors.HexColor("#0b2a3b"),
    )

    top_row = Table(
        [
            [
                Paragraph("<b>ORÇAMENTO</b>", title_style),
                Table(
                    [[Paragraph("<b>DATA:</b>", label_style), ""]],
                    colWidths=[18 * mm, 55 * mm],
                ),
            ]
        ],
        colWidths=[None, 90 * mm],
    )
    top_row.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ("LINEBELOW", (1, 0), (1, 0), 0.8, colors.HexColor("#0b2a3b")),
                ("FONTSIZE", (1, 0), (1, 0), 10),
            ]
        )
    )

    # Fill date into the right cell while keeping the underline style.
    top_row._cellvalues[0][1]._cellvalues[0][1] = Paragraph(created_day or "", label_style)

    def _field_row(label: str, value: str = ""):
        t = Table([[Paragraph(f"<b>{label}</b>", label_style), Paragraph(value or "", label_style)]], colWidths=[28 * mm, None])
        t.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LINEBELOW", (1, 0), (1, 0), 0.8, colors.HexColor("#0b2a3b")),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )
        return t

    fields = [
        _field_row("Cliente:", customer_name),
        _field_row("NUIT:", customer_nuit),
        _field_row("Endereço:", customer_address),
        _field_row("Cidade:", customer_city),
        _field_row("Telefone:", customer_phone),
        _field_row("E-mail:", customer_email),
    ]

    # Items table: fixed number of rows to match template.
    fixed_rows = 12
    rows = []
    for it in items[:fixed_rows]:
        desc = (it.get("product_name") or "").strip()
        qty = float(it.get("qty") or 0)
        total = float(it.get("line_gross") or 0)
        rows.append([desc, f"{qty:.2f}" if qty else "", f"{total:.2f}" if total else ""])
    while len(rows) < fixed_rows:
        rows.append(["", "", ""])

    table = Table(
        [["DESCRIÇÃO", "QUANTIDADE", "VALOR"]] + rows,
        colWidths=[None, 45 * mm, 30 * mm],
        rowHeights=[12 * mm] + [9 * mm] * fixed_rows,
        repeatRows=1,
    )
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e6e7e6")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0b2a3b")),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 10),
                ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#0b2a3b")),
                ("ALIGN", (0, 1), (0, -1), "LEFT"),
                ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.8, colors.HexColor("#0b2a3b")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    elements = [
        Spacer(0, 6 * mm),
        top_row,
        Spacer(0, 6 * mm),
        *fields,
        Spacer(0, 10 * mm),
        table,
        Spacer(0, 18 * mm),
    ]

    def on_page(canvas, doc):
        width, height = A4

        # Top waves (approximation)
        canvas.saveState()
        canvas.setFillColor(colors.HexColor("#7fb3c9"))
        canvas.setStrokeColor(colors.HexColor("#7fb3c9"))
        p1 = canvas.beginPath()
        p1.moveTo(0, height)
        p1.curveTo(width * 0.25, height - 18 * mm, width * 0.55, height - 4 * mm, width, height - 20 * mm)
        p1.lineTo(width, height)
        p1.close()
        canvas.drawPath(p1, stroke=0, fill=1)

        canvas.setFillColor(colors.HexColor("#0b4a73"))
        canvas.setStrokeColor(colors.HexColor("#0b4a73"))
        p2 = canvas.beginPath()
        p2.moveTo(0, height)
        p2.curveTo(width * 0.25, height - 10 * mm, width * 0.55, height + 2 * mm, width, height - 10 * mm)
        p2.lineTo(width, height)
        p2.close()
        canvas.drawPath(p2, stroke=0, fill=1)
        canvas.restoreState()

        # Footer
        phone = (company.get("phone") or "").strip()
        email = (company.get("email") or "").strip()
        address = (company.get("address") or "").strip()
        city = (company.get("city") or "").strip()

        left_lines = []
        if phone:
            left_lines.append(phone)
        if email:
            left_lines.append(email)
        if address or city:
            left_lines.append(" · ".join([x for x in [address, city] if x]))

        canvas.saveState()
        canvas.setFillColor(colors.HexColor("#0b2a3b"))
        canvas.setFont("Helvetica", 9)
        y = 18 * mm
        for line in left_lines[:3]:
            canvas.drawString(15 * mm, y, line)
            y -= 4.5 * mm

        # Bottom-right brand text
        brand = (company.get("name") or "").strip()
        logo_path = (company.get("logo_path") or "").strip()
        if logo_path:
            try:
                # Draw logo above the brand text (approx template)
                logo_w = 16 * mm
                logo_h = 16 * mm
                logo_x = width - 15 * mm - logo_w
                logo_y = 12 * mm
                canvas.drawImage(
                    logo_path,
                    logo_x,
                    logo_y,
                    width=logo_w,
                    height=logo_h,
                    preserveAspectRatio=True,
                    mask='auto',
                )
            except Exception:
                pass
        if brand:
            canvas.setFont("Helvetica-Bold", 14)
            # When logo exists, keep brand text below it to avoid overlap.
            brand_y = 8 * mm if logo_path else 14 * mm
            canvas.drawRightString(width - 15 * mm, brand_y, brand[:24])
        canvas.restoreState()

    data["on_page"] = on_page
    return elements


def vat_by_rate_pdf_elements(data: dict, company: dict) -> list:
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        alignment=1,
        spaceAfter=6*mm,
    )
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=12,
        alignment=1,
        spaceAfter=12*mm,
    )
    elements = [
        Paragraph('IVA por Taxa', title_style),
        Paragraph(f"Período: {data['start_day']} a {data['end_day']} (Africa/Maputo)", subtitle_style),
        _company_info_table(company),
        Spacer(0, 6*mm),
        _table_from_list(['Taxa', 'Incidência', 'IVA', 'Total'], [
            [f"{r['tax_rate']:.2f}%", f"{r['net_total']:.2f}", f"{r['tax_total']:.2f}", f"{r['gross_total']:.2f}"]
            for r in data.get('rows', [])
        ], aligns=['RIGHT', 'RIGHT', 'RIGHT', 'RIGHT']),
    ]
    return elements


def sales_by_period_pdf_elements(data: dict, company: dict, start: date, end: date) -> list:
    currency = (company.get('currency') or '').strip()
    sales_count = int(data.get('sales_count', 0) or 0)
    disc_total = float(data.get('discount_total', 0) or 0)
    styles = getSampleStyleSheet()
    elements = [
        _header_block('Vendas por Período', f"Período: {start} a {end} (Africa/Maputo)", company),
        Spacer(0, 6*mm),
        _metric_cards([
            ('Vendas', str(sales_count)),
            ('Descontos', _fmt_money(disc_total, currency)),
            ('IVA', _fmt_money(data.get('tax_total', 0), currency)),
            ('Total', _fmt_money(data.get('gross_total', 0), currency)),
        ]),
        Spacer(0, 6*mm),
        _styled_table(
            ['Data', 'Pagamento', 'Estado', 'Canal', 'Líquido', 'IVA', 'Total'],
            [
                [
                    s['created_at'][:10],
                    _payment_label(s.get('payment_method')),
                    _status_label(s.get('status')),
                    _channel_label(s.get('sale_channel')),
                    _fmt_money(float(s.get('net_total', 0) or 0), currency),
                    _fmt_money(float(s.get('tax_total', 0) or 0), currency),
                    _fmt_money(float(s.get('gross_total', 0) or 0), currency),
                ]
                for s in data.get('sales', [])
            ],
            col_widths=[22 * mm, 26 * mm, 22 * mm, 22 * mm, 24 * mm, 18 * mm, 24 * mm],
            aligns=['LEFT', 'LEFT', 'LEFT', 'LEFT', 'RIGHT', 'RIGHT', 'RIGHT'],
        ),
    ]

    printer_rows = []
    for s in data.get('sales', []) or []:
        for pl in (s.get('printer_lines') or []):
            printer_name = " ".join([x for x in [pl.get('brand'), pl.get('model')] if x])
            serial = (pl.get('serial_number') or '').strip()
            counter = (pl.get('counter_type_name') or pl.get('counter_type_code') or '-').strip() if isinstance(pl.get('counter_type_name') or pl.get('counter_type_code'), str) else (pl.get('counter_type_name') or pl.get('counter_type_code') or '-')
            printer_rows.append(
                [
                    (s.get('created_at') or '')[:10],
                    f"{printer_name} ({serial})".strip() if (printer_name or serial) else '-',
                    counter or '-',
                    str(int(pl.get('copies') or 0)),
                    _fmt_money(float(pl.get('unit_price', 0) or 0), currency),
                    _fmt_money(float(pl.get('line_total', 0) or 0), currency),
                ]
            )

    if printer_rows:
        elements.extend(
            [
                Spacer(0, 8 * mm),
                Paragraph('Detalhes de Impressão', ParagraphStyle('secPrint', parent=styles['Normal'], fontSize=11, textColor=colors.HexColor('#e2e8f0'))),
                Spacer(0, 3 * mm),
                _styled_table(
                    ['Data', 'Impressora', 'Tipo', 'Cópias', 'Preço/Cópia', 'Total'],
                    printer_rows,
                    col_widths=[22 * mm, None, 26 * mm, 18 * mm, 26 * mm, 26 * mm],
                    aligns=['LEFT', 'LEFT', 'LEFT', 'RIGHT', 'RIGHT', 'RIGHT'],
                ),
            ]
        )
    return elements


def cash_closure_pdf_elements(data: dict, company: dict, user: dict, day: date) -> list:
    styles = getSampleStyleSheet()
    currency = (company.get('currency') or '').strip()
    op_name = (user.get('name') or user.get('username') or '-').strip() if isinstance(user, dict) else '-'
    elements = [
        _header_block('Fecho de Caixa', f"Data: {day} (Africa/Maputo) · Operador: {op_name}", company),
        Spacer(0, 6 * mm),
        _metric_cards([
            ('Vendas', str(int(data.get('sales_count', 0) or 0))),
            ('Líquido', _fmt_money(data.get('net_total', 0), currency)),
            ('IVA', _fmt_money(data.get('tax_total', 0), currency)),
            ('Total', _fmt_money(data.get('gross_total', 0), currency)),
        ]),
        Spacer(0, 6 * mm),
        _styled_table(
            ['Hora', 'Pagamento', 'Estado', 'Canal', 'Líquido', 'IVA', 'Total'],
            [
                [
                    (s.get('created_at') or '')[11:19] or '-',
                    _payment_label(s.get('payment_method')),
                    _status_label(s.get('status')),
                    _channel_label(s.get('sale_channel')),
                    _fmt_money(s.get('net_total', 0), currency),
                    _fmt_money(s.get('tax_total', 0), currency),
                    _fmt_money(s.get('gross_total', 0), currency),
                ]
                for s in data.get('sales', [])
            ],
            col_widths=[16 * mm, 30 * mm, 20 * mm, 20 * mm, None, 22 * mm, None],
            aligns=['LEFT', 'LEFT', 'LEFT', 'LEFT', 'RIGHT', 'RIGHT', 'RIGHT'],
        ),
    ]

    printer_rows = []
    for s in data.get('sales', []) or []:
        for pl in (s.get('printer_lines') or []):
            printer_name = " ".join([x for x in [pl.get('brand'), pl.get('model')] if x])
            serial = (pl.get('serial_number') or '').strip()
            counter = (pl.get('counter_type_name') or pl.get('counter_type_code') or '-').strip() if isinstance(pl.get('counter_type_name') or pl.get('counter_type_code'), str) else (pl.get('counter_type_name') or pl.get('counter_type_code') or '-')
            printer_rows.append(
                [
                    (s.get('created_at') or '')[11:19] or '-',
                    f"{printer_name} ({serial})".strip() if (printer_name or serial) else '-',
                    counter or '-',
                    str(int(pl.get('copies') or 0)),
                    _fmt_money(float(pl.get('unit_price', 0) or 0), currency),
                    _fmt_money(float(pl.get('line_total', 0) or 0), currency),
                ]
            )

    if printer_rows:
        elements.extend(
            [
                Spacer(0, 8 * mm),
                Paragraph('Detalhes de Impressão', ParagraphStyle('secPrint2', parent=styles['Normal'], fontSize=11, textColor=colors.HexColor('#e2e8f0'))),
                Spacer(0, 3 * mm),
                _styled_table(
                    ['Hora', 'Impressora', 'Tipo', 'Cópias', 'Preço/Cópia', 'Total'],
                    printer_rows,
                    col_widths=[16 * mm, None, 26 * mm, 18 * mm, 26 * mm, 26 * mm],
                    aligns=['LEFT', 'LEFT', 'LEFT', 'RIGHT', 'RIGHT', 'RIGHT'],
                ),
            ]
        )
    return elements

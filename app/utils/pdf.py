from datetime import date
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image


def render_pdf(title: str, elements: list, on_page=None) -> bytes:
    """Render a list of Platypus elements to PDF bytes using ReportLab."""
    buffer = BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=15*mm, leftMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
    if on_page is not None:
        pdf.build(elements, onFirstPage=on_page, onLaterPages=on_page)
    else:
        pdf.build(elements)
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


def _summary_grid(data: dict, currency: str = '') -> Table:
    grid_data = [
        ['Docs emitidos', str(data.get('docs_issued', 0))],
        ['Docs anulados', str(data.get('docs_cancelled', 0))],
        ['IVA', f"{data.get('tax_total', 0):.2f} {currency}".strip()],
        ['Total', f"{data.get('gross_total', 0):.2f} {currency}".strip()],
    ]
    table = Table(grid_data, colWidths=[40*mm, 40*mm], rowHeights=[12*mm]*4)
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    return table


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
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#334155')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#0b1220'), colors.HexColor('#0f172a')]),
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
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        alignment=1,  # center
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
        Paragraph('Fecho Diário (Z)', title_style),
        Paragraph(f"Data: {data['day']} (Africa/Maputo)", subtitle_style),
        _company_info_table(company),
        Spacer(0, 6*mm),
        _summary_grid(data, company.get('currency', '')),
        Spacer(0, 6*mm),
        Paragraph('Por tipo de documento', styles['Heading2']),
        Spacer(0, 3*mm),
        _table_from_list(['Tipo', 'Qtd', 'Total'], [
            [r['document_type'], str(r['count']), f"{r['gross_total']:.2f}"]
            for r in data.get('by_type', [])
        ], aligns=['LEFT', 'CENTER', 'RIGHT']),
        Spacer(0, 6*mm),
        Paragraph('IVA por taxa', styles['Heading2']),
        Spacer(0, 3*mm),
        _table_from_list(['Taxa', 'Incidência', 'IVA', 'Total'], [
            [f"{r['tax_rate']:.2f}%", f"{r['net_total']:.2f}", f"{r['tax_total']:.2f}", f"{r['gross_total']:.2f}"]
            for r in data.get('vat_by_rate', [])
        ], aligns=['RIGHT', 'RIGHT', 'RIGHT', 'RIGHT']),
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
        _header_block('Vendas por Período', f"Período: {start} a {end} (Africa/Maputo)", company),
        Spacer(0, 6*mm),
        _summary_grid({
            'docs_issued': data.get('sales_count', 0),
            'docs_cancelled': 0,
            'tax_total': data.get('tax_total', 0),
            'gross_total': data.get('gross_total', 0),
        }, company.get('currency', '')),
        Spacer(0, 6*mm),
        _styled_table(
            ['Data', 'Pagamento', 'Estado', 'Canal', 'Líquido', 'IVA', 'Total'],
            [
                [
                    s['created_at'][:10],
                    (s.get('payment_method') or '-'),
                    (s.get('status') or '-'),
                    (s.get('sale_channel') or '-'),
                    f"{float(s.get('net_total', 0)):.2f}",
                    f"{float(s.get('tax_total', 0)):.2f}",
                    f"{float(s.get('gross_total', 0)):.2f}",
                ]
                for s in data.get('sales', [])
            ],
            col_widths=[22 * mm, 26 * mm, 22 * mm, 22 * mm, 24 * mm, 18 * mm, 24 * mm],
            aligns=['LEFT', 'LEFT', 'LEFT', 'LEFT', 'RIGHT', 'RIGHT', 'RIGHT'],
        ),
    ]
    return elements


def cash_closure_pdf_elements(data: dict, company: dict, user: dict, day: date) -> list:
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
        Paragraph('Fecho de Caixa', title_style),
        Paragraph(f"Data: {day} (Africa/Maputo)", subtitle_style),
        Paragraph(f"Operador: {user.get('name', '-')}", styles['Normal']),
        Spacer(0, 3*mm),
        _company_info_table(company),
        Spacer(0, 6*mm),
        _summary_grid({
            'docs_issued': data.get('sales_count', 0),
            'docs_cancelled': 0,
            'tax_total': data.get('tax_total', 0),
            'gross_total': data.get('gross_total', 0),
        }, company.get('currency', '')),
        Spacer(0, 6*mm),
        _table_from_list(['Hora', 'Pagamento', 'Estado', 'Canal', 'Líquido', 'IVA', 'Total'], [
            [
                s['created_at'][11:19],
                s.get('payment_method', '-') or '-',
                s.get('status', '-') or '-',
                s.get('sale_channel', '-') or '-',
                f"{s['net_total']:.2f}",
                f"{s['tax_total']:.2f}",
                f"{s['gross_total']:.2f}",
            ]
            for s in data.get('sales', [])
        ], aligns=['LEFT', 'LEFT', 'LEFT', 'LEFT', 'RIGHT', 'RIGHT', 'RIGHT']),
    ]
    return elements

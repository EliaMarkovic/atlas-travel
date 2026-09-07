import os
import re
import io
from datetime import datetime, timedelta

def clean_html_for_reportlab(text: str) -> str:
    """
    Sanifica e pulisce il testo per evitare qualsiasi crash o syntax error
    durante la compilazione PDF in ReportLab.
    """
    if not text:
        return ""
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r'&lt;(/?(b|i|u|font|a|para))&gt;', r'<\1>', text)
    return text

def generate_pdf_itinerary(destination: str, itinerary_text: str) -> bytes:
    """
    Genera un PDF elegante garantendo la massima stabilità anche in presenza di testi complessi,
    inclusi blocchi dedicati a Logistica Trasporti, Alloggi e Stima Economica.
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
    except ImportError:
        raise RuntimeError("La libreria 'reportlab' non è installata. Esegui: py -m pip install reportlab")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'AtlasTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=22,
        textColor=colors.HexColor('#2D3A30'),
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        'AtlasSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        textColor=colors.HexColor('#B8860B'),
        spaceAfter=15
    )

    day_heading_style = ParagraphStyle(
        'AtlasDayHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=colors.HexColor('#2D3A30'),
        spaceBefore=14,
        spaceAfter=6
    )

    step_heading_style = ParagraphStyle(
        'AtlasStepHeader',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=11,
        textColor=colors.HexColor('#6B7C67'),
        spaceBefore=8,
        spaceAfter=4
    )

    body_style = ParagraphStyle(
        'AtlasBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor('#1E293B'),
        spaceAfter=6
    )

    highlight_box_style = ParagraphStyle(
        'AtlasHighlight',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor('#2D3A30'),
        spaceAfter=4
    )

    story = []

    safe_dest = clean_html_for_reportlab(destination.upper())
    story.append(Paragraph(f"🧭 ATLAS — {safe_dest}", title_style))
    story.append(Paragraph(f"Personal AI Travel Concierge — Itinerario Creato il {datetime.now().strftime('%d/%m/%Y')}", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#C5A059'), spaceAfter=15))

    clean_text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', itinerary_text)
    lines = clean_text.split('\n')

    in_special_section = False
    in_budget_section = False
    budget_lines = []

    for line in lines:
        line_s = line.strip()
        if not line_s:
            continue

        # Gestione sezione Logistica Trasporti
        if "LOGISTICA TRASPORTI" in line_s.upper() or "TRASPORTI & ARRIVO" in line_s.upper():
            in_special_section = True
            in_budget_section = False
            story.append(Spacer(1, 10))
            story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2D3A30'), spaceAfter=10))
            story.append(Paragraph("✈️ LOGISTICA TRASPORTI & ARRIVO", day_heading_style))
            continue

        # Gestione sezione Proposta Alloggi
        if "PROPOSTA ALLOGGI" in line_s.upper() or "PERNOTTAMENTI STRATEGICI" in line_s.upper():
            in_special_section = True
            in_budget_section = False
            story.append(Spacer(1, 10))
            story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#6B7C67'), spaceAfter=10))
            story.append(Paragraph("🏨 PROPOSTA ALLOGGI E PERNOTTAMENTI STRATEGICI", day_heading_style))
            continue

        # Gestione sezione Stima Economica
        if "STIMA ECONOMICA" in line_s.upper() or "BOX STIMA" in line_s.upper():
            in_budget_section = True
            in_special_section = False
            story.append(Spacer(1, 10))
            story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#C5A059'), spaceAfter=10))
            story.append(Paragraph("💰 STIMA ECONOMICA E TOTALE VIAGGIO", day_heading_style))
            continue

        if in_budget_section:
            budget_lines.append(line_s.replace('*', '').replace('#', '').strip())
        elif in_special_section:
            if line_s.startswith('## '):
                in_special_section = False
                story.append(Spacer(1, 8))
                title = clean_html_for_reportlab(line_s.replace('## ', '').strip())
                story.append(Paragraph(title, day_heading_style))
                story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#CBD5E1'), spaceAfter=6))
            else:
                formatted_line = clean_html_for_reportlab(line_s)
                formatted_line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', formatted_line)
                story.append(Paragraph(formatted_line, highlight_box_style))
        else:
            if line_s.startswith('## '):
                story.append(Spacer(1, 8))
                title = clean_html_for_reportlab(line_s.replace('## ', '').strip())
                story.append(Paragraph(title, day_heading_style))
                story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#CBD5E1'), spaceAfter=6))
            elif line_s.startswith('### '):
                step_title = clean_html_for_reportlab(line_s.replace('### ', '').strip())
                story.append(Paragraph(step_title, step_heading_style))
            elif line_s.startswith('- '):
                bullet_text = clean_html_for_reportlab(line_s.replace('- ', '• ').strip())
                story.append(Paragraph(bullet_text, body_style))
            else:
                formatted_line = clean_html_for_reportlab(line_s)
                formatted_line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', formatted_line)
                story.append(Paragraph(formatted_line, body_style))

    # Formattazione della Tabella Stima Economica
    if budget_lines:
        table_data = []
        for bl in budget_lines:
            bl_clean = clean_html_for_reportlab(bl)
            if ':' in bl_clean:
                parts = bl_clean.split(':', 1)
                k = parts[0].strip()
                v = parts[1].strip()
                
                if "TOTALE" in k.upper():
                    table_data.append([
                        Paragraph(f"<b>{k}</b>", body_style),
                        Paragraph(f"<b><font color='#2D3A30'>{v}</font></b>", body_style)
                    ])
                else:
                    table_data.append([
                        Paragraph(f"<b>{k}</b>", body_style),
                        Paragraph(v, body_style)
                    ])
            else:
                table_data.append([Paragraph(bl_clean, body_style), ""])

        if table_data:
            t = Table(table_data, colWidths=[220, 310])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F4F6F8')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1E293B')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ]))
            story.append(t)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

def generate_ics_calendar(destination: str, itinerary_text: str, start_date_str: str) -> str:
    ics_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Atlas Personal AI Concierge//IT",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH"
    ]
    
    try:
        base_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    except Exception:
        base_date = datetime.now()

    day_blocks = re.split(r'\n(?=##\s+Giorno|\n##\s+Day)', itinerary_text)
    
    for day_idx, block in enumerate(day_blocks):
        if not block.strip():
            continue
            
        current_date = base_date + timedelta(days=day_idx)
        step_matches = re.findall(r'###\s+([^:\n]+):\s*([^\n]+)', block)
        
        for fascia, titolo in step_matches:
            summary = f"Atlas: {titolo.strip()} ({destination})"
            description = f"Attività prevista per la fascia {fascia.strip()} a {destination}."
            
            start_hour = "090000"
            end_hour = "120000"
            if "pranzo" in fascia.lower():
                start_hour = "123000"
                end_hour = "143000"
            elif "pomeriggio" in fascia.lower():
                start_hour = "150000"
                end_hour = "180000"
            elif "sera" in fascia.lower() or "cena" in fascia.lower():
                start_hour = "193000"
                end_hour = "220000"

            dtstart = f"{current_date.strftime('%Y%m%d')}T{start_hour}"
            dtend = f"{current_date.strftime('%Y%m%d')}T{end_hour}"
            
            ics_lines.extend([
                "BEGIN:VEVENT",
                f"SUMMARY:{summary}",
                f"DESCRIPTION:{description}",
                f"LOCATION:{destination}",
                f"DTSTART:{dtstart}",
                f"DTEND:{dtend}",
                f"STATUS:CONFIRMED",
                "END:VEVENT"
            ])
            
    ics_lines.append("END:VCALENDAR")
    return "\n".join(ics_lines)

def save_itinerary_to_file(destination: str, itinerary_text: str):
    os.makedirs("data", exist_ok=True)
    safe_dest = "".join(c for c in destination if c.isalnum() or c in (' ', '_', '-')).strip().replace(' ', '_')
    if not safe_dest:
        safe_dest = "Viaggio"
        
    file_path = os.path.join("data", f"itinerary_{safe_dest}.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(itinerary_text)
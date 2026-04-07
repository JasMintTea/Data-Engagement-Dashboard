import io
from datetime import date

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    Image,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

# ── Brand colours ─────────────────────────────────────────────────────────────
NAVY   = colors.HexColor('#0D2B54')
BLUE   = colors.HexColor('#1A56A0')
GOLD   = colors.HexColor('#C8963E')
LIGHT  = colors.HexColor('#EEF3FA')
MUTED  = colors.HexColor('#6B7B8F')
WHITE  = colors.white
GREEN  = colors.HexColor('#1a6e34')
RED    = colors.HexColor('#C0392B')

W, H = A4


# ── Styles ────────────────────────────────────────────────────────────────────
def _styles():
    s = getSampleStyleSheet()
    base = dict(fontName='Helvetica', leading=14)

    def ps(name, **kw):
        return ParagraphStyle(name, **{**base, **kw})

    return {
        'cover_title':  ps('ct',  fontSize=28, textColor=WHITE,  alignment=TA_CENTER, leading=34, fontName='Helvetica-Bold'),
        'cover_sub':    ps('cs',  fontSize=14, textColor=GOLD,   alignment=TA_CENTER, leading=18),
        'cover_meta':   ps('cm',  fontSize=11, textColor=WHITE,  alignment=TA_CENTER, leading=16),
        'section':      ps('sec', fontSize=14, textColor=NAVY,   fontName='Helvetica-Bold', leading=18, spaceBefore=16, spaceAfter=6),
        'subsection':   ps('sub', fontSize=11, textColor=BLUE,   fontName='Helvetica-Bold', leading=14, spaceBefore=10, spaceAfter=4),
        'body':         ps('bod', fontSize=9,  textColor=colors.HexColor('#222222'), leading=13),
        'metric_val':   ps('mv',  fontSize=22, textColor=NAVY,   fontName='Helvetica-Bold', alignment=TA_CENTER, leading=26),
        'metric_lbl':   ps('ml',  fontSize=8,  textColor=MUTED,  alignment=TA_CENTER, leading=10, fontName='Helvetica'),
        'footer':       ps('ft',  fontSize=8,  textColor=MUTED,  alignment=TA_CENTER),
        'inst_name':    ps('in',  fontSize=10, textColor=NAVY,   fontName='Helvetica-Bold', leading=13),
        'inst_sub':     ps('is',  fontSize=8,  textColor=MUTED,  leading=11),
        'tbl_hdr':      ps('th',  fontSize=8,  textColor=WHITE,  fontName='Helvetica-Bold', alignment=TA_CENTER, leading=10),
        'tbl_cell':     ps('tc',  fontSize=8,  textColor=colors.HexColor('#222222'), alignment=TA_CENTER, leading=10),
        'tbl_cell_l':   ps('tcl', fontSize=8,  textColor=colors.HexColor('#222222'), alignment=TA_LEFT,   leading=10),
    }


# ── Chart helpers (matplotlib → PNG → ReportLab Image) ───────────────────────
def _fig_to_image(fig, width_cm=16):
    import matplotlib
    matplotlib.use('Agg')
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    buf.seek(0)
    import matplotlib.pyplot as plt
    plt.close(fig)
    img = Image(buf)
    img.drawWidth  = width_cm * cm
    img.drawHeight = img.drawWidth * (fig.get_figheight() / fig.get_figwidth())
    return img


def _bar_chart(labels, values, title, colour='#1A56A0', ylabel='Participants'):
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')

    fig, ax = plt.subplots(figsize=(10, 4))
    x = range(len(labels))
    bars = ax.bar(x, values, color=colour, width=0.55, zorder=3)
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, fontsize=9, rotation=20, ha='right')
    ax.set_ylabel(ylabel, fontsize=9, color='#6B7B8F')
    ax.set_title(title, fontsize=11, color='#0D2B54', fontweight='bold', pad=10)
    ax.yaxis.grid(True, linestyle='--', alpha=0.5, zorder=0)
    ax.set_axisbelow(True)
    ax.spines[['top', 'right', 'left']].set_visible(False)
    for bar, val in zip(bars, values):
        if val > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                    str(val), ha='center', va='bottom', fontsize=8, color='#0D2B54')
    fig.tight_layout()
    return fig


def _horizontal_bar_chart(labels, values, title, colour='#1A56A0'):
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')

    fig, ax = plt.subplots(figsize=(10, max(3, len(labels) * 0.5)))
    y = range(len(labels))
    bars = ax.barh(list(y), values, color=colour, height=0.55, zorder=3)
    ax.set_yticks(list(y))
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel('Completion %', fontsize=9, color='#6B7B8F')
    ax.set_title(title, fontsize=11, color='#0D2B54', fontweight='bold', pad=10)
    ax.xaxis.grid(True, linestyle='--', alpha=0.5, zorder=0)
    ax.set_axisbelow(True)
    ax.set_xlim(0, 110)
    ax.spines[['top', 'right', 'bottom']].set_visible(False)
    for bar, val in zip(bars, values):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                f'{val}%', va='center', fontsize=8, color='#0D2B54')
    fig.tight_layout()
    return fig


def _pie_chart(labels, values, title, colours=None):
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')

    if colours is None:
        colours = ['#1A56A0', '#C8963E', '#1a6e34', '#C0392B', '#6B7B8F']
    fig, ax = plt.subplots(figsize=(5, 4))
    wedges, texts, autotexts = ax.pie(
        values, labels=None, autopct='%1.1f%%',
        colors=colours[:len(values)], startangle=90,
        wedgeprops=dict(width=0.6, edgecolor='white', linewidth=2),
        pctdistance=0.75,
    )
    for t in autotexts:
        t.set_fontsize(8)
        t.set_color('white')
        t.set_fontweight('bold')
    ax.legend(wedges, labels, loc='lower center', bbox_to_anchor=(0.5, -0.15),
              ncol=2, fontsize=8, frameon=False)
    ax.set_title(title, fontsize=11, color='#0D2B54', fontweight='bold', pad=10)
    fig.tight_layout()
    return fig


def _grouped_bar_chart(groups, m_vals, f_vals, title):
    import matplotlib.pyplot as plt
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')

    x   = np.arange(len(groups))
    w   = 0.35
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(x - w/2, m_vals, w, label='Male',   color='#1A56A0', zorder=3)
    ax.bar(x + w/2, f_vals, w, label='Female', color='#C8963E', zorder=3)
    ax.set_xticks(x)
    ax.set_xticklabels(groups, fontsize=9)
    ax.set_ylabel('Participants', fontsize=9, color='#6B7B8F')
    ax.set_title(title, fontsize=11, color='#0D2B54', fontweight='bold', pad=10)
    ax.yaxis.grid(True, linestyle='--', alpha=0.5, zorder=0)
    ax.set_axisbelow(True)
    ax.spines[['top', 'right', 'left']].set_visible(False)
    ax.legend(fontsize=9, frameon=False)
    fig.tight_layout()
    return fig


# ── Page templates ────────────────────────────────────────────────────────────
def _cover_page_cb(canvas, doc):
    canvas.saveState()
    # Navy background
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, W, H, fill=1, stroke=0)
    # Gold accent bar
    canvas.setFillColor(GOLD)
    canvas.rect(0, H * 0.38, W, 6, fill=1, stroke=0)
    # Light band
    canvas.setFillColor(colors.HexColor('#EEF3FA'))
    canvas.rect(0, H * 0.38 - 180, W, 180, fill=1, stroke=0)
    canvas.restoreState()


def _page_cb(canvas, doc):
    canvas.saveState()
    # Header bar
    canvas.setFillColor(NAVY)
    canvas.rect(0, H - 1.2 * cm, W, 1.2 * cm, fill=1, stroke=0)
    canvas.setFillColor(GOLD)
    canvas.rect(0, H - 1.2 * cm - 3, W, 3, fill=1, stroke=0)
    # Header text
    canvas.setFont('Helvetica-Bold', 9)
    canvas.setFillColor(WHITE)
    canvas.drawString(1.5 * cm, H - 0.85 * cm, 'CariFin Data Engagement Dashboard')
    canvas.drawRightString(W - 1.5 * cm, H - 0.85 * cm, doc.title)
    # Footer
    canvas.setFont('Helvetica', 7)
    canvas.setFillColor(MUTED)
    canvas.drawString(1.5 * cm, 0.8 * cm, f'Generated {date.today().strftime("%d %B %Y")}')
    canvas.drawCentredString(W / 2, 0.8 * cm, 'CONFIDENTIAL')
    canvas.drawRightString(W - 1.5 * cm, 0.8 * cm, f'Page {doc.page}')
    # Footer line
    canvas.setStrokeColor(LIGHT)
    canvas.setLineWidth(1)
    canvas.line(1.5 * cm, 1.2 * cm, W - 1.5 * cm, 1.2 * cm)
    canvas.restoreState()


# ── Table style helpers ───────────────────────────────────────────────────────
def _inst_table_style():
    return TableStyle([
        ('BACKGROUND',  (0, 0), (-1, 0),  NAVY),
        ('TEXTCOLOR',   (0, 0), (-1, 0),  WHITE),
        ('FONTNAME',    (0, 0), (-1, 0),  'Helvetica-Bold'),
        ('FONTSIZE',    (0, 0), (-1, 0),  8),
        ('FONTSIZE',    (0, 1), (-1, -1), 8),
        ('ALIGN',       (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN',       (0, 1), (0, -1),  'LEFT'),
        ('VALIGN',      (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT]),
        ('GRID',        (0, 0), (-1, -1), 0.3, colors.HexColor('#D0D8E4')),
        ('TOPPADDING',  (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('ROUNDEDCORNERS', [3]),
    ])


# ── Metric card row ───────────────────────────────────────────────────────────
def _metric_row(metrics, styles):
    """metrics = [(value, label), ...]"""
    n   = len(metrics)
    col = W / n - 2 * cm / n
    cells = []
    for val, lbl in metrics:
        cells.append([
            Paragraph(str(val), styles['metric_val']),
            Paragraph(lbl,      styles['metric_lbl']),
        ])
    t = Table([cells], colWidths=[col] * n)
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), LIGHT),
        ('BOX',           (0, 0), (-1, -1), 0.5, colors.HexColor('#D0D8E4')),
        ('INNERGRID',     (0, 0), (-1, -1), 0.5, colors.HexColor('#D0D8E4')),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    return t


# ── Main report builder ───────────────────────────────────────────────────────
def generate_season_report(season, institution_stats, stage_completion,
                           participation_by_inst, status_breakdown,
                           stage_funnel, gender_split, age_groups,
                           filter_inst=None):
    """
    Returns a bytes object containing the PDF.
    All data arguments are the same structures already used by the dashboard.
    """
    buf    = io.BytesIO()
    st     = _styles()
    margin = 1.5 * cm

    inst_label = f' — {filter_inst}' if filter_inst else ' — All Institutions'
    doc_title  = f'Season {season.year} Report{inst_label}'

    doc = BaseDocTemplate(
        buf, pagesize=A4,
        leftMargin=margin, rightMargin=margin,
        topMargin=2 * cm, bottomMargin=1.8 * cm,
        title=doc_title,
    )
    doc.title = doc_title

    # Page templates
    cover_frame  = Frame(0, 0, W, H, leftPadding=2*cm, rightPadding=2*cm,
                         topPadding=0, bottomPadding=0)
    body_frame   = Frame(margin, 1.8*cm, W - 2*margin, H - 3.2*cm,
                         leftPadding=0, rightPadding=0,
                         topPadding=0.3*cm, bottomPadding=0)

    doc.addPageTemplates([
        PageTemplate(id='Cover', frames=[cover_frame], onPage=_cover_page_cb),
        PageTemplate(id='Body',  frames=[body_frame],  onPage=_page_cb),
    ])

    story = []

    # ══════════════════════════════════════════════════════════════════════════
    # COVER PAGE
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Spacer(1, H * 0.12))
    story.append(Paragraph('CariFin', ParagraphStyle(
        'logo', fontSize=36, textColor=GOLD, alignment=TA_CENTER,
        fontName='Helvetica-Bold', leading=40)))
    story.append(Paragraph('Data Engagement Dashboard', ParagraphStyle(
        'tagline', fontSize=13, textColor=colors.HexColor('#A8BFDA'),
        alignment=TA_CENTER, leading=16)))
    story.append(Spacer(1, 0.8 * cm))
    story.append(HRFlowable(width='60%', thickness=2, color=GOLD,
                             hAlign='CENTER', spaceAfter=0.8*cm))
    story.append(Paragraph(f'Season {season.year}', st['cover_title']))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph('Annual Participation Report', st['cover_sub']))
    story.append(Spacer(1, 0.5 * cm))

    # Stats band (white background area)
    total_p  = sum(i['participants']    for i in institution_stats)
    total_r  = sum(i['registrations']  for i in institution_stats)
    total_pa = sum(i['participated']   for i in institution_stats)
    avg_rate = round(total_pa / total_r * 100, 1) if total_r else 0

    cover_stats = Table([[
        Paragraph(str(total_p),  ParagraphStyle('cv', fontSize=28, textColor=NAVY, fontName='Helvetica-Bold', alignment=TA_CENTER)),
        Paragraph(str(total_r),  ParagraphStyle('cv', fontSize=28, textColor=NAVY, fontName='Helvetica-Bold', alignment=TA_CENTER)),
        Paragraph(f'{avg_rate}%', ParagraphStyle('cv', fontSize=28, textColor=NAVY, fontName='Helvetica-Bold', alignment=TA_CENTER)),
        Paragraph(str(len(institution_stats)), ParagraphStyle('cv', fontSize=28, textColor=NAVY, fontName='Helvetica-Bold', alignment=TA_CENTER)),
    ], [
        Paragraph('Participants', ParagraphStyle('cl', fontSize=9, textColor=MUTED, alignment=TA_CENTER)),
        Paragraph('Registered',   ParagraphStyle('cl', fontSize=9, textColor=MUTED, alignment=TA_CENTER)),
        Paragraph('Part. Rate',   ParagraphStyle('cl', fontSize=9, textColor=MUTED, alignment=TA_CENTER)),
        Paragraph('Institutions', ParagraphStyle('cl', fontSize=9, textColor=MUTED, alignment=TA_CENTER)),
    ]], colWidths=[(W - 4*cm)/4]*4)
    cover_stats.setStyle(TableStyle([
        ('TOPPADDING',    (0, 0), (-1, -1), 14),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
        ('INNERGRID',     (0, 0), (-1, -1), 0.5, colors.HexColor('#D0D8E4')),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(cover_stats)
    story.append(Spacer(1, 1.2 * cm))

    reg_open  = season.reg_open.strftime('%d %b %Y')  if season.reg_open  else 'N/A'
    reg_close = season.reg_close.strftime('%d %b %Y') if season.reg_close else 'N/A'
    s_start   = season.start_date.strftime('%d %b %Y') if season.start_date else 'N/A'
    s_end     = season.end_date.strftime('%d %b %Y')   if season.end_date   else 'N/A'

    story.append(Paragraph(
        f'Registration: {reg_open} – {reg_close} &nbsp;&nbsp;|&nbsp;&nbsp; '
        f'Season: {s_start} – {s_end} &nbsp;&nbsp;|&nbsp;&nbsp; '
        f'Status: {(season.status or "").capitalize()}',
        st['cover_meta']))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(
        f'Generated {date.today().strftime("%d %B %Y")}',
        ParagraphStyle('gen', fontSize=9, textColor=colors.HexColor('#A8BFDA'), alignment=TA_CENTER)))

    story.append(NextPageTemplate('Body'))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 2 — EXECUTIVE SUMMARY
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph('Executive Summary', st['section']))
    story.append(HRFlowable(width='100%', thickness=1, color=BLUE, spaceAfter=12))

    participated  = status_breakdown.get('participated', 0)
    no_show       = status_breakdown.get('no_show', 0) + status_breakdown.get('pending', 0)
    part_rate_pct = round(participated / (participated + no_show) * 100, 1) if (participated + no_show) else 0

    story.append(_metric_row([
        (total_p,         'Total Participants'),
        (total_r,         'Total Registered'),
        (participated,    'Participated'),
        (no_show,         'No-Show / Pending'),
        (f'{part_rate_pct}%', 'Participation Rate'),
    ], st))
    story.append(Spacer(1, 0.5 * cm))

    # Institution summary table
    story.append(Paragraph('Participation by Institution', st['subsection']))
    tbl_data = [[
        Paragraph('Institution',      st['tbl_hdr']),
        Paragraph('Participants',     st['tbl_hdr']),
        Paragraph('Registered',       st['tbl_hdr']),
        Paragraph('Participated',     st['tbl_hdr']),
        Paragraph('Part. Rate',       st['tbl_hdr']),
        Paragraph('HR Users',         st['tbl_hdr']),
    ]]
    for i in sorted(institution_stats, key=lambda x: x['participants'], reverse=True):
        rate_color = GREEN if i['participation_rate'] >= 70 else (GOLD if i['participation_rate'] >= 40 else RED)
        tbl_data.append([
            Paragraph(i['name'],                        st['tbl_cell_l']),
            Paragraph(str(i['participants']),           st['tbl_cell']),
            Paragraph(str(i['registrations']),          st['tbl_cell']),
            Paragraph(str(i['participated']),           st['tbl_cell']),
            Paragraph(f"{i['participation_rate']}%",   ParagraphStyle('rate', fontSize=8, textColor=rate_color, alignment=TA_CENTER, fontName='Helvetica-Bold')),
            Paragraph(str(i['user_count']),             st['tbl_cell']),
        ])
    col_w = [(W - 3*cm) * x for x in [0.30, 0.14, 0.14, 0.14, 0.14, 0.14]]
    tbl = Table(tbl_data, colWidths=col_w, repeatRows=1)
    tbl.setStyle(_inst_table_style())
    story.append(tbl)
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 3 — PARTICIPATION CHARTS
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph('Participation Analytics', st['section']))
    story.append(HRFlowable(width='100%', thickness=1, color=BLUE, spaceAfter=12))

    # Bar chart — participation by institution
    if participation_by_inst:
        story.append(Paragraph('Participants by Institution', st['subsection']))
        labels = [r['code'] for r in participation_by_inst]
        values = [r['count'] for r in participation_by_inst]
        fig = _bar_chart(labels, values, 'Registered Participants per Institution')
        story.append(_fig_to_image(fig, width_cm=16))
        story.append(Spacer(1, 0.4 * cm))

    # Participation status pie chart
    if participated + no_show > 0:
        story.append(Paragraph('Participation Status', st['subsection']))
        pie_labels = ['Participated', 'No-Show / Pending']
        pie_vals   = [participated, no_show]
        pie_cols   = ['#1a6e34', '#C0392B']
        fig = _pie_chart(pie_labels, pie_vals, 'Participation Status Breakdown', pie_cols)
        story.append(_fig_to_image(fig, width_cm=10))
        story.append(Spacer(1, 0.4 * cm))

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 4 — STAGE & FUNNEL ANALYSIS
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph('Stage & Funnel Analysis', st['section']))
    story.append(HRFlowable(width='100%', thickness=1, color=BLUE, spaceAfter=12))

    if stage_completion:
        story.append(Paragraph('Stage Completion Rates', st['subsection']))
        s_labels = [f'Stage {s["stage"]}' for s in stage_completion]
        s_vals   = [s['completion'] for s in stage_completion]
        fig = _horizontal_bar_chart(s_labels, s_vals, 'Stage Completion (%)', colour='#1A56A0')
        story.append(_fig_to_image(fig, width_cm=14))
        story.append(Spacer(1, 0.3 * cm))

        # Stage completion table
        sc_data = [[
            Paragraph('Stage',      st['tbl_hdr']),
            Paragraph('Completed',  st['tbl_hdr']),
            Paragraph('Total',      st['tbl_hdr']),
            Paragraph('Rate',       st['tbl_hdr']),
        ]]
        for s in stage_completion:
            sc_data.append([
                Paragraph(f'Stage {s["stage"]}', st['tbl_cell']),
                Paragraph(str(s['completed']),   st['tbl_cell']),
                Paragraph(str(s['total']),        st['tbl_cell']),
                Paragraph(f'{s["completion"]}%', st['tbl_cell']),
            ])
        sc_tbl = Table(sc_data, colWidths=[(W-3*cm)/4]*4, repeatRows=1)
        sc_tbl.setStyle(_inst_table_style())
        story.append(sc_tbl)
        story.append(Spacer(1, 0.4 * cm))

    if stage_funnel and stage_funnel.get('stages'):
        story.append(Paragraph('Stage Drop-off Funnel', st['subsection']))
        f_labels = [s['label'] for s in stage_funnel['stages']]
        f_vals   = [s['count'] for s in stage_funnel['stages']]
        fig = _bar_chart(f_labels, f_vals,
                         f'Funnel — {stage_funnel.get("event_name","Event")} '
                         f'(Total Registered: {stage_funnel.get("total_registered",0)})',
                         colour='#C8963E', ylabel='Completions')
        story.append(_fig_to_image(fig, width_cm=16))

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 5 — DEMOGRAPHICS
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph('Demographic Analysis', st['section']))
    story.append(HRFlowable(width='100%', thickness=1, color=BLUE, spaceAfter=12))

    if gender_split:
        story.append(Paragraph('Gender Split', st['subsection']))
        g_labels = [g['sex'] for g in gender_split]
        g_vals   = [g['count'] for g in gender_split]
        g_cols   = ['#1A56A0', '#C8963E']
        fig = _pie_chart(g_labels, g_vals, 'Participants by Gender', g_cols)
        story.append(_fig_to_image(fig, width_cm=9))
        story.append(Spacer(1, 0.4 * cm))

    if age_groups:
        story.append(Paragraph('Age Group Distribution', st['subsection']))
        groups = [g['group'] for g in age_groups]
        m_vals = [g.get('M', 0) for g in age_groups]
        f_vals = [g.get('F', 0) for g in age_groups]
        fig = _grouped_bar_chart(groups, m_vals, f_vals, 'Participants by Age Group & Gender')
        story.append(_fig_to_image(fig, width_cm=16))
        story.append(Spacer(1, 0.3 * cm))

        # Age group table
        ag_data = [[
            Paragraph('Age Group', st['tbl_hdr']),
            Paragraph('Male',      st['tbl_hdr']),
            Paragraph('Female',    st['tbl_hdr']),
            Paragraph('Total',     st['tbl_hdr']),
        ]]
        for g in age_groups:
            ag_data.append([
                Paragraph(g['group'],          st['tbl_cell']),
                Paragraph(str(g.get('M', 0)),  st['tbl_cell']),
                Paragraph(str(g.get('F', 0)),  st['tbl_cell']),
                Paragraph(str(g['total']),     st['tbl_cell']),
            ])
        ag_tbl = Table(ag_data, colWidths=[(W-3*cm)/4]*4, repeatRows=1)
        ag_tbl.setStyle(_inst_table_style())
        story.append(ag_tbl)

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 6+ — PER-INSTITUTION DETAIL
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph('Institution Detail Pages', st['section']))
    story.append(HRFlowable(width='100%', thickness=1, color=BLUE, spaceAfter=6))
    story.append(Paragraph(
        'The following pages provide a detailed breakdown for each participating institution.',
        st['body']))
    story.append(Spacer(1, 0.4 * cm))

    for inst in sorted(institution_stats, key=lambda x: x['name']):
        if inst['participants'] == 0:
            continue

        story.append(Paragraph(inst['name'], st['inst_name']))
        story.append(Paragraph(f"Code: {inst['code']}", st['inst_sub']))
        story.append(Spacer(1, 0.2 * cm))

        story.append(_metric_row([
            (inst['participants'],         'Participants'),
            (inst['registrations'],        'Registered'),
            (inst['participated'],         'Participated'),
            (f"{inst['participation_rate']}%", 'Part. Rate'),
            (inst['user_count'],           'HR Users'),
        ], st))
        story.append(Spacer(1, 0.5 * cm))

        # Mini stage completion for this institution (from stage_completion if available)
        if stage_completion:
            sc_labels = [f'Stage {s["stage"]}' for s in stage_completion]
            sc_vals   = [s['completion'] for s in stage_completion]
            fig = _horizontal_bar_chart(
                sc_labels, sc_vals,
                f'Stage Completion — {inst["name"]}', colour='#1A56A0')
            story.append(_fig_to_image(fig, width_cm=13))

        story.append(HRFlowable(width='100%', thickness=0.5,
                                 color=colors.HexColor('#D0D8E4'), spaceAfter=10))

    # ══════════════════════════════════════════════════════════════════════════
    # FINAL PAGE — NOTES
    # ══════════════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(Paragraph('Notes & Methodology', st['section']))
    story.append(HRFlowable(width='100%', thickness=1, color=BLUE, spaceAfter=12))
    notes = [
        'Participation Rate is calculated as the number of participants with at least one recorded result divided by the total number of registered participants.',
        'No-Show / Pending includes participants registered but with no result recorded. If the event end date has not yet passed, these are counted as Pending.',
        'Stage Completion reflects the percentage of registered participants who completed each stage of the Urban Challenge.',
        'Age group data is derived from the division field (e.g. M3039 = Male, 30–39 age band).',
        'Data is sourced directly from the CariFin Data Engagement Dashboard database and reflects the state at the time of report generation.',
    ]
    for i, note in enumerate(notes, 1):
        story.append(Paragraph(f'{i}.  {note}', st['body']))
        story.append(Spacer(1, 0.3 * cm))

    doc.build(story)
    buf.seek(0)
    return buf.read()
from __future__ import annotations

from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from trustestate.config import APP_FULL_NAME, DISCLAIMER
from trustestate.risk_engine import CHECKS


def build_due_diligence_pdf(
    case: dict[str, Any], statuses: dict[str, str], result: dict[str, Any]
) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title=f"Due diligence report - {case.get('title', 'Property')}",
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CenteredTitle", parent=styles["Title"], alignment=TA_CENTER, textColor=colors.HexColor("#123047")))
    styles.add(ParagraphStyle(name="Small", parent=styles["BodyText"], fontSize=8.5, leading=11))
    story = [
        Paragraph(APP_FULL_NAME, styles["CenteredTitle"]),
        Paragraph("Property / Land Due-Diligence Decision Report", styles["Heading2"]),
        Spacer(1, 5 * mm),
    ]
    summary = [
        ["Property", case.get("title", "")],
        ["City / State", f"{case.get('city', '')} / {case.get('state', '')}"],
        ["Survey number", case.get("survey_number", "") or "Not supplied"],
        ["Coordinates", f"{case.get('latitude', '')}, {case.get('longitude', '')}"],
        ["Observed risk", f"{result['risk_score']}/100 - {result['risk_band']}"],
        ["Completion", f"{result['verified_count']}/{result['total_checks']} checks verified"],
    ]
    table = Table(summary, colWidths=[42 * mm, 120 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EAF2F8")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#9FB3C8")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.extend([table, Spacer(1, 5 * mm), Paragraph(result["decision"], styles["Heading3"])])

    if result["blockers"]:
        story.append(Paragraph("Critical blockers", styles["Heading2"]))
        for blocker in result["blockers"]:
            story.append(Paragraph(f"• {blocker}", styles["BodyText"]))

    story.extend([Spacer(1, 3 * mm), Paragraph("Verification checklist", styles["Heading2"])])
    rows = [["Category", "Check", "Status", "Evidence to obtain"]]
    for check in CHECKS:
        rows.append([
            check.category,
            Paragraph(check.label, styles["Small"]),
            statuses.get(check.key, "Pending"),
            Paragraph(check.evidence, styles["Small"]),
        ])
    checks_table = Table(rows, repeatRows=1, colWidths=[25 * mm, 56 * mm, 24 * mm, 58 * mm])
    checks_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#123047")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#AAB7B8")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F9F9")]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.extend([checks_table, Spacer(1, 5 * mm), Paragraph("Important limitation", styles["Heading2"]), Paragraph(DISCLAIMER, styles["Small"])])
    doc.build(story)
    return buffer.getvalue()

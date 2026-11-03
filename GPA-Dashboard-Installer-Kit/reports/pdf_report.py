"""Professional PDF academic report built with ReportLab."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from core.calculator import AcademicOverview, build_overview, quality_points
from core.grading import classify_gpa
from utils.helpers import APP_NAME, format_credits, format_gpa, today_text

NAVY = colors.HexColor("#1e1b4b")
ACCENT = colors.HexColor("#4f46e5")
LIGHT = colors.HexColor("#eef2ff")
ZEBRA = colors.HexColor("#f8fafc")
GRID = colors.HexColor("#cbd5e1")
MUTED = colors.HexColor("#64748b")

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 20 * mm
CONTENT_WIDTH = PAGE_WIDTH - 2 * MARGIN


class ReportError(Exception):
    """The PDF could not be created (message is user friendly)."""


class _NumberedCanvas(canvas.Canvas):
    """Canvas that draws the header band and a 'Page X of Y' footer."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._saved_states: list[dict[str, Any]] = []

    def showPage(self) -> None:  # noqa: N802 (ReportLab API name)
        self._saved_states.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        total = len(self._saved_states)
        for state in self._saved_states:
            self.__dict__.update(state)
            self._draw_chrome(total)
            super().showPage()
        super().save()

    def _draw_chrome(self, total_pages: int) -> None:
        self.setFillColor(NAVY)
        self.rect(0, PAGE_HEIGHT - 12 * mm, PAGE_WIDTH, 12 * mm, stroke=0, fill=1)
        self.setFillColor(colors.white)
        self.setFont("Helvetica-Bold", 9)
        self.drawString(MARGIN, PAGE_HEIGHT - 7.5 * mm, "STUDENT ACADEMIC REPORT")
        self.setFont("Helvetica", 9)
        self.drawRightString(PAGE_WIDTH - MARGIN, PAGE_HEIGHT - 7.5 * mm, APP_NAME)

        self.setStrokeColor(GRID)
        self.setLineWidth(0.6)
        self.line(MARGIN, 14 * mm, PAGE_WIDTH - MARGIN, 14 * mm)
        self.setFillColor(MUTED)
        self.setFont("Helvetica", 8)
        self.drawString(MARGIN, 9.5 * mm, f"Generated on {today_text()}")
        self.drawRightString(
            PAGE_WIDTH - MARGIN, 9.5 * mm, f"Page {self._pageNumber} of {total_pages}"
        )


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()["Normal"]
    return {
        "title": ParagraphStyle("title", parent=base, fontName="Helvetica-Bold",
                                fontSize=24, leading=28, textColor=NAVY),
        "subtitle": ParagraphStyle("subtitle", parent=base, fontSize=10,
                                   textColor=MUTED, spaceAfter=4),
        "heading": ParagraphStyle("heading", parent=base, fontName="Helvetica-Bold",
                                  fontSize=13, leading=16, textColor=NAVY,
                                  spaceBefore=14, spaceAfter=4, keepWithNext=1),
        "sem_heading": ParagraphStyle("sem_heading", parent=base,
                                      fontName="Helvetica-Bold", fontSize=11,
                                      leading=14, textColor=ACCENT, spaceBefore=10,
                                      spaceAfter=4, keepWithNext=1),
        "cell": ParagraphStyle("cell", parent=base, fontSize=9, leading=11),
        "note": ParagraphStyle("note", parent=base, fontSize=9, textColor=MUTED),
        "kpi_label": ParagraphStyle("kpi_label", parent=base, fontSize=8,
                                    textColor=MUTED, alignment=TA_CENTER),
        "kpi_value": ParagraphStyle("kpi_value", parent=base, fontName="Helvetica-Bold",
                                    fontSize=17, leading=20, textColor=NAVY,
                                    alignment=TA_CENTER),
    }


def _text(value: str, fallback: str = "-") -> str:
    return escape(value) if value else fallback


def _heading(text: str, styles: dict[str, ParagraphStyle]) -> list[Any]:
    return [
        Paragraph(text, styles["heading"]),
        HRFlowable(width="100%", thickness=0.8, color=ACCENT, spaceAfter=6),
    ]


def _student_table(overview: AcademicOverview, styles: dict[str, ParagraphStyle]) -> Table:
    student = overview.student
    rows = [
        ("Student Name", student.get("name", "")),
        ("Student ID", student.get("student_id", "")),
        ("Program", student.get("program", "")),
        ("University", student.get("university", "")),
        ("Department", student.get("department", "")),
    ]
    data = [
        [Paragraph(f"<b>{label}</b>", styles["cell"]),
         Paragraph(_text(value), styles["cell"])]
        for label, value in rows
    ]
    table = Table(data, colWidths=[45 * mm, CONTENT_WIDTH - 45 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LIGHT),
        ("GRID", (0, 0), (-1, -1), 0.5, GRID),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return table


def _summary_table(overview: AcademicOverview, styles: dict[str, ParagraphStyle]) -> Table:
    items = [
        ("CGPA", f"{format_gpa(overview.cgpa)} / 4.00"),
        ("TOTAL CREDITS", format_credits(overview.total_credits)),
        ("TOTAL SEMESTERS", str(overview.semester_count)),
        ("CLASSIFICATION", classify_gpa(overview.cgpa)),
    ]
    data = [
        [Paragraph(label, styles["kpi_label"]) for label, _ in items],
        [Paragraph(value, styles["kpi_value"]) for _, value in items],
    ]
    table = Table(data, colWidths=[CONTENT_WIDTH / 4] * 4)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.8, ACCENT),
        ("LINEAFTER", (0, 0), (-2, -1), 0.5, GRID),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return table


def _grid_style(header_rows: int = 1, total_row: bool = False) -> TableStyle:
    commands = [
        ("BACKGROUND", (0, 0), (-1, header_rows - 1), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, header_rows - 1), colors.white),
        ("FONTNAME", (0, 0), (-1, header_rows - 1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (2, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, GRID),
        ("ROWBACKGROUNDS", (0, header_rows), (-1, -1), [colors.white, ZEBRA]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    if total_row:
        commands += [
            ("BACKGROUND", (0, -1), (-1, -1), LIGHT),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ]
    return TableStyle(commands)


def _semester_summary_table(overview: AcademicOverview) -> Table:
    data = [["Semester", "Academic Year", "Credits", "Quality Points", "SGPA"]]
    for s in overview.summaries:
        data.append([
            s.name[:40], s.academic_year, format_credits(s.credits),
            f"{s.quality_points:.2f}", format_gpa(s.sgpa),
        ])
    table = Table(
        data, repeatRows=1,
        colWidths=[62 * mm, 32 * mm, 22 * mm, 30 * mm, 24 * mm],
    )
    table.setStyle(_grid_style())
    table.setStyle(TableStyle([("ALIGN", (1, 0), (1, -1), "CENTER")]))
    return table


def _semester_detail(summary: Any, semester: Mapping[str, Any],
                     styles: dict[str, ParagraphStyle]) -> list[Any]:
    title = (f"{escape(summary.name)} ({escape(summary.academic_year)}) "
             f"- SGPA {format_gpa(summary.sgpa)}")
    parts: list[Any] = [Paragraph(title, styles["sem_heading"])]
    subjects = semester["subjects"]
    if not subjects:
        parts.append(Paragraph("No subjects recorded for this semester.", styles["note"]))
        return parts

    data: list[list[Any]] = [
        ["Subject", "Code", "Credits", "Grade", "Grade Point", "Quality Points"]
    ]
    for subject in subjects:
        points = quality_points(subject["credit_hours"], subject["grade_point"])
        data.append([
            Paragraph(escape(subject["subject_name"]), styles["cell"]),
            subject["subject_code"] or "-",
            format_credits(subject["credit_hours"]),
            subject["grade"],
            f"{subject['grade_point']:.2f}",
            f"{points:.2f}",
        ])
    data.append([
        "Semester total", "", format_credits(summary.credits), "",
        f"SGPA {format_gpa(summary.sgpa)}", f"{summary.quality_points:.2f}",
    ])
    table = Table(
        data, repeatRows=1,
        colWidths=[58 * mm, 24 * mm, 20 * mm, 18 * mm, 24 * mm, 26 * mm],
    )
    table.setStyle(_grid_style(total_row=True))
    table.setStyle(TableStyle([("ALIGN", (1, 0), (1, -1), "CENTER")]))
    parts.append(table)
    return parts


def _performance_table(overview: AcademicOverview) -> Table | None:
    stats = overview.stats
    if stats is None:
        return None
    rows = [
        ("Highest SGPA", f"{format_gpa(stats.highest.sgpa)}  ({stats.highest.name})"),
        ("Lowest SGPA", f"{format_gpa(stats.lowest.sgpa)}  ({stats.lowest.name})"),
        ("Average SGPA", format_gpa(stats.average_sgpa)),
        ("Final CGPA", f"{format_gpa(stats.cgpa)} / 4.00  ({classify_gpa(stats.cgpa)})"),
    ]
    table = Table(rows, colWidths=[55 * mm, CONTENT_WIDTH - 55 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LIGHT),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, GRID),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def generate_pdf_report(path: str | Path, snapshot: Mapping[str, Any]) -> None:
    """Create the academic report PDF at ``path``.

    Raises:
        ReportError: if the PDF could not be written.
    """
    try:
        overview = build_overview(snapshot)
        styles = _styles()
        doc = SimpleDocTemplate(
            str(path), pagesize=A4,
            leftMargin=MARGIN, rightMargin=MARGIN,
            topMargin=22 * mm, bottomMargin=22 * mm,
            title="Student Academic Report", author=APP_NAME,
        )

        story: list[Any] = [
            Paragraph("STUDENT ACADEMIC REPORT", styles["title"]),
            Paragraph(f"Generated on {today_text()}", styles["subtitle"]),
            HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceAfter=4),
        ]
        story += _heading("Student Information", styles)
        story.append(_student_table(overview, styles))
        story += _heading("Academic Summary", styles)
        story.append(_summary_table(overview, styles))

        story += _heading("Semester Summary", styles)
        if overview.summaries:
            story.append(_semester_summary_table(overview))
        else:
            story.append(Paragraph("No semesters have been recorded yet.", styles["note"]))

        if overview.summaries:
            story += _heading("Detailed Subjects", styles)
            semester_by_number = {s["semester_number"]: s for s in snapshot["semesters"]}
            for summary in overview.summaries:
                story += _semester_detail(summary, semester_by_number[summary.number], styles)
                story.append(Spacer(1, 4))

        performance = _performance_table(overview)
        if performance is not None:
            story += _heading("Performance Summary", styles)
            story.append(performance)

        doc.build(story, canvasmaker=_NumberedCanvas)
    except OSError as exc:
        raise ReportError(f"Could not save the PDF: {exc.strerror or exc}") from exc
    except Exception as exc:  # noqa: BLE001 - ReportLab can raise many error types
        raise ReportError(f"Could not generate the PDF report: {exc}") from exc

"""Reports page: PDF academic report and CSV export."""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Any

from database.database import DatabaseError
from reports.pdf_report import ReportError, generate_pdf_report
from ui.widgets import PAD, BasePage, Card, Tooltip
from utils.export import FileOperationError, export_csv
from utils.helpers import open_file


class ReportsPage(BasePage):
    def __init__(self, parent: tk.Misc, app: Any) -> None:
        super().__init__(parent, app)
        self.columnconfigure(0, weight=1)
        self.build_header(self, "Reports",
                          "Create a printable academic report or export your data.")

        pdf_card = Card(self, padding=22)
        pdf_card.grid(row=1, column=0, sticky="ew", padx=PAD, pady=(0, 14))
        ttk.Label(pdf_card, text="PDF Academic Report", style="Heading.TLabel").pack(anchor="w")
        ttk.Label(pdf_card, style="CardMuted.TLabel", justify="left", text=(
            "Includes your student information, academic summary, semester summary,\n"
            "detailed subjects for every semester and a performance summary."
        )).pack(anchor="w", pady=(4, 14))
        pdf_button = ttk.Button(pdf_card, text="\U0001F4C4 Generate PDF Report",
                                style="Accent.TButton", command=self.generate_pdf)
        pdf_button.pack(anchor="w")
        Tooltip(pdf_button, "Choose where to save Student_Academic_Report.pdf")

        csv_card = Card(self, padding=22)
        csv_card.grid(row=2, column=0, sticky="ew", padx=PAD, pady=(0, 14))
        ttk.Label(csv_card, text="CSV Export", style="Heading.TLabel").pack(anchor="w")
        ttk.Label(csv_card, style="CardMuted.TLabel", justify="left", text=(
            "One row per subject: semester, academic year, subject, code, credit hours,\n"
            "grade, grade point and quality points. Opens in Excel or Google Sheets."
        )).pack(anchor="w", pady=(4, 14))
        csv_button = ttk.Button(csv_card, text="Export CSV", command=self.export_csv)
        csv_button.pack(anchor="w")
        Tooltip(csv_button, "Save all subjects to a .csv file")

    def refresh(self) -> None:
        """Nothing to redraw; the page has no data-driven content."""

    def _snapshot(self) -> dict[str, Any] | None:
        try:
            return self.app.db.snapshot()
        except DatabaseError as exc:
            self.app.show_error("Database error", str(exc))
            return None

    def generate_pdf(self) -> None:
        snapshot = self._snapshot()
        if snapshot is None:
            return
        if not snapshot["semesters"]:
            messagebox.showinfo("Nothing to report yet",
                                "Add at least one semester before generating a report.",
                                parent=self.app)
            return
        path = filedialog.asksaveasfilename(
            parent=self.app, title="Save PDF Report", defaultextension=".pdf",
            initialfile="Student_Academic_Report.pdf",
            filetypes=[("PDF files", "*.pdf")])
        if not path:
            return
        try:
            generate_pdf_report(path, snapshot)
        except ReportError as exc:
            self.app.show_error("PDF report failed", str(exc))
            return
        self.app.set_status(f"PDF report saved to {path}")
        if messagebox.askyesno("Report saved", "The PDF report was created.\n\nOpen it now?",
                               parent=self.app):
            open_file(path)

    def export_csv(self) -> None:
        snapshot = self._snapshot()
        if snapshot is None:
            return
        path = filedialog.asksaveasfilename(
            parent=self.app, title="Export CSV", defaultextension=".csv",
            initialfile="student_gpa_data.csv", filetypes=[("CSV files", "*.csv")])
        if not path:
            return
        try:
            rows = export_csv(path, snapshot)
        except FileOperationError as exc:
            self.app.show_error("CSV export failed", str(exc))
            return
        self.app.set_status(f"Exported {rows} subject(s) to {path}")

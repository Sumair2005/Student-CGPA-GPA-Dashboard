"""Dashboard page: profile, statistic cards, GPA chart and semester table."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

from core.calculator import AcademicOverview, build_overview
from core.grading import classify_gpa
from database.database import DatabaseError
from ui.charts import build_trend_figure, embed_figure
from ui.widgets import (PAD, BasePage, Card, Column, DataTable, ScrollableFrame,
                        StatCard)
from utils.helpers import format_credits, format_gpa, show_dash

SEMESTER_COLUMNS = (
    Column("name", "Semester", 85, "w", stretch=True),
    Column("credits", "Credits", 60, "center"),
    Column("sgpa", "SGPA", 50, "center"),
    Column("standing", "Standing", 100, "center"),
)


class DashboardPage(BasePage):
    def __init__(self, parent: tk.Misc, app: Any) -> None:
        super().__init__(parent, app)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.scroll = ScrollableFrame(self, app.theme)
        self.scroll.grid(row=0, column=0, sticky="nsew")
        self.body = self.scroll.inner
        self.body.columnconfigure(0, weight=1)

    def refresh(self) -> None:
        for child in self.body.winfo_children():
            child.destroy()
        try:
            overview = build_overview(self.app.db.snapshot())
        except DatabaseError as exc:
            self.app.show_error("Database error", str(exc))
            return
        if overview.is_empty:
            self._build_empty_state()
            return
        self._build_header(overview)
        self._build_profile(overview)
        self._build_stats(overview)
        self._build_bottom(overview)

    # ---------------------------------------------------------------- sections
    def _build_empty_state(self) -> None:
        card = Card(self.body, padding=40)
        card.grid(row=0, column=0, padx=PAD, pady=60)
        ttk.Label(card, text="\U0001F393", font=("Segoe UI Emoji", 40),
                  style="Card.TLabel").pack()
        ttk.Label(card, text="Welcome to Student GPA & CGPA Dashboard",
                  style="Heading.TLabel", font=("Segoe UI", 18, "bold")).pack(pady=(10, 6))
        ttk.Label(card, style="CardMuted.TLabel", justify="center",
                  text="Start by adding your student information\nand your first semester."
                  ).pack(pady=(0, 20))
        row = ttk.Frame(card, style="Inner.TFrame")
        row.pack()
        ttk.Button(row, text="Add First Semester", style="Accent.TButton",
                   command=self._add_first_semester).pack(side="left", padx=(0, 8))
        ttk.Button(row, text="Edit Student Information",
                   command=self.app.edit_student).pack(side="left")

    def _add_first_semester(self) -> None:
        self.app.show_page("semesters")
        self.app.pages["semesters"].add_semester()

    def _build_header(self, overview: AcademicOverview) -> None:
        name = overview.student.get("name") or "Student"
        header = ttk.Frame(self.body, style="Bg.TFrame")
        header.grid(row=0, column=0, sticky="ew", padx=PAD, pady=(24, 14))
        ttk.Label(header, text=f"Welcome, {name}", style="PageTitle.TLabel").pack(anchor="w")
        ttk.Label(header, text="Here is an overview of your academic progress.",
                  style="Subtitle.TLabel").pack(anchor="w")

    def _build_profile(self, overview: AcademicOverview) -> None:
        card = Card(self.body)
        card.grid(row=1, column=0, sticky="ew", padx=PAD, pady=(0, 14))
        card.columnconfigure(0, weight=1)
        top = ttk.Frame(card, style="Inner.TFrame")
        top.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        top.columnconfigure(0, weight=1)
        ttk.Label(top, text="Student Profile", style="Heading.TLabel").grid(
            row=0, column=0, sticky="w")
        ttk.Button(top, text="\u270E Edit", command=self.app.edit_student).grid(
            row=0, column=1, sticky="e")

        student = overview.student
        items = (
            ("Student Name", student.get("name", "")),
            ("Student ID", student.get("student_id", "")),
            ("Program", student.get("program", "")),
            ("University", student.get("university", "")),
            ("Department", student.get("department", "")),
            ("Current Semester", overview.current_semester_name),
        )
        grid = ttk.Frame(card, style="Inner.TFrame")
        grid.grid(row=1, column=0, sticky="ew")
        for column in range(3):
            grid.columnconfigure(column, weight=1, uniform="profile")
        for index, (label, value) in enumerate(items):
            cell = ttk.Frame(grid, style="Inner.TFrame")
            cell.grid(row=index // 3, column=index % 3, sticky="w", pady=6, padx=(0, 16))
            ttk.Label(cell, text=label.upper(), style="CardTitle.TLabel").pack(anchor="w")
            ttk.Label(cell, text=show_dash(value), style="Card.TLabel",
                      wraplength=260).pack(anchor="w")

    def _build_stats(self, overview: AcademicOverview) -> None:
        row = ttk.Frame(self.body, style="Bg.TFrame")
        row.grid(row=2, column=0, sticky="ew", padx=PAD, pady=(0, 14))
        cards = (
            ("CGPA", f"{format_gpa(overview.cgpa)} / 4.00", classify_gpa(overview.cgpa)),
            ("Latest SGPA", format_gpa(overview.latest.sgpa if overview.latest else None),
             overview.latest.name if overview.latest else "No graded semester yet"),
            ("Total Credits", format_credits(overview.total_credits), "credit hours"),
            ("Semesters", str(overview.semester_count), "recorded"),
        )
        for column, (title, value, sub) in enumerate(cards):
            row.columnconfigure(column, weight=1, uniform="stats")
            StatCard(row, title, value, sub).grid(
                row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 7, 7 if column < 3 else 0))

    def _build_bottom(self, overview: AcademicOverview) -> None:
        row = ttk.Frame(self.body, style="Bg.TFrame")
        row.grid(row=3, column=0, sticky="ew", padx=PAD, pady=(0, PAD))
        row.columnconfigure(0, weight=3, uniform="bottom")
        row.columnconfigure(1, weight=2, uniform="bottom")

        chart_card = Card(row)
        chart_card.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        ttk.Label(chart_card, text="GPA Performance Chart", style="Heading.TLabel").pack(
            anchor="w", pady=(0, 8))
        if overview.stats is None:
            ttk.Label(chart_card, text="Add subjects to a semester to see your GPA trend.",
                      style="CardMuted.TLabel").pack(pady=60)
        else:
            figure = build_trend_figure(overview.summaries, self.app.theme.palette)
            embed_figure(chart_card, figure, self.app.theme.palette, height=270)

        table_card = Card(row)
        table_card.grid(row=0, column=1, sticky="nsew", padx=(7, 0))
        table_card.columnconfigure(0, weight=1)
        ttk.Label(table_card, text="Semester Performance", style="Heading.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 8))
        table = DataTable(table_card, self.app.theme, SEMESTER_COLUMNS, height=8,
                          empty_text="No semesters yet.")
        table.grid(row=1, column=0, sticky="nsew")
        table.set_rows([
            (str(s.semester_id), (s.name, format_credits(s.credits), format_gpa(s.sgpa),
                                  classify_gpa(s.sgpa)))
            for s in overview.summaries
        ])

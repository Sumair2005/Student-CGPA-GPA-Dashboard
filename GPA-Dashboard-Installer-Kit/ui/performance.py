"""Performance page: statistics, GPA trend and grade distribution."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

from core.calculator import build_overview
from core.grading import classify_gpa
from database.database import DatabaseError
from ui.charts import build_distribution_figure, build_trend_figure, embed_figure
from ui.widgets import PAD, BasePage, Card, ScrollableFrame, StatCard
from utils.helpers import format_credits, format_gpa


class PerformancePage(BasePage):
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

        header = ttk.Frame(self.body, style="Bg.TFrame")
        header.grid(row=0, column=0, sticky="ew", padx=PAD, pady=(24, 14))
        ttk.Label(header, text="Performance", style="PageTitle.TLabel").pack(anchor="w")
        ttk.Label(header, text="Trends and statistics across your semesters.",
                  style="Subtitle.TLabel").pack(anchor="w")

        stats = overview.stats
        if stats is None:
            card = Card(self.body, padding=40)
            card.grid(row=1, column=0, padx=PAD, pady=40)
            ttk.Label(card, text="Add subjects to a semester to see performance analytics.",
                      style="CardMuted.TLabel").pack()
            return

        row = ttk.Frame(self.body, style="Bg.TFrame")
        row.grid(row=1, column=0, sticky="ew", padx=PAD, pady=(0, 14))
        cards = (
            ("Highest SGPA", format_gpa(stats.highest.sgpa), stats.highest.name),
            ("Lowest SGPA", format_gpa(stats.lowest.sgpa), stats.lowest.name),
            ("Average SGPA", format_gpa(stats.average_sgpa), "across semesters"),
            ("Current CGPA", format_gpa(stats.cgpa), classify_gpa(stats.cgpa)),
            ("Total Credits", format_credits(stats.total_credits), "credit hours"),
        )
        for column, (title, value, sub) in enumerate(cards):
            row.columnconfigure(column, weight=1, uniform="perf")
            StatCard(row, title, value, sub).grid(
                row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 6, 6 if column < 4 else 0))

        highlights = ttk.Frame(self.body, style="Bg.TFrame")
        highlights.grid(row=2, column=0, sticky="ew", padx=PAD, pady=(0, 14))
        highlights.columnconfigure(0, weight=1, uniform="hl")
        highlights.columnconfigure(1, weight=1, uniform="hl")
        for column, (title, summary) in enumerate((
                ("Highest Performance", stats.highest), ("Lowest Performance", stats.lowest))):
            card = Card(highlights)
            card.grid(row=0, column=column, sticky="nsew",
                      padx=(0, 7) if column == 0 else (7, 0))
            ttk.Label(card, text=title.upper(), style="CardTitle.TLabel").pack(anchor="w")
            ttk.Label(card, text=f"{summary.name}  \u00b7  SGPA {format_gpa(summary.sgpa)}",
                      style="Heading.TLabel").pack(anchor="w", pady=(4, 0))
            ttk.Label(card, text=f"{summary.academic_year}  \u00b7  "
                                 f"{format_credits(summary.credits)} credits",
                      style="CardMuted.TLabel").pack(anchor="w")

        charts = ttk.Frame(self.body, style="Bg.TFrame")
        charts.grid(row=3, column=0, sticky="ew", padx=PAD, pady=(0, PAD))
        charts.columnconfigure(0, weight=3, uniform="charts")
        charts.columnconfigure(1, weight=2, uniform="charts")
        palette = self.app.theme.palette

        trend = Card(charts)
        trend.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        ttk.Label(trend, text="GPA Trend", style="Heading.TLabel").pack(anchor="w", pady=(0, 8))
        embed_figure(trend, build_trend_figure(overview.summaries, palette), palette, 300)

        distribution = Card(charts)
        distribution.grid(row=0, column=1, sticky="nsew", padx=(7, 0))
        ttk.Label(distribution, text="Grade Distribution", style="Heading.TLabel").pack(
            anchor="w", pady=(0, 8))
        embed_figure(distribution, build_distribution_figure(overview.distribution, palette),
                     palette, 300)

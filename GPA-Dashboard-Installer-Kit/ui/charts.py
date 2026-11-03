"""Matplotlib figures (built without pyplot) embedded in Tkinter."""

from __future__ import annotations

import tkinter as tk
from typing import Sequence

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator

from core.calculator import SemesterSummary
from core.grading import MAX_GPA
from ui.theme import Palette


def _style_axes(figure: Figure, axes, palette: Palette) -> None:
    figure.patch.set_facecolor(palette.surface)
    axes.set_facecolor(palette.surface)
    for side in ("top", "right"):
        axes.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        axes.spines[side].set_color(palette.border)
    axes.tick_params(colors=palette.text_muted, labelsize=9)
    axes.yaxis.label.set_color(palette.text_muted)
    axes.grid(axis="y", color=palette.border, linewidth=0.6, alpha=0.8)
    axes.set_axisbelow(True)


def _short(label: str, limit: int = 14) -> str:
    return label if len(label) <= limit else label[: limit - 1] + "\u2026"


def build_trend_figure(summaries: Sequence[SemesterSummary], palette: Palette,
                       figsize: tuple[float, float] = (6.2, 3.2)) -> Figure:
    """Line chart of SGPA per semester with a 4.0 reference line."""
    figure = Figure(figsize=figsize, dpi=100)
    axes = figure.add_subplot(111)
    _style_axes(figure, axes, palette)

    points = [s for s in summaries if s.sgpa is not None]
    positions = list(range(len(points)))
    values = [s.sgpa for s in points]
    axes.axhline(MAX_GPA, color=palette.success, linestyle="--", linewidth=1,
                 label=f"Maximum ({MAX_GPA:.2f})")
    axes.plot(positions, values, color=palette.accent, marker="o", linewidth=2.4,
              markersize=8, markerfacecolor=palette.surface, markeredgewidth=2)
    for x, value in zip(positions, values):
        axes.annotate(f"{value:.2f}", (x, value), textcoords="offset points",
                      xytext=(0, 10), ha="center", fontsize=9, color=palette.text)
    axes.set_xlim(-0.5, max(len(points) - 0.5, 0.5))
    axes.set_ylim(0, MAX_GPA + 0.6)
    axes.set_yticks([0, 1, 2, 3, 4])
    axes.set_xticks(positions)
    axes.set_xticklabels([_short(s.name) for s in points],
                         rotation=20 if len(points) > 4 else 0,
                         ha="right" if len(points) > 4 else "center")
    axes.set_ylabel("GPA")
    legend = axes.legend(loc="lower left", fontsize=8, frameon=True,
                         facecolor=palette.surface, edgecolor=palette.border)
    for text in legend.get_texts():
        text.set_color(palette.text_muted)
    figure.tight_layout()
    return figure


def build_distribution_figure(distribution: dict[str, int], palette: Palette,
                              figsize: tuple[float, float] = (5.0, 3.2)) -> Figure:
    """Bar chart with the number of subjects for every grade."""
    figure = Figure(figsize=figsize, dpi=100)
    axes = figure.add_subplot(111)
    _style_axes(figure, axes, palette)

    grades = list(distribution)
    counts = [distribution[g] for g in grades]
    axes.bar(grades, counts, color=palette.accent, width=0.62)
    for index, count in enumerate(counts):
        if count:
            axes.text(index, count + 0.05, str(count), ha="center", va="bottom",
                      fontsize=9, color=palette.text)
    axes.set_ylim(0, max(max(counts, default=0), 1) + 1)
    axes.yaxis.set_major_locator(MaxNLocator(integer=True))
    axes.set_ylabel("Subjects")
    figure.tight_layout()
    return figure


def embed_figure(parent: tk.Misc, figure: Figure, palette: Palette,
                 height: int = 280) -> FigureCanvasTkAgg:
    """Place a figure inside ``parent`` and return its canvas."""
    canvas = FigureCanvasTkAgg(figure, master=parent)
    widget = canvas.get_tk_widget()
    widget.configure(bg=palette.surface, height=height, highlightthickness=0)
    widget.pack(fill="both", expand=True)
    canvas.draw()
    return canvas

"""Central place for every colour, font and ttk style used by the app."""

from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from tkinter import ttk
from typing import Callable

FONT_FAMILY = "Segoe UI"
DEFAULT_THEME = "dark"


@dataclass(frozen=True)
class Palette:
    name: str
    bg: str
    surface: str
    surface_alt: str
    row_alt: str
    sidebar: str
    sidebar_text: str
    sidebar_hover: str
    border: str
    text: str
    text_muted: str
    accent: str
    accent_hover: str
    accent_text: str
    danger: str
    danger_hover: str
    success: str
    input_bg: str
    selection: str
    selection_text: str


DARK = Palette(
    name="dark", bg="#0f172a", surface="#1e293b", surface_alt="#273449",
    row_alt="#233044", sidebar="#0b1220", sidebar_text="#cbd5e1",
    sidebar_hover="#1e293b", border="#334155", text="#f1f5f9",
    text_muted="#94a3b8", accent="#6366f1", accent_hover="#818cf8",
    accent_text="#ffffff", danger="#ef4444", danger_hover="#f87171",
    success="#22c55e", input_bg="#0f172a", selection="#3730a3",
    selection_text="#ffffff",
)

LIGHT = Palette(
    name="light", bg="#f1f5f9", surface="#ffffff", surface_alt="#e8edf4",
    row_alt="#f8fafc", sidebar="#e2e8f0", sidebar_text="#334155",
    sidebar_hover="#cbd5e1", border="#d5dce6", text="#0f172a",
    text_muted="#64748b", accent="#4f46e5", accent_hover="#6366f1",
    accent_text="#ffffff", danger="#dc2626", danger_hover="#ef4444",
    success="#16a34a", input_bg="#ffffff", selection="#c7d2fe",
    selection_text="#1e1b4b",
)

PALETTES: dict[str, Palette] = {"light": LIGHT, "dark": DARK}


class ThemeManager:
    """Applies a palette to every ttk style and notifies subscribers."""

    def __init__(self, root: tk.Tk, name: str = DEFAULT_THEME) -> None:
        self.root = root
        self.style = ttk.Style(root)
        self.style.theme_use("clam")
        self.name = name if name in PALETTES else DEFAULT_THEME
        self._listeners: list[Callable[[Palette], None]] = []
        self._configure()

    @property
    def palette(self) -> Palette:
        return PALETTES[self.name]

    def subscribe(self, callback: Callable[[Palette], None]) -> None:
        self._listeners.append(callback)

    def unsubscribe(self, callback: Callable[[Palette], None]) -> None:
        if callback in self._listeners:
            self._listeners.remove(callback)

    def set_theme(self, name: str) -> None:
        if name not in PALETTES:
            return
        self.name = name
        self._configure()
        for callback in list(self._listeners):
            try:
                callback(self.palette)
            except tk.TclError:
                pass  # a widget was destroyed; nothing to restyle

    def toggle(self) -> str:
        self.set_theme("light" if self.name == "dark" else "dark")
        return self.name

    # ------------------------------------------------------------------ styles
    def _configure(self) -> None:
        p, s = self.palette, self.style
        self.root.configure(bg=p.bg)
        self.root.option_add("*TCombobox*Listbox.background", p.input_bg)
        self.root.option_add("*TCombobox*Listbox.foreground", p.text)
        self.root.option_add("*TCombobox*Listbox.selectBackground", p.selection)
        self.root.option_add("*TCombobox*Listbox.selectForeground", p.selection_text)
        self.root.option_add("*TCombobox*Listbox.font", (FONT_FAMILY, 10))

        s.configure(".", font=(FONT_FAMILY, 10), background=p.bg, foreground=p.text,
                    bordercolor=p.border, darkcolor=p.border, lightcolor=p.border,
                    troughcolor=p.bg, focuscolor=p.accent, insertcolor=p.text,
                    selectbackground=p.selection, selectforeground=p.selection_text)

        # Frames
        s.configure("TFrame", background=p.bg)
        s.configure("Bg.TFrame", background=p.bg)
        s.configure("Card.TFrame", background=p.surface, borderwidth=1,
                    relief="solid", bordercolor=p.border)
        s.configure("Inner.TFrame", background=p.surface, borderwidth=0)
        s.configure("Header.TFrame", background=p.surface)
        s.configure("Sidebar.TFrame", background=p.sidebar)

        # Labels on the page background
        s.configure("TLabel", background=p.bg, foreground=p.text)
        s.configure("PageTitle.TLabel", font=(FONT_FAMILY, 20, "bold"))
        s.configure("DialogTitle.TLabel", font=(FONT_FAMILY, 14, "bold"))
        s.configure("Subtitle.TLabel", foreground=p.text_muted)
        s.configure("Muted.TLabel", foreground=p.text_muted)
        s.configure("Error.TLabel", foreground=p.danger)

        # Labels inside cards
        s.configure("Card.TLabel", background=p.surface, foreground=p.text)
        s.configure("CardMuted.TLabel", background=p.surface, foreground=p.text_muted)
        s.configure("CardTitle.TLabel", background=p.surface, foreground=p.text_muted,
                    font=(FONT_FAMILY, 9, "bold"))
        s.configure("CardValue.TLabel", background=p.surface, foreground=p.text,
                    font=(FONT_FAMILY, 20, "bold"))
        s.configure("CardSub.TLabel", background=p.surface, foreground=p.accent,
                    font=(FONT_FAMILY, 9))
        s.configure("Heading.TLabel", background=p.surface, foreground=p.text,
                    font=(FONT_FAMILY, 12, "bold"))
        s.configure("CardSuccess.TLabel", background=p.surface, foreground=p.success)
        s.configure("CardError.TLabel", background=p.surface, foreground=p.danger)

        # Header, sidebar, status bar
        s.configure("Header.TLabel", background=p.surface, foreground=p.text,
                    font=(FONT_FAMILY, 14, "bold"))
        s.configure("Sidebar.TLabel", background=p.sidebar, foreground=p.sidebar_text,
                    font=(FONT_FAMILY, 8))
        s.configure("Status.TLabel", background=p.surface, foreground=p.text_muted,
                    font=(FONT_FAMILY, 9))

        # Buttons
        s.configure("TButton", background=p.surface_alt, foreground=p.text,
                    padding=(14, 7), borderwidth=1, relief="flat", anchor="center")
        s.map("TButton", background=[("active", p.border), ("disabled", p.surface)],
              foreground=[("disabled", p.text_muted)])
        s.configure("Accent.TButton", background=p.accent, foreground=p.accent_text,
                    bordercolor=p.accent, darkcolor=p.accent, lightcolor=p.accent)
        s.map("Accent.TButton",
              background=[("active", p.accent_hover), ("disabled", p.surface_alt)],
              foreground=[("disabled", p.text_muted)])
        s.configure("Danger.TButton", background=p.danger, foreground="#ffffff",
                    bordercolor=p.danger, darkcolor=p.danger, lightcolor=p.danger)
        s.map("Danger.TButton", background=[("active", p.danger_hover)])
        s.configure("Nav.TButton", background=p.sidebar, foreground=p.sidebar_text,
                    anchor="w", padding=(18, 11), borderwidth=0,
                    bordercolor=p.sidebar, darkcolor=p.sidebar, lightcolor=p.sidebar,
                    font=(FONT_FAMILY, 11))
        s.map("Nav.TButton", background=[("active", p.sidebar_hover)])
        s.configure("NavActive.TButton", background=p.accent, foreground=p.accent_text,
                    anchor="w", padding=(18, 11), borderwidth=0,
                    bordercolor=p.accent, darkcolor=p.accent, lightcolor=p.accent,
                    font=(FONT_FAMILY, 11, "bold"))
        s.map("NavActive.TButton", background=[("active", p.accent_hover)])
        s.configure("Icon.TButton", background=p.surface, foreground=p.text,
                    padding=(10, 5), borderwidth=0, font=(FONT_FAMILY, 14),
                    bordercolor=p.surface, darkcolor=p.surface, lightcolor=p.surface)
        s.map("Icon.TButton", background=[("active", p.surface_alt)])

        # Inputs
        for widget in ("TEntry", "TCombobox"):
            s.configure(widget, fieldbackground=p.input_bg, foreground=p.text,
                        padding=6, bordercolor=p.border, insertcolor=p.text)
            s.map(widget, bordercolor=[("focus", p.accent)],
                  lightcolor=[("focus", p.accent)], darkcolor=[("focus", p.accent)])
        s.configure("TCombobox", background=p.surface_alt, arrowcolor=p.text_muted)
        s.map("TCombobox",
              fieldbackground=[("readonly", p.input_bg)],
              foreground=[("readonly", p.text)],
              selectbackground=[("readonly", p.input_bg)],
              selectforeground=[("readonly", p.text)])

        # Tables
        s.configure("Treeview", background=p.surface, fieldbackground=p.surface,
                    foreground=p.text, rowheight=30, borderwidth=0, font=(FONT_FAMILY, 10))
        s.map("Treeview", background=[("selected", p.selection)],
              foreground=[("selected", p.selection_text)])
        s.configure("Treeview.Heading", background=p.surface_alt, foreground=p.text_muted,
                    font=(FONT_FAMILY, 9, "bold"), relief="flat", padding=(8, 7),
                    bordercolor=p.border)
        s.map("Treeview.Heading", background=[("active", p.border)])

        # Misc
        s.configure("Vertical.TScrollbar", background=p.surface_alt, troughcolor=p.bg,
                    bordercolor=p.bg, arrowcolor=p.text_muted, relief="flat")
        s.map("Vertical.TScrollbar", background=[("active", p.border)])
        s.configure("Card.TRadiobutton", background=p.surface, foreground=p.text,
                    indicatorcolor=p.input_bg, font=(FONT_FAMILY, 10))
        s.map("Card.TRadiobutton", background=[("active", p.surface)],
              indicatorcolor=[("selected", p.accent)])
        s.configure("TSeparator", background=p.border)

"""Main application window: header, sidebar navigation, pages, status bar."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any

from core.validators import ValidationError, validate_student
from database.database import Database, DatabaseError
from ui.dashboard import DashboardPage
from ui.performance import PerformancePage
from ui.reports import ReportsPage
from ui.semesters import SemestersPage
from ui.settings import SettingsPage
from ui.theme import DEFAULT_THEME, ThemeManager
from ui.widgets import Field, FormDialog, Tooltip
from utils.helpers import APP_NAME, APP_VERSION

NAV_ITEMS = (
    ("dashboard", "\U0001F3E0", "Dashboard"),
    ("semesters", "\U0001F4DA", "Semesters"),
    ("performance", "\U0001F4CA", "Performance"),
    ("reports", "\U0001F4C4", "Reports"),
    ("settings", "\u2699", "Settings"),
)

STUDENT_FIELDS = (
    Field("name", "Student Name"),
    Field("student_id", "Student ID"),
    Field("program", "Program (e.g. BS Computer Science)"),
    Field("university", "University"),
    Field("department", "Department"),
)


class App(tk.Tk):
    """Root window. Pages talk to the database through ``app.db``."""

    def __init__(self, db: Database) -> None:
        super().__init__()
        self.db = db
        self.title(APP_NAME)
        self.geometry("1200x760")
        self.minsize(1000, 660)

        try:
            saved_theme = db.get_setting("theme", DEFAULT_THEME)
        except DatabaseError:
            saved_theme = DEFAULT_THEME
        self.theme = ThemeManager(self, saved_theme or DEFAULT_THEME)

        self.pages: dict[str, Any] = {}
        self.current_page = ""
        self._stale: set[str] = set()
        self._status_job: str | None = None
        self._nav_buttons: dict[str, ttk.Button] = {}

        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)
        self._build_header()
        self._build_sidebar()
        self._build_content()
        self._build_status_bar()
        self._bind_shortcuts()

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.show_page("dashboard")

    # ------------------------------------------------------------------ layout
    def _build_header(self) -> None:
        header = ttk.Frame(self, style="Header.TFrame", padding=(20, 10))
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text=f"\U0001F393  {APP_NAME}", style="Header.TLabel").grid(
            row=0, column=0, sticky="w")
        self.theme_button = ttk.Button(header, style="Icon.TButton", command=self.toggle_theme)
        self.theme_button.grid(row=0, column=1, padx=(0, 4))
        settings_button = ttk.Button(header, text="\u2699", style="Icon.TButton",
                                     command=lambda: self.show_page("settings"))
        settings_button.grid(row=0, column=2)
        Tooltip(self.theme_button, "Switch between light and dark mode")
        Tooltip(settings_button, "Open settings")
        self._update_theme_icon()

    def _build_sidebar(self) -> None:
        sidebar = ttk.Frame(self, style="Sidebar.TFrame", width=220)
        sidebar.grid(row=1, column=0, sticky="ns")
        sidebar.grid_propagate(False)
        sidebar.pack_propagate(False)
        ttk.Frame(sidebar, style="Sidebar.TFrame", height=14).pack()
        for index, (key, icon, label) in enumerate(NAV_ITEMS, start=1):
            button = ttk.Button(sidebar, text=f"  {icon}   {label}", style="Nav.TButton",
                                command=lambda k=key: self.show_page(k))
            button.pack(fill="x", padx=12, pady=2)
            Tooltip(button, f"{label}  (Ctrl+{index})")
            self._nav_buttons[key] = button
        ttk.Label(sidebar, text=f"v{APP_VERSION}  \u00b7  Local data only",
                  style="Sidebar.TLabel").pack(side="bottom", pady=14)

    def _build_content(self) -> None:
        self.content = ttk.Frame(self, style="Bg.TFrame")
        self.content.grid(row=1, column=1, sticky="nsew")
        self.content.columnconfigure(0, weight=1)
        self.content.rowconfigure(0, weight=1)
        page_classes = {
            "dashboard": DashboardPage, "semesters": SemestersPage,
            "performance": PerformancePage, "reports": ReportsPage,
            "settings": SettingsPage,
        }
        for key, cls in page_classes.items():
            page = cls(self.content, self)
            page.grid(row=0, column=0, sticky="nsew")
            self.pages[key] = page

    def _build_status_bar(self) -> None:
        bar = ttk.Frame(self, style="Header.TFrame", padding=(20, 6))
        bar.grid(row=2, column=0, columnspan=2, sticky="ew")
        self._status = tk.StringVar(value="Ready")
        ttk.Label(bar, textvariable=self._status, style="Status.TLabel").pack(side="left")

    def _bind_shortcuts(self) -> None:
        for index, (key, _icon, _label) in enumerate(NAV_ITEMS, start=1):
            self.bind(f"<Control-Key-{index}>", lambda _e, k=key: self.show_page(k))

    # -------------------------------------------------------------- navigation
    def show_page(self, name: str) -> None:
        self.current_page = name
        self.pages[name].tkraise()
        for key, button in self._nav_buttons.items():
            button.configure(style="NavActive.TButton" if key == name else "Nav.TButton")
        if name in self._stale or not getattr(self.pages[name], "_loaded", False):
            self._stale.discard(name)
            self.pages[name]._loaded = True
            self.pages[name].refresh()

    def invalidate(self, skip: str | None = None) -> None:
        """Mark every page as out of date and redraw the visible one."""
        self._stale = set(self.pages) - ({skip} if skip else set())
        if self.current_page and self.current_page != skip:
            self._stale.discard(self.current_page)
            self.pages[self.current_page].refresh()

    # ------------------------------------------------------------------ theming
    def toggle_theme(self) -> None:
        self.set_theme("light" if self.theme.name == "dark" else "dark")

    def set_theme(self, name: str) -> None:
        if name == self.theme.name:
            self._update_theme_icon()
            return
        self.theme.set_theme(name)
        try:
            self.db.set_setting("theme", self.theme.name)
        except DatabaseError as exc:
            self.show_error("Could not save theme", str(exc))
        self._update_theme_icon()
        self.invalidate()  # redraw charts with the new colours

    def _update_theme_icon(self) -> None:
        # Show the mode you would switch TO.
        self.theme_button.configure(text="\u2600" if self.theme.name == "dark" else "\U0001F319")

    # ------------------------------------------------------------ shared dialogs
    def edit_student(self) -> None:
        try:
            initial = self.db.get_student()
        except DatabaseError as exc:
            self.show_error("Database error", str(exc))
            return
        result = FormDialog(self, self.theme, "Student Information", STUDENT_FIELDS,
                            validate_student, initial, "Save").show()
        if result is None:
            return
        try:
            self.db.save_student(result)
        except DatabaseError as exc:
            self.show_error("Could not save", str(exc))
            return
        self.set_status("Student information saved.")
        self.invalidate()

    def show_error(self, title: str, message: str) -> None:
        messagebox.showerror(title, message, parent=self)

    def set_status(self, message: str, duration_ms: int = 6000) -> None:
        self._status.set(message)
        if self._status_job is not None:
            self.after_cancel(self._status_job)
        self._status_job = self.after(duration_ms, lambda: self._status.set("Ready"))

    def _on_close(self) -> None:
        self.db.close()
        self.destroy()

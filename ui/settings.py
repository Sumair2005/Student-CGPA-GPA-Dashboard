"""Settings page: student info, appearance, grading scale and data tools."""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Any

from core.grading import GRADE_SCALE, classification_ranges
from core.validators import ValidationError, validate_student
from database.database import DatabaseError
from ui.widgets import (PAD, BasePage, Card, Column, DataTable, ScrollableFrame,
                        Tooltip, confirm)
from utils.export import FileOperationError, read_backup, write_backup

STUDENT_FIELDS = (
    ("name", "Name"),
    ("student_id", "Student ID"),
    ("program", "Program"),
    ("university", "University"),
    ("department", "Department"),
)


class SettingsPage(BasePage):
    def __init__(self, parent: tk.Misc, app: Any) -> None:
        super().__init__(parent, app)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.scroll = ScrollableFrame(self, app.theme)
        self.scroll.grid(row=0, column=0, sticky="nsew")
        body = self.scroll.inner
        body.columnconfigure(0, weight=1)

        header = ttk.Frame(body, style="Bg.TFrame")
        header.grid(row=0, column=0, sticky="ew", padx=PAD, pady=(24, 14))
        ttk.Label(header, text="Settings", style="PageTitle.TLabel").pack(anchor="w")
        ttk.Label(header, text="Your data never leaves this computer.",
                  style="Subtitle.TLabel").pack(anchor="w")

        self._build_student_card(body, 1)
        self._build_appearance_card(body, 2)
        self._build_grading_card(body, 3)
        self._build_data_card(body, 4)

    # ---------------------------------------------------------------- sections
    def _build_student_card(self, body: ttk.Frame, row: int) -> None:
        card = Card(body, padding=20)
        card.grid(row=row, column=0, sticky="ew", padx=PAD, pady=(0, 14))
        card.columnconfigure(1, weight=1)
        ttk.Label(card, text="Student Information", style="Heading.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        self._vars: dict[str, tk.StringVar] = {}
        for index, (key, label) in enumerate(STUDENT_FIELDS, start=1):
            ttk.Label(card, text=label, style="CardMuted.TLabel", width=14).grid(
                row=index, column=0, sticky="w", pady=4)
            var = tk.StringVar()
            self._vars[key] = var
            entry = ttk.Entry(card, textvariable=var)
            entry.grid(row=index, column=1, sticky="ew", pady=4)
            entry.bind("<Return>", lambda _e: self.save_student())
        footer = ttk.Frame(card, style="Inner.TFrame")
        footer.grid(row=len(STUDENT_FIELDS) + 1, column=0, columnspan=2, sticky="w", pady=(10, 0))
        ttk.Button(footer, text="Save Information", style="Accent.TButton",
                   command=self.save_student).pack(side="left")
        self._student_msg = tk.StringVar()
        ttk.Label(footer, textvariable=self._student_msg, style="CardSuccess.TLabel").pack(
            side="left", padx=12)

    def _build_appearance_card(self, body: ttk.Frame, row: int) -> None:
        card = Card(body, padding=20)
        card.grid(row=row, column=0, sticky="ew", padx=PAD, pady=(0, 14))
        ttk.Label(card, text="Appearance", style="Heading.TLabel").pack(anchor="w", pady=(0, 8))
        self.theme_var = tk.StringVar(value=self.app.theme.name)
        for value, text in (("light", "\u2600  Light Mode"), ("dark", "\U0001F319  Dark Mode")):
            ttk.Radiobutton(card, text=text, value=value, variable=self.theme_var,
                            style="Card.TRadiobutton",
                            command=lambda: self.app.set_theme(self.theme_var.get())
                            ).pack(anchor="w", pady=3)

    def _build_grading_card(self, body: ttk.Frame, row: int) -> None:
        card = Card(body, padding=20)
        card.grid(row=row, column=0, sticky="ew", padx=PAD, pady=(0, 14))
        card.columnconfigure(0, weight=1, uniform="grading")
        card.columnconfigure(1, weight=1, uniform="grading")
        ttk.Label(card, text="GPA Settings \u2014 Active Grading Scale",
                  style="Heading.TLabel").grid(row=0, column=0, columnspan=2,
                                               sticky="w", pady=(0, 10))
        scale = DataTable(card, self.app.theme,
                          (Column("grade", "Grade", 100, "center", True),
                           Column("point", "Grade Point", 120, "center")), height=12)
        scale.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
        scale.set_rows([(grade, (grade, f"{point:.2f}")) for grade, point in GRADE_SCALE.items()])
        bands = DataTable(card, self.app.theme,
                          (Column("range", "GPA Range", 120, "center"),
                           Column("label", "Classification", 150, "w", True)), height=5)
        bands.grid(row=1, column=1, sticky="new", padx=(8, 0))
        bands.set_rows([(str(i), row_) for i, row_ in enumerate(classification_ranges())])
        ttk.Label(card, style="CardMuted.TLabel", wraplength=700, justify="left", text=(
            "The scale is defined in core/grading.py. Classifications are descriptive only "
            "and never change how SGPA or CGPA are calculated.")).grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(10, 0))

    def _build_data_card(self, body: ttk.Frame, row: int) -> None:
        card = Card(body, padding=20)
        card.grid(row=row, column=0, sticky="ew", padx=PAD, pady=(0, PAD))
        ttk.Label(card, text="Data", style="Heading.TLabel").pack(anchor="w")
        ttk.Label(card, style="CardMuted.TLabel", justify="left", text=(
            "Backups are plain JSON files. Restoring replaces all current data."
        )).pack(anchor="w", pady=(4, 12))
        buttons = ttk.Frame(card, style="Inner.TFrame")
        buttons.pack(anchor="w")
        backup = ttk.Button(buttons, text="Backup Data", command=self.backup_data)
        restore = ttk.Button(buttons, text="Restore Data", command=self.restore_data)
        clear = ttk.Button(buttons, text="Clear All Data", style="Danger.TButton",
                           command=self.clear_data)
        for button in (backup, restore, clear):
            button.pack(side="left", padx=(0, 8))
        Tooltip(backup, "Save everything to a .json file")
        Tooltip(restore, "Load data from a .json backup")
        Tooltip(clear, "Permanently delete all student, semester and subject data")

    # ----------------------------------------------------------------- actions
    def refresh(self) -> None:
        try:
            student = self.app.db.get_student()
        except DatabaseError as exc:
            self.app.show_error("Database error", str(exc))
            return
        for key, var in self._vars.items():
            var.set(student.get(key, ""))
        self.theme_var.set(self.app.theme.name)
        self._student_msg.set("")

    def save_student(self) -> None:
        try:
            cleaned = validate_student({k: v.get() for k, v in self._vars.items()})
            self.app.db.save_student(cleaned)
        except (ValidationError, DatabaseError) as exc:
            self.app.show_error("Could not save", str(exc))
            return
        self._student_msg.set("Saved.")
        self.app.set_status("Student information saved.")
        self.app.invalidate(skip="settings")

    def backup_data(self) -> None:
        path = filedialog.asksaveasfilename(
            parent=self.app, title="Backup Data", defaultextension=".json",
            initialfile="student_gpa_backup.json", filetypes=[("JSON files", "*.json")])
        if not path:
            return
        try:
            write_backup(path, self.app.db.snapshot())
        except (FileOperationError, DatabaseError) as exc:
            self.app.show_error("Backup failed", str(exc))
            return
        self.app.set_status(f"Backup saved to {path}")

    def restore_data(self) -> None:
        path = filedialog.askopenfilename(
            parent=self.app, title="Restore Data",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if not path:
            return
        try:
            data = read_backup(path)  # validated before anything is touched
        except (FileOperationError, ValidationError) as exc:
            self.app.show_error("Restore failed", str(exc))
            return
        if not confirm(self, "Restore Data?",
                       f"This backup contains {len(data['semesters'])} semester(s).\n\n"
                       "Restoring will REPLACE all data currently in the app. Continue?"):
            return
        try:
            self.app.db.replace_all(data)
        except DatabaseError as exc:
            self.app.show_error("Restore failed", str(exc))
            return
        if data["theme"]:
            self.app.set_theme(data["theme"])
        self.app.set_status("Backup restored.")
        self.app.invalidate()

    def clear_data(self) -> None:
        if not confirm(self, "Clear All Data?",
                       "This permanently deletes your student information, all semesters "
                       "and all subjects.\n\nConsider making a backup first. Continue?"):
            return
        try:
            self.app.db.clear_all()
        except DatabaseError as exc:
            self.app.show_error("Could not clear data", str(exc))
            return
        self.app.set_status("All data cleared.")
        self.app.invalidate()

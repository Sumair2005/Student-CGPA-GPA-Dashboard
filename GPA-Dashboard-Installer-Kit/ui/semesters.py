"""Semesters page: semester list on top, subjects of the selection below."""

from __future__ import annotations

import tkinter as tk
from datetime import date
from tkinter import ttk
from typing import Any, Callable, Mapping

from core.calculator import build_overview
from core.grading import classify_gpa
from core.validators import ValidationError, validate_semester_form
from database.database import DatabaseError
from ui.subjects import SubjectsPanel
from ui.widgets import (PAD, BasePage, Card, Column, DataTable, Field, FormDialog,
                        Tooltip, confirm)
from utils.helpers import format_credits, format_gpa

COLUMNS = (
    Column("name", "Semester", 200, "w", stretch=True),
    Column("year", "Academic Year", 120, "center"),
    Column("number", "No.", 60, "center"),
    Column("subjects", "Subjects", 80, "center"),
    Column("credits", "Credits", 80, "center"),
    Column("sgpa", "SGPA", 80, "center"),
    Column("standing", "Standing", 140, "center"),
)

SEMESTER_FIELDS = (
    Field("semester_name", "Semester Name (e.g. 5th Semester)"),
    Field("academic_year", "Academic Year (e.g. 2026 or 2025-2026)"),
    Field("semester_number", "Semester Number (e.g. 5)"),
)


class SemestersPage(BasePage):
    def __init__(self, parent: tk.Misc, app: Any) -> None:
        super().__init__(parent, app)
        self.selected_id: int | None = None
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=2)

        actions = self.build_header(
            self, "Semesters", "Add semesters, then select one to manage its subjects.")
        self.add_button = ttk.Button(actions, text="+ Add Semester", style="Accent.TButton",
                                     command=self.add_semester)
        self.add_button.pack(side="left", padx=(0, 6))
        edit = ttk.Button(actions, text="Edit", command=self.edit_selected)
        edit.pack(side="left", padx=(0, 6))
        delete = ttk.Button(actions, text="Delete", command=self.delete_selected)
        delete.pack(side="left")
        Tooltip(self.add_button, "Add a new semester")
        Tooltip(edit, "Edit the selected semester (or double-click a row)")
        Tooltip(delete, "Delete the selected semester and its subjects (Delete key)")

        card = Card(self)
        card.grid(row=1, column=0, sticky="nsew", padx=PAD, pady=(0, 12))
        card.columnconfigure(0, weight=1)
        card.rowconfigure(0, weight=1)
        self.table = DataTable(card, app.theme, COLUMNS, height=5,
                               empty_text="No semesters yet. Click \u201c+ Add Semester\u201d.")
        self.table.grid(row=0, column=0, sticky="nsew")
        tree = self.table.tree
        tree.bind("<<TreeviewSelect>>", self._on_select)
        tree.bind("<Double-1>", lambda _e: self.edit_selected())
        tree.bind("<Return>", lambda _e: self.edit_selected())
        tree.bind("<Delete>", lambda _e: self.delete_selected())

        self.subjects = SubjectsPanel(self, app, on_change=self.app.invalidate)
        self.subjects.grid(row=2, column=0, sticky="nsew", padx=PAD, pady=(0, PAD))

    # ---------------------------------------------------------------- display
    def refresh(self) -> None:
        try:
            overview = build_overview(self.app.db.snapshot())
        except DatabaseError as exc:
            self.app.show_error("Database error", str(exc))
            return
        rows = [
            (str(s.semester_id), (
                s.name, s.academic_year, s.number, s.subject_count,
                format_credits(s.credits), format_gpa(s.sgpa), classify_gpa(s.sgpa),
            ))
            for s in overview.summaries
        ]
        self.table.set_rows(rows)
        ids = [str(s.semester_id) for s in overview.summaries]
        if self.selected_id is None or str(self.selected_id) not in ids:
            self.selected_id = int(ids[0]) if ids else None
        if self.selected_id is not None:
            self.table.select(str(self.selected_id))
        self.subjects.set_semester(self.selected_id)

    def _on_select(self, _event: tk.Event) -> None:
        iid = self.table.selected()
        if iid is None or int(iid) == self.selected_id and self.subjects.semester_id == int(iid):
            return
        self.selected_id = int(iid)
        self.subjects.set_semester(self.selected_id)

    # ---------------------------------------------------------------- actions
    def _validator(self, exclude_id: int | None = None
                   ) -> Callable[[Mapping[str, str]], dict[str, Any]]:
        def validate(raw: Mapping[str, str]) -> dict[str, Any]:
            cleaned = validate_semester_form(raw)
            try:
                taken = self.app.db.semester_number_exists(cleaned["semester_number"], exclude_id)
            except DatabaseError as exc:
                raise ValidationError(str(exc)) from None
            if taken:
                raise ValidationError(
                    f"Semester number {cleaned['semester_number']} already exists. "
                    "Please choose a different number.")
            return cleaned
        return validate

    def add_semester(self) -> None:
        try:
            number = self.app.db.next_semester_number()
        except DatabaseError as exc:
            self.app.show_error("Database error", str(exc))
            return
        initial = {"semester_name": f"Semester {number}", "semester_number": number,
                   "academic_year": str(date.today().year)}
        result = FormDialog(self, self.app.theme, "Add Semester", SEMESTER_FIELDS,
                            self._validator(), initial, "Add Semester").show()
        if result is None:
            return
        try:
            self.selected_id = self.app.db.add_semester(
                result["semester_name"], result["semester_number"], result["academic_year"])
        except DatabaseError as exc:
            self.app.show_error("Could not add semester", str(exc))
            return
        self.app.set_status(f"Added {result['semester_name']}.")
        self.app.invalidate()

    def edit_selected(self) -> None:
        iid = self.table.selected()
        if iid is None:
            self.app.set_status("Select a semester first.")
            return
        semester = self.app.db.get_semester(int(iid))
        if semester is None:
            return
        result = FormDialog(self, self.app.theme, "Edit Semester", SEMESTER_FIELDS,
                            self._validator(int(iid)), semester, "Save Changes").show()
        if result is None:
            return
        try:
            self.app.db.update_semester(int(iid), result["semester_name"],
                                        result["semester_number"], result["academic_year"])
        except DatabaseError as exc:
            self.app.show_error("Could not update semester", str(exc))
            return
        self.app.set_status("Semester updated.")
        self.app.invalidate()

    def delete_selected(self) -> None:
        iid = self.table.selected()
        if iid is None:
            self.app.set_status("Select a semester first.")
            return
        semester = self.app.db.get_semester(int(iid))
        if semester is None:
            return
        count = len(self.app.db.list_subjects(int(iid)))
        if not confirm(self, "Delete Semester?",
                       f"Delete \u201c{semester['semester_name']}\u201d and its {count} "
                       f"subject(s)? This cannot be undone."):
            return
        try:
            self.app.db.delete_semester(int(iid))
        except DatabaseError as exc:
            self.app.show_error("Could not delete semester", str(exc))
            return
        self.selected_id = None
        self.app.set_status("Semester deleted.")
        self.app.invalidate()

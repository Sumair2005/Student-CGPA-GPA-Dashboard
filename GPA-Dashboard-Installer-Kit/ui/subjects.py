"""Subjects table for the selected semester (add / edit / delete)."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, Callable

from core.calculator import quality_points, summarize_semester
from core.grading import GRADES, classify_gpa
from core.validators import ValidationError, validate_subject_form
from database.database import DatabaseError
from ui.widgets import Card, Column, DataTable, Field, FormDialog, Tooltip, confirm
from utils.helpers import format_credits, format_gpa, show_dash

ACTIONS_TEXT = "\u270E Edit    \U0001F5D1 Delete"

COLUMNS = (
    Column("subject_name", "Subject", 240, "w", stretch=True),
    Column("subject_code", "Code", 90, "w"),
    Column("credit_hours", "Credit Hours", 110, "center"),
    Column("grade", "Grade", 70, "center"),
    Column("grade_point", "Grade Point", 105, "center"),
    Column("quality_points", "Quality Points", 125, "center"),
    Column("actions", "Actions", 150, "center"),
)

SUBJECT_FIELDS = (
    Field("subject_name", "Subject Name"),
    Field("subject_code", "Subject Code (optional, e.g. CS-501)"),
    Field("credit_hours", "Credit Hours (e.g. 3)"),
    Field("grade", "Grade", kind="combo", values=GRADES),
)


class SubjectsPanel(Card):
    """Shows and edits the subjects of one semester."""

    def __init__(self, parent: tk.Misc, app: Any, on_change: Callable[[], None]) -> None:
        super().__init__(parent)
        self.app = app
        self.on_change = on_change
        self.semester_id: int | None = None

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        top = ttk.Frame(self, style="Inner.TFrame")
        top.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        top.columnconfigure(0, weight=1)
        titles = ttk.Frame(top, style="Inner.TFrame")
        titles.grid(row=0, column=0, sticky="w")
        self._title = tk.StringVar(value="Subjects")
        self._summary = tk.StringVar()
        ttk.Label(titles, textvariable=self._title, style="Heading.TLabel").pack(anchor="w")
        ttk.Label(titles, textvariable=self._summary, style="CardMuted.TLabel").pack(anchor="w")

        buttons = ttk.Frame(top, style="Inner.TFrame")
        buttons.grid(row=0, column=1, sticky="e")
        self.add_button = ttk.Button(buttons, text="+ Add Subject", style="Accent.TButton",
                                     command=self.add_subject)
        self.add_button.pack(side="left", padx=(0, 6))
        self.edit_button = ttk.Button(buttons, text="Edit", command=self.edit_selected)
        self.edit_button.pack(side="left", padx=(0, 6))
        self.delete_button = ttk.Button(buttons, text="Delete", command=self.delete_selected)
        self.delete_button.pack(side="left")
        Tooltip(self.add_button, "Add a subject to this semester")
        Tooltip(self.edit_button, "Edit the selected subject (or double-click a row)")
        Tooltip(self.delete_button, "Delete the selected subject (Delete key)")

        self.table = DataTable(self, app.theme, COLUMNS, height=7,
                               empty_text="Select a semester to view its subjects.")
        self.table.grid(row=1, column=0, sticky="nsew")
        tree = self.table.tree
        tree.bind("<Double-1>", lambda _e: self.edit_selected())
        tree.bind("<Return>", lambda _e: self.edit_selected())
        tree.bind("<Delete>", lambda _e: self.delete_selected())
        tree.bind("<ButtonRelease-1>", self._on_click)

    # ---------------------------------------------------------------- display
    def set_semester(self, semester_id: int | None) -> None:
        self.semester_id = semester_id
        self.refresh()

    def refresh(self) -> None:
        state = ["disabled"] if self.semester_id is None else ["!disabled"]
        self.add_button.state(state)
        if self.semester_id is None:
            self._title.set("Subjects")
            self._summary.set("")
            self.table.set_rows([], "Select a semester to view its subjects.")
            return
        try:
            semester = self.app.db.get_semester(self.semester_id)
            subjects = self.app.db.list_subjects(self.semester_id)
        except DatabaseError as exc:
            self.app.show_error("Database error", str(exc))
            return
        if semester is None:
            self.set_semester(None)
            return

        summary = summarize_semester({**semester, "subjects": subjects})
        self._title.set(f"{semester['semester_name']} \u2014 Subjects")
        self._summary.set(
            f"SGPA {format_gpa(summary.sgpa)}  \u00b7  "
            f"{format_credits(summary.credits)} credits  \u00b7  "
            f"{summary.quality_points:.2f} quality points  \u00b7  "
            f"{classify_gpa(summary.sgpa)}"
        )
        rows = []
        for subject in subjects:
            points = quality_points(subject["credit_hours"], subject["grade_point"])
            rows.append((str(subject["id"]), (
                subject["subject_name"], show_dash(subject["subject_code"]),
                format_credits(subject["credit_hours"]), subject["grade"],
                f"{subject['grade_point']:.2f}", f"{points:.2f}", ACTIONS_TEXT,
            )))
        self.table.set_rows(rows, "No subjects yet. Click \u201c+ Add Subject\u201d to start.")

    # ---------------------------------------------------------------- actions
    def add_subject(self) -> None:
        if self.semester_id is None:
            return
        initial = {"credit_hours": "3"}
        result = FormDialog(self, self.app.theme, "Add Subject", SUBJECT_FIELDS,
                            validate_subject_form, initial, "Add Subject").show()
        if result is None:
            return
        try:
            self.app.db.add_subject(self.semester_id, **result)
        except DatabaseError as exc:
            self.app.show_error("Could not add subject", str(exc))
            return
        self.app.set_status(f"Added subject \u201c{result['subject_name']}\u201d.")
        self.on_change()

    def edit_selected(self, iid: str | None = None) -> None:
        iid = iid or self.table.selected()
        if iid is None:
            self.app.set_status("Select a subject first.")
            return
        try:
            subject = self.app.db.get_subject(int(iid))
        except DatabaseError as exc:
            self.app.show_error("Database error", str(exc))
            return
        if subject is None:
            return
        result = FormDialog(self, self.app.theme, "Edit Subject", SUBJECT_FIELDS,
                            validate_subject_form, subject, "Save Changes").show()
        if result is None:
            return
        try:
            self.app.db.update_subject(int(iid), **result)
        except DatabaseError as exc:
            self.app.show_error("Could not update subject", str(exc))
            return
        self.app.set_status("Subject updated.")
        self.on_change()

    def delete_selected(self, iid: str | None = None) -> None:
        iid = iid or self.table.selected()
        if iid is None:
            self.app.set_status("Select a subject first.")
            return
        subject = self.app.db.get_subject(int(iid))
        name = subject["subject_name"] if subject else "this subject"
        if not confirm(self, "Delete Subject?", f"Delete \u201c{name}\u201d? This cannot be undone."):
            return
        try:
            self.app.db.delete_subject(int(iid))
        except DatabaseError as exc:
            self.app.show_error("Could not delete subject", str(exc))
            return
        self.app.set_status("Subject deleted.")
        self.on_change()

    def _on_click(self, event: tk.Event) -> None:
        """Clicking the Actions cell edits (left half) or deletes (right half)."""
        tree = self.table.tree
        if tree.identify("region", event.x, event.y) != "cell":
            return
        column = tree.identify_column(event.x)
        row = tree.identify_row(event.y)
        if not row or column != f"#{len(COLUMNS)}":
            return
        x, _y, width, _height = tree.bbox(row, column)
        if event.x < x + width / 2:
            self.edit_selected(row)
        else:
            self.delete_selected(row)

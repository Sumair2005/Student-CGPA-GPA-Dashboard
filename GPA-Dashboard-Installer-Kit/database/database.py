"""SQLite persistence layer.

All SQL uses parameterised queries. Foreign keys are enabled so deleting a
semester also deletes its subjects (``ON DELETE CASCADE``).
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Mapping

from core.grading import grade_to_point

STUDENT_FIELDS = ("name", "student_id", "program", "university", "department")

SCHEMA = """
CREATE TABLE IF NOT EXISTS student (
    id          INTEGER PRIMARY KEY CHECK (id = 1),
    name        TEXT NOT NULL DEFAULT '',
    student_id  TEXT NOT NULL DEFAULT '',
    program     TEXT NOT NULL DEFAULT '',
    university  TEXT NOT NULL DEFAULT '',
    department  TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS semesters (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    semester_name   TEXT NOT NULL,
    semester_number INTEGER NOT NULL UNIQUE,
    academic_year   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS subjects (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    semester_id  INTEGER NOT NULL REFERENCES semesters(id) ON DELETE CASCADE,
    subject_name TEXT NOT NULL,
    subject_code TEXT NOT NULL DEFAULT '',
    credit_hours REAL NOT NULL CHECK (credit_hours > 0),
    grade        TEXT NOT NULL,
    grade_point  REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_subjects_semester ON subjects(semester_id);
"""


class DatabaseError(Exception):
    """A friendly, user-presentable database problem."""


class Database:
    """Small wrapper around a single SQLite connection."""

    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        try:
            self._conn = sqlite3.connect(self.path)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys = ON")
            self._conn.executescript(SCHEMA)
        except sqlite3.Error as exc:
            raise DatabaseError(f"Could not open the database: {exc}") from exc

    # ------------------------------------------------------------------ helpers
    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        """Commit on success, roll back on any error."""
        try:
            with self._conn:
                yield self._conn
        except sqlite3.IntegrityError as exc:
            raise DatabaseError(
                "The change conflicts with existing data (for example a duplicate "
                "semester number)."
            ) from exc
        except sqlite3.Error as exc:
            raise DatabaseError(f"Database error: {exc}") from exc

    def _fetch_all(self, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
        try:
            return [dict(row) for row in self._conn.execute(sql, params).fetchall()]
        except sqlite3.Error as exc:
            raise DatabaseError(f"Database error: {exc}") from exc

    def _fetch_one(self, sql: str, params: tuple = ()) -> dict[str, Any] | None:
        rows = self._fetch_all(sql, params)
        return rows[0] if rows else None

    def close(self) -> None:
        try:
            self._conn.close()
        except sqlite3.Error:
            pass

    # ------------------------------------------------------------------ student
    def get_student(self) -> dict[str, str]:
        row = self._fetch_one(
            "SELECT name, student_id, program, university, department "
            "FROM student WHERE id = 1"
        )
        return row or {field: "" for field in STUDENT_FIELDS}

    @staticmethod
    def _write_student(conn: sqlite3.Connection, data: Mapping[str, str]) -> None:
        conn.execute(
            "INSERT OR REPLACE INTO student "
            "(id, name, student_id, program, university, department) "
            "VALUES (1, ?, ?, ?, ?, ?)",
            tuple(data.get(field, "") for field in STUDENT_FIELDS),
        )

    def save_student(self, data: Mapping[str, str]) -> None:
        with self._transaction() as conn:
            self._write_student(conn, data)

    # ---------------------------------------------------------------- semesters
    def list_semesters(self) -> list[dict[str, Any]]:
        return self._fetch_all("SELECT * FROM semesters ORDER BY semester_number")

    def get_semester(self, semester_id: int) -> dict[str, Any] | None:
        return self._fetch_one("SELECT * FROM semesters WHERE id = ?", (semester_id,))

    def semester_number_exists(self, number: int, exclude_id: int | None = None) -> bool:
        row = self._fetch_one(
            "SELECT id FROM semesters WHERE semester_number = ? AND id IS NOT ?",
            (number, exclude_id),
        )
        return row is not None

    def next_semester_number(self) -> int:
        row = self._fetch_one("SELECT MAX(semester_number) AS highest FROM semesters")
        return (row["highest"] or 0) + 1 if row else 1

    def add_semester(self, semester_name: str, semester_number: int, academic_year: str) -> int:
        with self._transaction() as conn:
            cursor = conn.execute(
                "INSERT INTO semesters (semester_name, semester_number, academic_year) "
                "VALUES (?, ?, ?)",
                (semester_name, semester_number, academic_year),
            )
            return int(cursor.lastrowid)

    def update_semester(
        self, semester_id: int, semester_name: str, semester_number: int, academic_year: str
    ) -> None:
        with self._transaction() as conn:
            conn.execute(
                "UPDATE semesters SET semester_name = ?, semester_number = ?, "
                "academic_year = ? WHERE id = ?",
                (semester_name, semester_number, academic_year, semester_id),
            )

    def delete_semester(self, semester_id: int) -> None:
        """Delete a semester; its subjects are removed by ON DELETE CASCADE."""
        with self._transaction() as conn:
            conn.execute("DELETE FROM semesters WHERE id = ?", (semester_id,))

    # ----------------------------------------------------------------- subjects
    def list_subjects(self, semester_id: int) -> list[dict[str, Any]]:
        return self._fetch_all(
            "SELECT * FROM subjects WHERE semester_id = ? ORDER BY id", (semester_id,)
        )

    def get_subject(self, subject_id: int) -> dict[str, Any] | None:
        return self._fetch_one("SELECT * FROM subjects WHERE id = ?", (subject_id,))

    def add_subject(
        self,
        semester_id: int,
        subject_name: str,
        subject_code: str,
        credit_hours: float,
        grade: str,
    ) -> int:
        with self._transaction() as conn:
            cursor = conn.execute(
                "INSERT INTO subjects "
                "(semester_id, subject_name, subject_code, credit_hours, grade, grade_point) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (semester_id, subject_name, subject_code, credit_hours, grade,
                 grade_to_point(grade)),
            )
            return int(cursor.lastrowid)

    def update_subject(
        self,
        subject_id: int,
        subject_name: str,
        subject_code: str,
        credit_hours: float,
        grade: str,
    ) -> None:
        with self._transaction() as conn:
            conn.execute(
                "UPDATE subjects SET subject_name = ?, subject_code = ?, "
                "credit_hours = ?, grade = ?, grade_point = ? WHERE id = ?",
                (subject_name, subject_code, credit_hours, grade,
                 grade_to_point(grade), subject_id),
            )

    def delete_subject(self, subject_id: int) -> None:
        with self._transaction() as conn:
            conn.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))

    # ----------------------------------------------------------------- settings
    def get_setting(self, key: str, default: str | None = None) -> str | None:
        row = self._fetch_one("SELECT value FROM settings WHERE key = ?", (key,))
        return row["value"] if row else default

    @staticmethod
    def _write_setting(conn: sqlite3.Connection, key: str, value: str) -> None:
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))

    def set_setting(self, key: str, value: str) -> None:
        with self._transaction() as conn:
            self._write_setting(conn, key, value)

    # ------------------------------------------------------- bulk data handling
    def snapshot(self, include_ids: bool = True) -> dict[str, Any]:
        """Return all data as nested dictionaries (student > semesters > subjects)."""
        semesters = self.list_semesters()
        subjects = self._fetch_all("SELECT * FROM subjects ORDER BY semester_id, id")
        by_semester: dict[int, list[dict[str, Any]]] = {}
        for subject in subjects:
            by_semester.setdefault(subject["semester_id"], []).append(subject)

        result_semesters = []
        for semester in semesters:
            subject_rows = []
            for subject in by_semester.get(semester["id"], []):
                row = dict(subject)
                if not include_ids:
                    row.pop("id")
                    row.pop("semester_id")
                subject_rows.append(row)
            entry = dict(semester)
            if not include_ids:
                entry.pop("id")
            entry["subjects"] = subject_rows
            result_semesters.append(entry)

        return {
            "student": self.get_student(),
            "settings": {"theme": self.get_setting("theme", "")},
            "semesters": result_semesters,
        }

    def replace_all(self, data: Mapping[str, Any]) -> None:
        """Replace every record with validated backup data (one transaction)."""
        with self._transaction() as conn:
            conn.execute("DELETE FROM subjects")
            conn.execute("DELETE FROM semesters")
            self._write_student(conn, data["student"])
            if data.get("theme"):
                self._write_setting(conn, "theme", data["theme"])
            for semester in data["semesters"]:
                cursor = conn.execute(
                    "INSERT INTO semesters (semester_name, semester_number, academic_year) "
                    "VALUES (?, ?, ?)",
                    (semester["semester_name"], semester["semester_number"],
                     semester["academic_year"]),
                )
                semester_id = cursor.lastrowid
                conn.executemany(
                    "INSERT INTO subjects "
                    "(semester_id, subject_name, subject_code, credit_hours, grade, grade_point) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    [
                        (semester_id, s["subject_name"], s["subject_code"],
                         s["credit_hours"], s["grade"], grade_to_point(s["grade"]))
                        for s in semester["subjects"]
                    ],
                )

    def clear_all(self) -> None:
        """Delete student, semester and subject data (the theme choice is kept)."""
        with self._transaction() as conn:
            conn.execute("DELETE FROM subjects")
            conn.execute("DELETE FROM semesters")
            conn.execute("DELETE FROM student")

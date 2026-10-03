"""CSV export and JSON backup / restore helpers."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Mapping

from core.calculator import quality_points
from core.validators import BACKUP_APP_ID, BACKUP_VERSION, ValidationError, validate_backup
from utils.helpers import timestamp_iso

CSV_HEADERS = (
    "Semester",
    "Academic Year",
    "Subject",
    "Subject Code",
    "Credit Hours",
    "Grade",
    "Grade Point",
    "Quality Points",
)


class FileOperationError(Exception):
    """A file could not be read or written (message is user friendly)."""


def build_csv_rows(snapshot: Mapping[str, Any]) -> list[list[Any]]:
    rows: list[list[Any]] = []
    for semester in snapshot["semesters"]:
        for subject in semester["subjects"]:
            rows.append([
                semester["semester_name"],
                semester["academic_year"],
                subject["subject_name"],
                subject["subject_code"],
                f"{subject['credit_hours']:g}",
                subject["grade"],
                f"{subject['grade_point']:.2f}",
                f"{quality_points(subject['credit_hours'], subject['grade_point']):.2f}",
            ])
    return rows


def export_csv(path: str | Path, snapshot: Mapping[str, Any]) -> int:
    """Write all subjects to a CSV file. Returns the number of data rows."""
    rows = build_csv_rows(snapshot)
    try:
        # utf-8-sig lets Excel on Windows open the file with correct characters.
        with open(path, "w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.writer(handle)
            writer.writerow(CSV_HEADERS)
            writer.writerows(rows)
    except OSError as exc:
        raise FileOperationError(f"Could not save the CSV file: {exc.strerror or exc}") from exc
    return len(rows)


def build_backup(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    """Convert a snapshot (with ids) into the portable backup format."""
    semesters = []
    for semester in snapshot["semesters"]:
        semesters.append({
            "semester_name": semester["semester_name"],
            "semester_number": semester["semester_number"],
            "academic_year": semester["academic_year"],
            "subjects": [
                {
                    "subject_name": s["subject_name"],
                    "subject_code": s["subject_code"],
                    "credit_hours": s["credit_hours"],
                    "grade": s["grade"],
                    "grade_point": s["grade_point"],
                }
                for s in semester["subjects"]
            ],
        })
    theme = snapshot.get("settings", {}).get("theme") or None
    return {
        "app": BACKUP_APP_ID,
        "version": BACKUP_VERSION,
        "exported_at": timestamp_iso(),
        "student": dict(snapshot["student"]),
        "settings": {"theme": theme} if theme else {},
        "semesters": semesters,
    }


def write_backup(path: str | Path, snapshot: Mapping[str, Any]) -> None:
    try:
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(build_backup(snapshot), handle, indent=2, ensure_ascii=False)
    except OSError as exc:
        raise FileOperationError(f"Could not save the backup: {exc.strerror or exc}") from exc


def read_backup(path: str | Path) -> dict[str, Any]:
    """Read and validate a backup file. Raises FileOperationError/ValidationError."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except OSError as exc:
        raise FileOperationError(f"Could not open the backup: {exc.strerror or exc}") from exc
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise ValidationError("This file is not a valid JSON backup.") from None
    return validate_backup(data)

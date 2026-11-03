"""Input validation helpers.

Every function either returns a cleaned value or raises ``ValidationError``
with a friendly message that can be shown directly to the user.
"""

from __future__ import annotations

import math
import re
from typing import Any, Mapping

from core.grading import is_valid_grade, normalize_grade

BACKUP_APP_ID = "student-gpa-cgpa-dashboard"
BACKUP_VERSION = 1
MAX_CREDIT_HOURS = 12.0
# Keep in sync with the palettes defined in ui/theme.py.
VALID_THEMES = ("light", "dark")

STUDENT_FIELDS = ("name", "student_id", "program", "university", "department")
_YEAR_PATTERN = re.compile(r"^\d{4}(\s*[-/]\s*(\d{2}|\d{4}))?$")


class ValidationError(ValueError):
    """Raised when user input or imported data is not acceptable."""


def _clean_text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def validate_subject_name(value: Any) -> str:
    text = _clean_text(value)
    if not text:
        raise ValidationError("Please enter a subject name.")
    if len(text) > 100:
        raise ValidationError("Subject name is too long (maximum 100 characters).")
    return text


def validate_subject_code(value: Any) -> str:
    """Subject code is optional."""
    text = _clean_text(value)
    if len(text) > 20:
        raise ValidationError("Subject code is too long (maximum 20 characters).")
    return text


def validate_credit_hours(value: Any) -> float:
    """Return credit hours as a float greater than 0 and at most 12."""
    message = "Please enter valid credit hours."
    if isinstance(value, bool):
        raise ValidationError(message)
    try:
        credits = float(str(value).strip())
    except (TypeError, ValueError):
        raise ValidationError(message) from None
    if not math.isfinite(credits) or credits <= 0 or credits > MAX_CREDIT_HOURS:
        raise ValidationError(message)
    return credits


def validate_grade(value: Any) -> str:
    grade = normalize_grade(value)
    if not is_valid_grade(grade):
        raise ValidationError("Please select a valid grade.")
    return grade


def validate_semester_name(value: Any) -> str:
    text = _clean_text(value)
    if not text:
        raise ValidationError("Please enter a semester name.")
    if len(text) > 60:
        raise ValidationError("Semester name is too long (maximum 60 characters).")
    return text


def validate_semester_number(value: Any) -> int:
    message = "Please enter a valid semester number (1 to 99)."
    if isinstance(value, bool):
        raise ValidationError(message)
    try:
        number = int(str(value).strip())
    except (TypeError, ValueError):
        raise ValidationError(message) from None
    if not 1 <= number <= 99:
        raise ValidationError(message)
    return number


def validate_academic_year(value: Any) -> str:
    text = _clean_text(value)
    if not _YEAR_PATTERN.match(text):
        raise ValidationError(
            "Please enter a valid academic year (for example 2026 or 2025-2026)."
        )
    return text


def validate_student(data: Mapping[str, Any]) -> dict[str, str]:
    """Clean the student profile. All fields are optional text."""
    cleaned: dict[str, str] = {}
    for field in STUDENT_FIELDS:
        text = _clean_text(data.get(field, ""))
        if len(text) > 120:
            raise ValidationError("One of the student fields is too long.")
        cleaned[field] = text
    return cleaned


def validate_semester_form(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the values collected by the add/edit semester dialog."""
    return {
        "semester_name": validate_semester_name(raw.get("semester_name")),
        "academic_year": validate_academic_year(raw.get("academic_year")),
        "semester_number": validate_semester_number(raw.get("semester_number")),
    }


def validate_subject_form(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the values collected by the add/edit subject dialog."""
    return {
        "subject_name": validate_subject_name(raw.get("subject_name")),
        "subject_code": validate_subject_code(raw.get("subject_code")),
        "credit_hours": validate_credit_hours(raw.get("credit_hours")),
        "grade": validate_grade(raw.get("grade")),
    }


def validate_backup(data: Any) -> dict[str, Any]:
    """Validate a decoded backup file and return clean, import-ready data.

    Grade points in the file are ignored on purpose: they are recalculated
    from the grade letters when the data is imported.
    """
    if not isinstance(data, dict) or data.get("app") != BACKUP_APP_ID:
        raise ValidationError("This file is not a Student GPA & CGPA Dashboard backup.")
    if data.get("version") != BACKUP_VERSION:
        raise ValidationError("This backup was made by an unsupported version.")

    student = data.get("student", {})
    if not isinstance(student, dict):
        raise ValidationError("Backup problem: invalid student information.")
    settings = data.get("settings", {})
    if not isinstance(settings, dict):
        raise ValidationError("Backup problem: invalid settings.")
    theme = settings.get("theme")
    if theme is not None and theme not in VALID_THEMES:
        raise ValidationError("Backup problem: unknown theme.")
    semesters = data.get("semesters")
    if not isinstance(semesters, list):
        raise ValidationError("Backup problem: the semester list is missing.")

    cleaned_semesters: list[dict[str, Any]] = []
    seen_numbers: set[int] = set()
    for s_index, semester in enumerate(semesters, start=1):
        label = f"Backup problem in semester entry {s_index}"
        if not isinstance(semester, dict):
            raise ValidationError(f"{label}: invalid entry.")
        try:
            cleaned = validate_semester_form(semester)
        except ValidationError as exc:
            raise ValidationError(f"{label}: {exc}") from None
        if cleaned["semester_number"] in seen_numbers:
            raise ValidationError(f"{label}: duplicate semester number.")
        seen_numbers.add(cleaned["semester_number"])

        subjects = semester.get("subjects", [])
        if not isinstance(subjects, list):
            raise ValidationError(f"{label}: invalid subject list.")
        cleaned["subjects"] = []
        for j_index, subject in enumerate(subjects, start=1):
            if not isinstance(subject, dict):
                raise ValidationError(f"{label}, subject {j_index}: invalid entry.")
            try:
                cleaned["subjects"].append(validate_subject_form(subject))
            except ValidationError as exc:
                raise ValidationError(f"{label}, subject {j_index}: {exc}") from None
        cleaned_semesters.append(cleaned)

    try:
        cleaned_student = validate_student(student)
    except ValidationError as exc:
        raise ValidationError(f"Backup problem: {exc}") from None

    return {"student": cleaned_student, "theme": theme, "semesters": cleaned_semesters}

"""Centralised grading scale and GPA classification rules.

Every grade point and classification label used by the application comes from
this module, so changing the grading scale means editing one place only.
"""

from __future__ import annotations

from typing import Final

MAX_GPA: Final[float] = 4.0

# Updated grading scale (grade points per credit hour matching your transcript scale).
GRADE_SCALE: Final[dict[str, float]] = {
    "A+": 4.00,  # 12.00 QP for 3 credit hours
    "A": 3.60,   # 10.80
    "A-": 3.40,  # 10.20
    "B+": 3.20,  #  9.60
    "B": 2.80,   #  8.40
    "B-": 2.60,  #  7.80
    "C+": 2.40,  #  7.20
    "C": 2.00,   #  6.00
    "C-": 1.75,  #  5.25
    "D+": 1.50,  #  4.50
    "D": 1.00,   #  3.00
    "F": 0.00,
}

GRADES: Final[tuple[str, ...]] = tuple(GRADE_SCALE)

# (minimum GPA, label), highest band first. Purely descriptive: it never
# changes how a GPA is calculated.
CLASSIFICATION_BANDS: Final[tuple[tuple[float, str], ...]] = (
    (3.50, "Excellent"),
    (3.00, "Very Good"),
    (2.50, "Good"),
    (2.00, "Average"),
)
LOWEST_CLASSIFICATION: Final[str] = "Needs Improvement"
NOT_AVAILABLE: Final[str] = "N/A"


def normalize_grade(grade: object) -> str:
    """Return a grade as a clean upper-case string (``" b+ "`` -> ``"B+"``)."""
    if grade is None:
        return ""
    return str(grade).strip().upper()


def is_valid_grade(grade: object) -> bool:
    """Return True if ``grade`` exists in the grading scale."""
    return normalize_grade(grade) in GRADE_SCALE


def grade_to_point(grade: object) -> float:
    """Return the grade point for a letter grade.

    Raises:
        ValueError: if the grade is not part of the grading scale.
    """
    key = normalize_grade(grade)
    if key not in GRADE_SCALE:
        raise ValueError(f"Unknown grade: {grade!r}")
    return GRADE_SCALE[key]


def classify_gpa(gpa: float | None) -> str:
    """Return a friendly classification label for a GPA value."""
    if gpa is None:
        return NOT_AVAILABLE
    value = round(gpa, 2)  # classify what the user actually sees on screen
    for minimum, label in CLASSIFICATION_BANDS:
        if value >= minimum:
            return label
    return LOWEST_CLASSIFICATION


def classification_ranges() -> list[tuple[str, str]]:
    """Return ``(range text, label)`` rows for display in the UI."""
    rows: list[tuple[str, str]] = []
    upper = MAX_GPA
    for minimum, label in CLASSIFICATION_BANDS:
        rows.append((f"{minimum:.2f} - {upper:.2f}", label))
        upper = round(minimum - 0.01, 2)
    rows.append((f"Below {CLASSIFICATION_BANDS[-1][0]:.2f}", LOWEST_CLASSIFICATION))
    return rows
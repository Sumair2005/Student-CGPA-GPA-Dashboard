"""Pure GPA maths: quality points, SGPA, CGPA and performance statistics.

Nothing in this module touches the GUI or the database, which keeps it easy
to unit test. Internal values stay precise; rounding happens only when a
number is displayed (see ``utils.helpers.format_gpa``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

from core.grading import GRADES


def quality_points(credit_hours: float, grade_point: float) -> float:
    """Quality points = credit hours x grade point."""
    return credit_hours * grade_point


def totals(subjects: Iterable[Mapping[str, Any]]) -> tuple[float, float]:
    """Return ``(total credit hours, total quality points)`` for subjects."""
    total_credits = 0.0
    total_points = 0.0
    for subject in subjects:
        credits = float(subject["credit_hours"])
        total_credits += credits
        total_points += quality_points(credits, float(subject["grade_point"]))
    return total_credits, total_points


def calculate_sgpa(subjects: Iterable[Mapping[str, Any]]) -> float | None:
    """SGPA = total quality points / total credit hours (None if no credits)."""
    credits, points = totals(subjects)
    return points / credits if credits > 0 else None


@dataclass(frozen=True)
class SemesterSummary:
    """Aggregated numbers for a single semester."""

    semester_id: int | None
    name: str
    number: int
    academic_year: str
    subject_count: int
    credits: float
    quality_points: float
    sgpa: float | None

    @property
    def has_data(self) -> bool:
        return self.credits > 0


def summarize_semester(semester: Mapping[str, Any]) -> SemesterSummary:
    subjects = semester.get("subjects", [])
    credits, points = totals(subjects)
    return SemesterSummary(
        semester_id=semester.get("id"),
        name=semester["semester_name"],
        number=int(semester["semester_number"]),
        academic_year=str(semester["academic_year"]),
        subject_count=len(subjects),
        credits=credits,
        quality_points=points,
        sgpa=points / credits if credits > 0 else None,
    )


def summarize_semesters(semesters: Iterable[Mapping[str, Any]]) -> list[SemesterSummary]:
    """Summaries sorted by semester number."""
    return sorted((summarize_semester(s) for s in semesters), key=lambda s: s.number)


def calculate_cgpa(summaries: Iterable[SemesterSummary]) -> float | None:
    """Credit-weighted CGPA.

    CGPA = total quality points of all semesters / total credit hours of all
    semesters. This is NOT the plain average of the SGPAs.
    """
    credits = 0.0
    points = 0.0
    for summary in summaries:
        credits += summary.credits
        points += summary.quality_points
    return points / credits if credits > 0 else None


@dataclass(frozen=True)
class PerformanceStats:
    highest: SemesterSummary
    lowest: SemesterSummary
    average_sgpa: float
    cgpa: float
    total_credits: float


def compute_performance(summaries: Sequence[SemesterSummary]) -> PerformanceStats | None:
    """Return statistics over semesters that contain graded subjects."""
    graded = [s for s in summaries if s.has_data and s.sgpa is not None]
    if not graded:
        return None
    cgpa = calculate_cgpa(graded)
    assert cgpa is not None  # graded semesters always have credits
    return PerformanceStats(
        highest=max(graded, key=lambda s: s.sgpa),
        lowest=min(graded, key=lambda s: s.sgpa),
        average_sgpa=sum(s.sgpa for s in graded) / len(graded),
        cgpa=cgpa,
        total_credits=sum(s.credits for s in graded),
    )


def grade_distribution(semesters: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    """Count subjects per grade letter (every grade is present, even at 0)."""
    counts = {grade: 0 for grade in GRADES}
    for semester in semesters:
        for subject in semester.get("subjects", []):
            grade = subject["grade"]
            if grade in counts:
                counts[grade] += 1
    return counts


@dataclass(frozen=True)
class AcademicOverview:
    """Everything the dashboard, charts and PDF report need in one object."""

    student: dict[str, str]
    summaries: list[SemesterSummary]
    cgpa: float | None
    total_credits: float
    total_quality_points: float
    latest: SemesterSummary | None
    current_semester_name: str
    stats: PerformanceStats | None
    distribution: dict[str, int] = field(default_factory=dict)

    @property
    def semester_count(self) -> int:
        return len(self.summaries)

    @property
    def is_empty(self) -> bool:
        """True for a brand-new profile: no student details and no semesters."""
        return not self.summaries and not any(self.student.values())


def build_overview(snapshot: Mapping[str, Any]) -> AcademicOverview:
    """Build an ``AcademicOverview`` from ``Database.snapshot()`` output."""
    semesters = snapshot.get("semesters", [])
    summaries = summarize_semesters(semesters)
    graded = [s for s in summaries if s.has_data]
    return AcademicOverview(
        student=dict(snapshot.get("student", {})),
        summaries=summaries,
        cgpa=calculate_cgpa(summaries),
        total_credits=sum(s.credits for s in summaries),
        total_quality_points=sum(s.quality_points for s in summaries),
        latest=graded[-1] if graded else None,
        current_semester_name=summaries[-1].name if summaries else "",
        stats=compute_performance(summaries),
        distribution=grade_distribution(semesters),
    )

"""Unit tests for grading, quality points, SGPA, CGPA and statistics."""

import unittest

from core.calculator import (build_overview, calculate_cgpa, calculate_sgpa,
                             compute_performance, grade_distribution, quality_points,
                             summarize_semester, summarize_semesters)
from core.grading import (GRADE_SCALE, classify_gpa, grade_to_point, is_valid_grade)


def subject(credits: float, grade: str) -> dict:
    return {"credit_hours": credits, "grade": grade, "grade_point": grade_to_point(grade)}


def semester(number: int, subjects: list) -> dict:
    return {"id": number, "semester_name": f"Semester {number}",
            "semester_number": number, "academic_year": "2026", "subjects": subjects}


class GradingTests(unittest.TestCase):
    def test_grade_points(self):
        self.assertEqual(grade_to_point("A"), 4.00)
        self.assertEqual(grade_to_point("A+"), 4.00)
        self.assertEqual(grade_to_point("B+"), 3.30)
        self.assertEqual(grade_to_point("F"), 0.00)

    def test_grade_lookup_is_case_and_space_insensitive(self):
        self.assertEqual(grade_to_point(" b+ "), 3.30)

    def test_unknown_grade_raises(self):
        with self.assertRaises(ValueError):
            grade_to_point("Z")
        self.assertFalse(is_valid_grade(""))
        self.assertFalse(is_valid_grade(None))

    def test_scale_has_twelve_grades(self):
        self.assertEqual(len(GRADE_SCALE), 12)

    def test_classification(self):
        self.assertEqual(classify_gpa(4.0), "Excellent")
        self.assertEqual(classify_gpa(3.50), "Excellent")
        self.assertEqual(classify_gpa(3.49), "Very Good")
        self.assertEqual(classify_gpa(2.75), "Good")
        self.assertEqual(classify_gpa(2.0), "Average")
        self.assertEqual(classify_gpa(1.99), "Needs Improvement")
        self.assertEqual(classify_gpa(None), "N/A")


class QualityPointTests(unittest.TestCase):
    def test_quality_points(self):
        self.assertAlmostEqual(quality_points(3, 4.00), 12.00)
        self.assertAlmostEqual(quality_points(3, 3.30), 9.90)
        self.assertAlmostEqual(quality_points(1.5, 2.0), 3.0)


class SgpaTests(unittest.TestCase):
    def test_example_from_specification(self):
        subjects = [subject(3, "A"), subject(3, "B+"), subject(3, "A-")]
        self.assertAlmostEqual(calculate_sgpa(subjects), 33.0 / 9.0)
        self.assertEqual(f"{calculate_sgpa(subjects):.2f}", "3.67")

    def test_different_credit_hours_are_weighted(self):
        subjects = [subject(4, "A"), subject(1, "F")]
        self.assertAlmostEqual(calculate_sgpa(subjects), 3.2)

    def test_no_subjects_gives_none(self):
        self.assertIsNone(calculate_sgpa([]))


class CgpaTests(unittest.TestCase):
    def test_cgpa_is_weighted_by_credits(self):
        # Semester 1: SGPA 3.50 over 18 credits, Semester 2: SGPA 3.80 over 21 credits.
        sem1 = semester(1, [{"credit_hours": 18, "grade": "A-", "grade_point": 3.50}])
        sem2 = semester(2, [{"credit_hours": 21, "grade": "A", "grade_point": 3.80}])
        summaries = summarize_semesters([sem1, sem2])
        expected = (3.50 * 18 + 3.80 * 21) / 39
        self.assertAlmostEqual(calculate_cgpa(summaries), expected)
        simple_average = (3.50 + 3.80) / 2
        self.assertNotAlmostEqual(calculate_cgpa(summaries), simple_average, places=3)

    def test_cgpa_equals_simple_average_for_equal_credits(self):
        sem1 = semester(1, [subject(3, "A"), subject(3, "B")])   # SGPA 3.5
        sem2 = semester(2, [subject(3, "B"), subject(3, "C")])   # SGPA 2.5
        cgpa = calculate_cgpa(summarize_semesters([sem1, sem2]))
        self.assertAlmostEqual(cgpa, 3.0)

    def test_empty_semester_does_not_change_cgpa(self):
        full = semester(1, [subject(3, "A")])
        empty = semester(2, [])
        self.assertAlmostEqual(calculate_cgpa(summarize_semesters([full, empty])), 4.0)

    def test_no_data_gives_none(self):
        self.assertIsNone(calculate_cgpa([]))


class StatsTests(unittest.TestCase):
    def setUp(self):
        self.semesters = [
            semester(1, [subject(3, "A"), subject(3, "B")]),
            semester(2, [subject(3, "A")]),
            semester(3, [subject(3, "C")]),
            semester(4, []),
        ]

    def test_performance_stats(self):
        stats = compute_performance(summarize_semesters(self.semesters))
        self.assertEqual(stats.highest.number, 2)
        self.assertEqual(stats.lowest.number, 3)
        self.assertAlmostEqual(stats.average_sgpa, (3.5 + 4.0 + 2.0) / 3)
        self.assertAlmostEqual(stats.total_credits, 12)

    def test_summaries_are_sorted_by_number(self):
        numbers = [s.number for s in summarize_semesters(reversed(self.semesters))]
        self.assertEqual(numbers, [1, 2, 3, 4])

    def test_grade_distribution_counts_every_grade(self):
        counts = grade_distribution(self.semesters)
        self.assertEqual(counts["A"], 2)
        self.assertEqual(counts["B"], 1)
        self.assertEqual(counts["C"], 1)
        self.assertEqual(counts["F"], 0)
        self.assertEqual(len(counts), 12)

    def test_overview(self):
        overview = build_overview({"student": {"name": ""}, "semesters": self.semesters})
        self.assertEqual(overview.semester_count, 4)
        self.assertEqual(overview.latest.number, 3)  # latest semester WITH grades
        self.assertEqual(overview.current_semester_name, "Semester 4")
        self.assertFalse(overview.is_empty)

    def test_empty_overview(self):
        overview = build_overview({"student": {"name": ""}, "semesters": []})
        self.assertTrue(overview.is_empty)
        self.assertIsNone(overview.cgpa)
        self.assertIsNone(overview.stats)

    def test_summarize_single_semester(self):
        summary = summarize_semester(semester(1, [subject(3, "A"), subject(3, "B+")]))
        self.assertEqual(summary.subject_count, 2)
        self.assertAlmostEqual(summary.quality_points, 12 + 9.9)


if __name__ == "__main__":
    unittest.main()

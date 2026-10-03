"""Unit tests for input validation and backup validation."""

import unittest

from core.validators import (BACKUP_APP_ID, BACKUP_VERSION, ValidationError,
                             validate_academic_year, validate_backup,
                             validate_credit_hours, validate_grade,
                             validate_semester_name, validate_semester_number,
                             validate_subject_form, validate_subject_name)


class SubjectValidationTests(unittest.TestCase):
    def test_empty_subject_name(self):
        for value in ("", "   ", None):
            with self.assertRaises(ValidationError) as ctx:
                validate_subject_name(value)
            self.assertEqual(str(ctx.exception), "Please enter a subject name.")

    def test_subject_name_is_trimmed(self):
        self.assertEqual(validate_subject_name("  Databases "), "Databases")

    def test_valid_credit_hours(self):
        self.assertEqual(validate_credit_hours("3"), 3.0)
        self.assertEqual(validate_credit_hours(" 1.5 "), 1.5)
        self.assertEqual(validate_credit_hours(4), 4.0)

    def test_invalid_credit_hours(self):
        for value in ("", "abc", "0", "-3", "-0.5", "13", "nan", "inf", None, True):
            with self.subTest(value=value):
                with self.assertRaises(ValidationError) as ctx:
                    validate_credit_hours(value)
                self.assertEqual(str(ctx.exception), "Please enter valid credit hours.")

    def test_invalid_grade(self):
        for value in ("", "Z", "A++", "E", None):
            with self.subTest(value=value):
                with self.assertRaises(ValidationError) as ctx:
                    validate_grade(value)
                self.assertEqual(str(ctx.exception), "Please select a valid grade.")

    def test_valid_grade_is_normalised(self):
        self.assertEqual(validate_grade("b+"), "B+")

    def test_subject_form(self):
        cleaned = validate_subject_form({"subject_name": "DB", "subject_code": " CS-1 ",
                                         "credit_hours": "3", "grade": "a"})
        self.assertEqual(cleaned, {"subject_name": "DB", "subject_code": "CS-1",
                                   "credit_hours": 3.0, "grade": "A"})


class SemesterValidationTests(unittest.TestCase):
    def test_empty_semester_name(self):
        with self.assertRaises(ValidationError) as ctx:
            validate_semester_name("  ")
        self.assertEqual(str(ctx.exception), "Please enter a semester name.")

    def test_semester_number(self):
        self.assertEqual(validate_semester_number("5"), 5)
        for value in ("", "0", "-1", "abc", "2.5", "100", None):
            with self.subTest(value=value):
                with self.assertRaises(ValidationError):
                    validate_semester_number(value)

    def test_academic_year(self):
        for value in ("2026", "2025-2026", "2025-26", "2025 / 2026"):
            self.assertEqual(validate_academic_year(value), value)
        for value in ("", "26", "abcd", "2025-2", None):
            with self.subTest(value=value):
                with self.assertRaises(ValidationError):
                    validate_academic_year(value)


class BackupValidationTests(unittest.TestCase):
    @staticmethod
    def valid_backup() -> dict:
        return {
            "app": BACKUP_APP_ID, "version": BACKUP_VERSION,
            "student": {"name": "Ali"}, "settings": {"theme": "dark"},
            "semesters": [{
                "semester_name": "Semester 1", "semester_number": 1, "academic_year": "2026",
                "subjects": [{"subject_name": "DB", "subject_code": "", "credit_hours": 3,
                              "grade": "A", "grade_point": 99}],
            }],
        }

    def test_valid_backup(self):
        cleaned = validate_backup(self.valid_backup())
        self.assertEqual(cleaned["theme"], "dark")
        self.assertEqual(cleaned["student"]["name"], "Ali")
        self.assertEqual(len(cleaned["semesters"][0]["subjects"]), 1)
        # Grade points in a file are never trusted.
        self.assertNotIn("grade_point", cleaned["semesters"][0]["subjects"][0])

    def test_wrong_file(self):
        for data in ({}, [], "text", {"app": "other", "version": 1}):
            with self.subTest(data=data):
                with self.assertRaises(ValidationError):
                    validate_backup(data)

    def test_bad_version(self):
        data = self.valid_backup()
        data["version"] = 99
        with self.assertRaises(ValidationError):
            validate_backup(data)

    def test_invalid_grade_inside_backup(self):
        data = self.valid_backup()
        data["semesters"][0]["subjects"][0]["grade"] = "Q"
        with self.assertRaises(ValidationError) as ctx:
            validate_backup(data)
        self.assertIn("valid grade", str(ctx.exception))

    def test_duplicate_semester_numbers(self):
        data = self.valid_backup()
        data["semesters"].append(dict(data["semesters"][0]))
        with self.assertRaises(ValidationError):
            validate_backup(data)

    def test_unknown_theme(self):
        data = self.valid_backup()
        data["settings"]["theme"] = "neon"
        with self.assertRaises(ValidationError):
            validate_backup(data)


if __name__ == "__main__":
    unittest.main()

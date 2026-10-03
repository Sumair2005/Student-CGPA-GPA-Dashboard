"""Tests for the SQLite layer, using an in-memory database."""

import json
import os
import tempfile
import unittest

from core.validators import validate_backup
from database.database import Database, DatabaseError
from utils.export import (FileOperationError, build_csv_rows, export_csv, read_backup,
                          write_backup)


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.db = Database(":memory:")

    def tearDown(self):
        self.db.close()

    def test_grade_point_is_stored_from_grade(self):
        sem = self.db.add_semester("Semester 1", 1, "2026")
        subject_id = self.db.add_subject(sem, "DB", "CS-1", 3, "B+")
        self.assertEqual(self.db.get_subject(subject_id)["grade_point"], 3.30)
        self.db.update_subject(subject_id, "DB", "CS-1", 3, "A")
        self.assertEqual(self.db.get_subject(subject_id)["grade_point"], 4.00)

    def test_duplicate_semester_number_is_rejected(self):
        self.db.add_semester("Semester 1", 1, "2026")
        self.assertTrue(self.db.semester_number_exists(1))
        with self.assertRaises(DatabaseError):
            self.db.add_semester("Another", 1, "2026")

    def test_deleting_a_semester_deletes_its_subjects(self):
        sem = self.db.add_semester("Semester 1", 1, "2026")
        self.db.add_subject(sem, "DB", "", 3, "A")
        self.db.delete_semester(sem)
        self.assertEqual(self.db.snapshot()["semesters"], [])
        count = self.db._conn.execute("SELECT COUNT(*) FROM subjects").fetchone()[0]
        self.assertEqual(count, 0)

    def test_student_and_settings_round_trip(self):
        self.assertEqual(self.db.get_student()["name"], "")
        self.db.save_student({"name": "Ali", "student_id": "1", "program": "BSCS",
                              "university": "UoS", "department": "IMCS"})
        self.assertEqual(self.db.get_student()["name"], "Ali")
        self.assertEqual(self.db.get_setting("theme", "light"), "light")
        self.db.set_setting("theme", "dark")
        self.assertEqual(self.db.get_setting("theme"), "dark")

    def test_sql_injection_text_is_stored_literally(self):
        sem = self.db.add_semester("S'; DROP TABLE subjects;--", 1, "2026")
        self.assertEqual(self.db.get_semester(sem)["semester_name"], "S'; DROP TABLE subjects;--")

    def test_clear_all_keeps_theme(self):
        self.db.set_setting("theme", "dark")
        sem = self.db.add_semester("Semester 1", 1, "2026")
        self.db.add_subject(sem, "DB", "", 3, "A")
        self.db.clear_all()
        self.assertEqual(self.db.snapshot()["semesters"], [])
        self.assertEqual(self.db.get_setting("theme"), "dark")


class BackupRestoreTests(unittest.TestCase):
    def test_backup_round_trip_and_csv(self):
        source = Database(":memory:")
        source.save_student({"name": "Ali", "student_id": "7", "program": "BSCS",
                             "university": "UoS", "department": "IMCS"})
        source.set_setting("theme", "dark")
        sem = source.add_semester("Semester 1", 1, "2026")
        source.add_subject(sem, "Databases", "CS-501", 3, "A")
        source.add_subject(sem, "Networks", "CS-503", 3, "A-")

        with tempfile.TemporaryDirectory() as folder:
            backup_path = os.path.join(folder, "backup.json")
            csv_path = os.path.join(folder, "data.csv")
            write_backup(backup_path, source.snapshot())
            self.assertEqual(export_csv(csv_path, source.snapshot()), 2)
            with open(csv_path, encoding="utf-8-sig") as handle:
                lines = handle.read().splitlines()
            self.assertEqual(lines[0].split(",")[0], "Semester")
            self.assertIn("Databases", lines[1])

            target = Database(":memory:")
            target.replace_all(read_backup(backup_path))
            restored = target.snapshot(include_ids=False)
            self.assertEqual(restored["student"]["name"], "Ali")
            self.assertEqual(target.get_setting("theme"), "dark")
            self.assertEqual(len(restored["semesters"][0]["subjects"]), 2)
            self.assertEqual(restored["semesters"][0]["subjects"][1]["grade_point"], 3.70)

    def test_corrupt_backup_is_rejected_without_touching_data(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "bad.json")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("{ not json")
            with self.assertRaises(Exception) as ctx:
                read_backup(path)
            self.assertIn("valid JSON", str(ctx.exception))
            with self.assertRaises(FileOperationError):
                read_backup(os.path.join(folder, "missing.json"))

    def test_csv_rows_have_quality_points(self):
        db = Database(":memory:")
        sem = db.add_semester("Semester 1", 1, "2026")
        db.add_subject(sem, "DB", "", 3, "B+")
        row = build_csv_rows(db.snapshot())[0]
        self.assertEqual(row[-1], "9.90")


if __name__ == "__main__":
    unittest.main()

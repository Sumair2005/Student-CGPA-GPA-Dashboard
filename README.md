# Student GPA & CGPA Dashboard

A modern desktop application for tracking semesters, subjects, SGPA and CGPA.
Built with Python, Tkinter, SQLite, Matplotlib and ReportLab. Everything runs
locally - no internet connection, accounts or tracking.

## Features

- Modern dashboard with sidebar navigation, stat cards and a student profile
- SGPA calculator (per semester) and credit-weighted CGPA calculator
- Multiple semesters with add / edit / delete
- Subject management (credit hours, grade, grade point, quality points)
- Dark and light theme, remembered between launches
- GPA trend chart and grade distribution chart (Matplotlib)
- Professional PDF academic report (ReportLab)
- CSV export of all subjects
- JSON backup and restore with validation
- SQLite database with foreign keys and parameterised queries
- Unit tests with the built-in `unittest` module

## Screenshots

screenshots/dashboard.png
screenshots/semester.png
screenshots/dark-mode.png
screenshots/report.png


## Technologies

```text
Python 3.11+
Tkinter / ttk
SQLite (sqlite3)
Matplotlib
ReportLab
unittest
```

## Installation (Windows)

Requires Python 3.11 or newer, installed from python.org with the
"tcl/tk and IDLE" option enabled (it is on by default).

```bash
git clone https://github.com/Sumair2005/Student-CGPA-GPA-Dashboard.git
cd Student-CGPA-GPA-Dashboard
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

The database file `student_gpa.db` is created automatically on first launch.

## Testing

```bash
python -m unittest discover
```

## GPA Formula

**Quality points** for a subject:

```text
Quality Points = Credit Hours x Grade Point
```

**SGPA** (semester GPA):

```text
SGPA = Total Quality Points in the semester / Total Credit Hours in the semester
```

Example with the grade scale below (three subjects, 3 credit hours each):

```text
Subject 1: grade A   ->  3 x 3.60 = 10.80
Subject 2: grade B+  ->  3 x 3.20 =  9.60
Subject 3: grade A-  ->  3 x 3.20 =  9.60

Total quality points = 30.00
Total credit hours   = 9
SGPA = 30.00 / 9 = 3.33
```

**CGPA** (cumulative GPA) is weighted by credit hours. It is *not* the average
of the SGPAs:

```text
CGPA = Total Quality Points across all semesters / Total Credit Hours across all semesters
```

Example: Semester 1 has SGPA 3.50 over 18 credits and Semester 2 has SGPA 3.80
over 21 credits. CGPA = (3.50 x 18 + 3.80 x 21) / 39 = 3.66 (a simple average
would wrongly give 3.65).

## Grade Scale

The scale used by this project (edit it in `core/grading.py`):

| Grade | Grade Point | Quality Points (3 credit hours) |
|-------|-------------|---------------------------------|
| A+    | 4.00        | 12.00                           |
| A     | 3.60        | 10.80                           |
| A-    | 3.20        | 9.60                            |
| B+    | 3.20        | 9.60                            |
| B     | 2.80        | 8.40                            |
| B-    | 2.40        | 7.20                            |
| C+    | 2.20        | 6.60                            |
| C     | 2.00        | 6.00                            |
| C-    | 1.80        | 5.40                            |
| D+    | 1.50        | 4.50                            |
| D     | 1.00        | 3.00                            |
| F     | 0.00        | 0.00                            |

## Project Structure

```text
Student-CGPA-GPA-Dashboard/
|-- main.py
|-- database/
|   |-- __init__.py
|   `-- database.py
|-- core/
|   |-- __init__.py
|   |-- calculator.py
|   |-- validators.py
|   `-- grading.py
|-- ui/
|   |-- __init__.py
|   |-- app.py
|   |-- dashboard.py
|   |-- semesters.py
|   |-- subjects.py
|   |-- performance.py
|   |-- reports.py
|   |-- settings.py
|   |-- charts.py
|   |-- widgets.py
|   `-- theme.py
|-- reports/
|   |-- __init__.py
|   `-- pdf_report.py
|-- utils/
|   |-- __init__.py
|   |-- export.py
|   `-- helpers.py
|-- tests/
|   |-- __init__.py
|   |-- test_calculator.py
|   |-- test_validators.py
|   `-- test_database.py
|-- assets/README.md
|-- screenshots/README.md
|-- requirements.txt
|-- README.md
|-- LICENSE
`-- .gitignore
```

## Privacy

All data stays on your computer in `student_gpa.db`. The database is listed in
`.gitignore` so personal student data is never committed by accident.

## Future Improvements

- University-specific grading scales
- Multiple grading systems (percentage, 5.0 scale)
- Optional cloud synchronisation
- Login system for multiple students
- Mobile version

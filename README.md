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

Screenshots are not included yet. Add your own to the `screenshots/` folder,
then reference them here:

```text
screenshots/dashboard.png
screenshots/semester.png
screenshots/dark-mode.png
screenshots/report.png
```

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
git clone YOUR_REPOSITORY_URL
cd student-gpa-cgpa-dashboard
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

**CGPA** (cumulative GPA) is weighted by credit hours. It is *not* the average
of the SGPAs:

```text
CGPA = Total Quality Points across all semesters / Total Credit Hours across all semesters
```

Example: Semester 1 has SGPA 3.50 over 18 credits and Semester 2 has SGPA 3.80
over 21 credits. CGPA = (3.50 x 18 + 3.80 x 21) / 39 = 3.66 (a simple average
would wrongly give 3.65).

Default grade scale (edit it in `core/grading.py`):

```text
A+ 4.00   A 4.00   A- 3.70
B+ 3.30   B 3.00   B- 2.70
C+ 2.30   C 2.00   C- 1.70
D+ 1.30   D 1.00   F  0.00
```

## Project Structure

```text
student-gpa-cgpa-dashboard/
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

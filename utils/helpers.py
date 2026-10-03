"""Small, reusable helper functions."""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

APP_NAME = "Student GPA & CGPA Dashboard"
APP_VERSION = "1.0.0"
DB_FILENAME = "student_gpa.db"


def project_root() -> Path:
    """Folder that contains main.py (works from any working directory)."""
    return Path(__file__).resolve().parent.parent


def default_db_path() -> Path:
    return project_root() / DB_FILENAME


def format_gpa(value: float | None, placeholder: str = "-") -> str:
    """Format a GPA to 2 decimal places (internal precision is untouched)."""
    return placeholder if value is None else f"{value:.2f}"


def format_credits(value: float) -> str:
    """Show whole credit hours without a trailing '.0' (3.0 -> '3', 1.5 -> '1.5')."""
    return f"{value:g}"


def today_text() -> str:
    return date.today().strftime("%d %B %Y")


def timestamp_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def show_dash(text: str) -> str:
    """Return ``text`` or an em dash when it is empty (for on-screen display)."""
    return text if text else "\u2014"


def open_file(path: str | Path) -> None:
    """Open a file with the system default application (best effort)."""
    try:
        if sys.platform.startswith("win"):
            os.startfile(str(path))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
    except (OSError, ValueError):
        pass  # opening is a convenience only; the file is already saved


def enable_high_dpi() -> None:
    """Make text crisp on high-DPI Windows displays (no-op elsewhere)."""
    if not sys.platform.startswith("win"):
        return
    try:
        import ctypes

        ctypes.windll.shcore.SetProcessDpiAwareness(1)  # type: ignore[attr-defined]
    except (AttributeError, OSError):
        pass

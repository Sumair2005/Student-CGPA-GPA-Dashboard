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


def is_frozen() -> bool:
    """True when running from the installed (PyInstaller) build."""
    return bool(getattr(sys, "frozen", False))


def project_root() -> Path:
    """Folder holding bundled resources such as ``assets/``.

    Source run: the folder that contains main.py.
    Installed build: PyInstaller's bundle folder.
    """
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent.parent


def user_data_dir() -> Path:
    """Writable per-user folder for the database (the install folder may be read-only)."""
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("XDG_DATA_HOME") \
        or str(Path.home())
    folder = Path(base) / "StudentGPADashboard"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def default_db_path() -> Path:
    if is_frozen():
        return user_data_dir() / DB_FILENAME
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

def set_windows_app_id(app_id: str = "Sumair.StudentGPADashboard.1") -> None:
    """Make Windows show this app's own icon in the taskbar."""
    if not sys.platform.startswith("win"):
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)  # type: ignore[attr-defined]
    except (AttributeError, OSError):
        pass
"""Entry point for the Student GPA & CGPA Dashboard."""

from __future__ import annotations

import sys
import tkinter as tk
from tkinter import messagebox

from database.database import Database, DatabaseError
from ui.app import App
from utils.helpers import APP_NAME, default_db_path, enable_high_dpi


def main() -> int:
    enable_high_dpi()
    try:
        database = Database(default_db_path())
    except DatabaseError as exc:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(APP_NAME, f"The application could not start.\n\n{exc}")
        root.destroy()
        return 1

    app = App(database)
    app.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())

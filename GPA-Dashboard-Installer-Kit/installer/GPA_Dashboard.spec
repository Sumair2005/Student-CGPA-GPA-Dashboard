# PyInstaller spec - windowed, folder-style app (fast start, fewer AV false positives)
import os, sys

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))
ICON = os.path.join(ROOT, "assets", "app_icon.ico")

a = Analysis(
    [os.path.join(ROOT, "main.py")],
    pathex=[ROOT],
    binaries=[],
    datas=[(os.path.join(ROOT, "assets"), "assets")],
    hiddenimports=["matplotlib.backends.backend_tkagg", "PIL._tkinter_finder"],
    hookspath=[],
    runtime_hooks=[],
    excludes=["PyQt5", "PyQt6", "PySide2", "PySide6", "wx", "IPython", "pytest",
              "scipy", "pandas", "tests"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="StudentGPADashboard",
    console=False,
    icon=ICON if sys.platform == "win32" else None,
    upx=False,
)

coll = COLLECT(exe, a.binaries, a.datas, name="StudentGPADashboard", upx=False)

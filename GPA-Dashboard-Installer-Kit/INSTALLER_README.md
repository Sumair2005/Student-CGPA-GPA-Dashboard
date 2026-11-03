# Building the Setup.exe

1. Double-click **`build_installer.bat`** (Windows + Python 3.10+ + internet, once).
2. Wait for it to finish. The installer appears in **`build\installer\`**:
   `StudentGPADashboard_Setup_1.0.0.exe`
3. Send that single file to any 64-bit Windows 10/11 PC. Double-click, Next, Install. No Python needed there.

Notes
- Installs with Start Menu + optional Desktop shortcut and an uninstaller.
- Each PC gets its own fresh database in `%LOCALAPPDATA%\StudentGPADashboard\` (kept on uninstall). Your personal `student_gpa.db` is NOT included.
- Version/publisher are at the top of `installer\setup.iss`.
- Unsigned installers may trigger SmartScreen: *More info > Run anyway*.

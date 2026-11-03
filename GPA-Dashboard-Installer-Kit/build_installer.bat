@echo off
setlocal
cd /d "%~dp0"
title Building Student GPA Dashboard installer

echo.
echo === [1/4] Checking Python ===
set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY ( where python >nul 2>nul && set "PY=python" )
if not defined PY (
  echo Python 3.10+ was not found. Install it from https://www.python.org/downloads/ ^(tick "Add python.exe to PATH"^) and run this again.
  pause & exit /b 1
)

echo.
echo === [2/4] Creating build environment and installing packages ===
if not exist ".build-venv\Scripts\python.exe" %PY% -m venv .build-venv || goto :fail
".build-venv\Scripts\python.exe" -m pip install --upgrade pip || goto :fail
".build-venv\Scripts\python.exe" -m pip install -r requirements.txt pyinstaller || goto :fail

echo.
echo === [3/4] Building the app with PyInstaller ===
if exist build\dist rmdir /s /q build\dist
if exist build\work rmdir /s /q build\work
".build-venv\Scripts\python.exe" -m PyInstaller installer\GPA_Dashboard.spec --noconfirm --distpath build\dist --workpath build\work || goto :fail

echo.
echo === [4/4] Creating Setup.exe with Inno Setup ===
set "ISCC="
for %%P in ("%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" "%ProgramFiles%\Inno Setup 6\ISCC.exe" "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe") do if exist %%P set "ISCC=%%~P"
if not defined ISCC (
  echo Inno Setup not found - trying to install it with winget...
  winget install -e --id JRSoftware.InnoSetup --accept-package-agreements --accept-source-agreements
  for %%P in ("%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" "%ProgramFiles%\Inno Setup 6\ISCC.exe" "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe") do if exist %%P set "ISCC=%%~P"
)
if not defined ISCC (
  echo Could not find Inno Setup. Install it from https://jrsoftware.org/isdl.php then run this again.
  pause & exit /b 1
)
"%ISCC%" installer\setup.iss || goto :fail

echo.
echo ================================================================
echo  DONE.  Your installer is in:  build\installer\
echo  Send  StudentGPADashboard_Setup_1.0.0.exe  to any Windows PC.
echo ================================================================
start "" "build\installer"
pause
exit /b 0

:fail
echo.
echo BUILD FAILED - see the messages above.
pause
exit /b 1

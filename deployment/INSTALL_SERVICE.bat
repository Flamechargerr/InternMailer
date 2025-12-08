@echo off
REM InternMailer - Windows Service Setup (Simple Version)
REM Run this script to install JARVIS as Windows service

echo ============================================
echo    JARVIS Windows Service Installer
echo ============================================
echo.

REM Get paths
set SCRIPT_DIR=%~dp0
set PYTHON_EXE=python
set JARVIS_SCRIPT=%SCRIPT_DIR%jarvis_mode.py

echo [1/3] Checking Python...
%PYTHON_EXE% --version
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python or add to PATH
    pause
    exit /b 1
)
echo OK - Python found
echo.

echo [2/3] Creating VBS launcher...
(
echo Set WshShell = CreateObject^("WScript.Shell"^)
echo WshShell.Run "cmd /c cd /d %SCRIPT_DIR% ^&^& %PYTHON_EXE% jarvis_mode.py --start", 0, False
echo Set WshShell = Nothing
) > "%SCRIPT_DIR%run_jarvis_hidden.vbs"
echo OK - VBS launcher created
echo.

echo [3/3] Creating Windows Task...
echo This requires Administrator privileges.
echo.

REM Create the scheduled task
schtasks /Create /TN "JARVIS_InternMailer" /TR "wscript.exe \"%SCRIPT_DIR%run_jarvis_hidden.vbs\"" /SC ONSTART /RU "%USERNAME%" /RL HIGHEST /F

if errorlevel 1 (
    echo.
    echo ERROR: Failed to create task
    echo.
    echo Please run this as Administrator:
    echo   1. Right-click this file
    echo   2. Select "Run as administrator"
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================
echo    SUCCESS! JARVIS is now installed!
echo ============================================
echo.
echo What this means:
echo   - JARVIS runs on Windows startup
echo   - JARVIS survives terminal close
echo   - JARVIS survives Antigravity close
echo   - JARVIS runs in background (no window)
echo.
echo To manage JARVIS:
echo   Start:  schtasks /Run /TN JARVIS_InternMailer
echo   Stop:   taskkill /F /IM python.exe
echo   Remove: schtasks /Delete /TN JARVIS_InternMailer /F
echo.
echo Starting JARVIS now...
schtasks /Run /TN JARVIS_InternMailer
echo.
echo DONE! Close this window. JARVIS is running!
echo.
pause

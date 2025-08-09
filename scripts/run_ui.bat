@echo off
setlocal

REM Simple batch wrapper to launch the Streamlit UI via PowerShell

set PS=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe
if not exist "%PS%" (
  echo PowerShell not found. Please run scripts\run_ui.ps1 manually.
  exit /b 1
)

REM Pass -Enhanced if first argument is ENHANCED
if /I "%1"=="ENHANCED" (
  "%PS%" -ExecutionPolicy Bypass -File "%~dp0run_ui.ps1" -Enhanced
) else (
  "%PS%" -ExecutionPolicy Bypass -File "%~dp0run_ui.ps1"
)

endlocal

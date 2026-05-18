@echo off
setlocal
title Local AI Control Center Setup

set SCRIPT_DIR=%~dp0
set INSTALL_SCRIPT=%SCRIPT_DIR%install\windows\install.ps1

echo Local AI Control Center - Windows Setup
echo.
echo This bootstrap will:
echo   1. Prepare the LocalQwenHome workspace
echo   2. Check dependencies and install OpenCode
echo   3. Clone or verify llama.cpp
echo   4. Prepare the Control Center launchers
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%INSTALL_SCRIPT%"
set EXITCODE=%ERRORLEVEL%
echo.
if %EXITCODE% EQU 0 (
  echo Setup finished successfully.
) else (
  echo Setup failed with exit code %EXITCODE%.
)
pause
exit /b %EXITCODE%

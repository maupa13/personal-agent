@echo off
setlocal
cd /d "%~dp0"
echo ============================================================
echo Personal Agent Rus - first run / install / update
echo ============================================================

rem If this canonical root was already installed, VERIFY-PACKAGE.ps1 is an
rem installed-root proxy. Re-running RUN-FIRST must start/verify the existing
rem app instead of trying to stage the proxy as a new signed package.
if exist "%~dp0app\START.cmd" if exist "%~dp0VERIFY-PACKAGE.ps1" (
  findstr /C:"Installed application verifier is missing" "%~dp0VERIFY-PACKAGE.ps1" >nul 2>nul
  if not errorlevel 1 (
    echo [INFO] Existing canonical installation detected.
    echo [INFO] Starting and verifying the installed application; no reinstall is needed.
    call "%~dp0app\START.cmd"
    exit /b %ERRORLEVEL%
  )
)

call "%~dp0INSTALL-OR-UPDATE.cmd"
exit /b %ERRORLEVEL%

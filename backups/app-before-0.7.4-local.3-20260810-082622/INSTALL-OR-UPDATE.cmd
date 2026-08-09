@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0INSTALL-OR-UPDATE.ps1" %*
set "EC=%ERRORLEVEL%"
if not "%EC%"=="0" (
  echo.
  echo [FAILED] Personal Agent Rus installation/update failed with exit code %EC%.
  echo No Docker volumes were deleted.
  pause
)
exit /b %EC%

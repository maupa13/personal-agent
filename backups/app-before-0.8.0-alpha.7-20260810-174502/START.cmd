@echo off
setlocal
cd /d "%~dp0"
echo [INFO] Preflight: verifying signed package and Windows lifecycle contract...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0VERIFY-PACKAGE.ps1"
set "EC=%ERRORLEVEL%"
if not "%EC%"=="0" (
  echo.
  echo [FAILED] Preflight verification failed. Docker was not started.
  pause
  exit /b %EC%
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\pa.ps1" -Action start
set "EC=%ERRORLEVEL%"
if not "%EC%"=="0" (
  echo.
  echo [FAILED] Personal Agent Rus start failed with exit code %EC%.
  if exist "%~dp0logs\PERSONAL-AGENT-LAST.log" echo Log: %~dp0logs\PERSONAL-AGENT-LAST.log
  pause
)
exit /b %EC%

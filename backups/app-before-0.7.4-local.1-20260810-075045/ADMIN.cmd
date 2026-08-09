@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\pa.ps1" -Action admin
set "EC=%ERRORLEVEL%"
if not "%EC%"=="0" (
  echo.
  echo [FAILED] Personal Agent Rus command failed with exit code %EC%.
  if exist "%~dp0logs\PERSONAL-AGENT-LAST.log" echo Log: %~dp0logs\PERSONAL-AGENT-LAST.log
  pause
)
exit /b %EC%

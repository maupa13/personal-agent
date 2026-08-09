@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\pa.ps1" -Action codeverify
set "EC=%ERRORLEVEL%"
if not "%EC%"=="0" (
  echo.
  echo [FAILED] Personal Agent Rus Code acceptance failed with exit code %EC%.
  if exist "%~dp0logs\PERSONAL-AGENT-LAST.log" echo Log: %~dp0logs\PERSONAL-AGENT-LAST.log
)
exit /b %EC%

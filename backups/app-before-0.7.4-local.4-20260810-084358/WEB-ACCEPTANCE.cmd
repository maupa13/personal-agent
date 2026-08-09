@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\pa.ps1" -Action webverify
set "ec=%ERRORLEVEL%"
if not "%ec%"=="0" (
  echo.
  echo [FAILED] Personal Agent Rus Web acceptance failed with exit code %ec%.
  echo Log: %~dp0logs\PERSONAL-AGENT-LAST.log
)
exit /b %ec%

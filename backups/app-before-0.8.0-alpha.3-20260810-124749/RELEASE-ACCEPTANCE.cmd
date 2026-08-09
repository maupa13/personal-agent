@echo off
setlocal
cd /d "%~dp0"
echo [INFO] Running the complete pre-reboot reference-host release acceptance.
echo [INFO] This covers FULL-ACCEPTANCE, RESTART, REPAIR and STOP/START without deleting named volumes.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\pa.ps1" -Action releaseverify
set "EC=%ERRORLEVEL%"
if not "%EC%"=="0" (
  echo.
  echo [FAILED] Personal Agent Rus release acceptance failed with exit code %EC%.
  if exist "%~dp0logs\PERSONAL-AGENT-LAST.log" echo Log: %~dp0logs\PERSONAL-AGENT-LAST.log
  pause
)
exit /b %EC%

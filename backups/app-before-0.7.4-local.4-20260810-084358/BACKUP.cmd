@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\pa.ps1" -Action backup
set "EC=%ERRORLEVEL%"
if not "%EC%"=="0" pause
exit /b %EC%

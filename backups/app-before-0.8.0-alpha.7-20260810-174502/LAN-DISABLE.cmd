@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\lan.ps1" -Action disable
exit /b %ERRORLEVEL%

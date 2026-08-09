@echo off
setlocal
cd /d "%~dp0"
echo ============================================================
echo Personal Agent Rus - first run / install / update
echo ============================================================
call "%~dp0INSTALL-OR-UPDATE.cmd"
exit /b %ERRORLEVEL%

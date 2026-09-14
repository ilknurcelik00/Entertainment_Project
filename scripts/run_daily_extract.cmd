@echo off
setlocal

set "PROJECT_DIR=%~dp0.."
"%PROJECT_DIR%\.venv\Scripts\python.exe" "%PROJECT_DIR%\src\extract\run_daily_extract.py"

exit /b %ERRORLEVEL%

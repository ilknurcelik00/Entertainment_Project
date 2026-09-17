@echo off
setlocal

set "PROJECT_DIR=%~dp0.."
"%PROJECT_DIR%\.venv\Scripts\python.exe" "%PROJECT_DIR%\src\db\load_warehouse.py"

exit /b %ERRORLEVEL%

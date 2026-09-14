@echo off
setlocal
set "PROJECT_DIR=%~dp0.."
"%PROJECT_DIR%\.venv\Scripts\python.exe" "%PROJECT_DIR%\src\db\load_source_staging.py" tvmaze
exit /b %ERRORLEVEL%

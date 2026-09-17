@echo off
setlocal

chcp 65001 >nul
set "JAVA_TOOL_OPTIONS=-Duser.language=en -Duser.country=US -Dfile.encoding=UTF-8"
set "PROJECT_DIR=%~dp0.."
set "HOP_AUDIT_FOLDER=%PROJECT_DIR%\logs\hop-audit"

if not exist "%PROJECT_DIR%\logs" mkdir "%PROJECT_DIR%\logs"
if not exist "%HOP_AUDIT_FOLDER%" mkdir "%HOP_AUDIT_FOLDER%"

cd /d C:\hop

call hop-run.bat ^
  -j=default ^
  -r=local ^
  -f="%PROJECT_DIR%\hop\workflows\run_daily_etl.hwf" ^
  -l=BASIC ^
  -lf="%PROJECT_DIR%\logs\run_daily_etl.log"

exit /b %ERRORLEVEL%

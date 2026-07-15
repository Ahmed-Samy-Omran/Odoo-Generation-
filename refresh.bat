@echo off
setlocal
cd /d "%~dp0"
echo.
echo Running Backend refresh...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0refresh.ps1" %*
if errorlevel 1 (
  echo.
  echo Refresh failed.
  pause
  exit /b 1
)
echo.
pause

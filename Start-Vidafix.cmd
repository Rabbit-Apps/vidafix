@echo off
setlocal DisableDelayedExpansion
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run Setup-Windows.cmd first.
  pause
  exit /b 1
)
echo Vidafix: keep this window open. Ctrl+C stops the server.
".venv\Scripts\python.exe" -m tools.windows run
pause

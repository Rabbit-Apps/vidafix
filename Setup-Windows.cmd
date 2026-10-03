@echo off
setlocal DisableDelayedExpansion
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -m tools.windows setup
) else (
  where py >nul 2>&1
  if errorlevel 1 (
    python -m tools.windows setup
  ) else (
    py -3 -m tools.windows setup
  )
)
if errorlevel 1 echo Setup failed. Install Python from python.org and check the message above.
pause

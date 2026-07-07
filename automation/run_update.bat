@echo off
REM FOMC dashboard auto-update (refresh + publish). Run by Windows Task Scheduler.
REM %~dp0 = this scripts\ folder; %~dp0.. = repo root (works with any path).
set SENTIMENT_ENGINE=finbert
set PYTHONUTF8=1
cd /d "%~dp0.."
if not exist logs mkdir logs
echo ==== %DATE% %TIME% : update start ==== >> "logs\scheduler.log"
".venv\Scripts\python.exe" update.py >> "logs\scheduler.log" 2>&1
echo ==== %DATE% %TIME% : update end (exit %ERRORLEVEL%) ==== >> "logs\scheduler.log"

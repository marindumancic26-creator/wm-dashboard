@echo off
rem Taeglicher Matchday-Lauf — manuell oder per Windows Task Scheduler.
rem Task-Scheduler-Setup (einmalig, KEINE Automation ohne deine Zustimmung aktiv):
rem   schtasks /Create /TN "WM-Dashboard Daily" /TR "\"%~dp0run_daily.bat\"" /SC DAILY /ST 09:00
cd /d "%~dp0"
python -m src.pipeline.daily_matchday_run >> data\snapshots\run_log.txt 2>&1

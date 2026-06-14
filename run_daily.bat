@echo off
rem Taeglicher Matchday-Lauf — laeuft automatisch per Windows Task Scheduler (09:00),
rem solange der Rechner an ist. KEINE App/Claude noetig.
rem Task-Setup (einmalig): schtasks /Create /TN "WM-Dashboard Daily" /TR "\"%~dp0run_daily.bat\"" /SC DAILY /ST 09:00
cd /d "%~dp0"

rem 1) Pipeline: Daten laden, simulieren, docs/index.html erzeugen
python -m src.pipeline.daily_matchday_run >> data\snapshots\run_log.txt 2>&1

rem 2) Auto-Push der Handy-Ansicht zu GitHub Pages (nutzt gespeicherte Git-Credentials).
rem    Faellt still aus, falls keine Aenderung oder kein Internet.
git add docs/index.html >> data\snapshots\run_log.txt 2>&1
git commit -m "Auto-Update Dashboard %date% %time%" >> data\snapshots\run_log.txt 2>&1 || echo keine Aenderung >> data\snapshots\run_log.txt
git push >> data\snapshots\run_log.txt 2>&1

@echo off
rem Taeglicher Matchday-Lauf — laeuft automatisch per Windows Task Scheduler (09:00),
rem solange der Rechner an ist. KEINE App/Claude noetig.
rem Task-Setup (einmalig): schtasks /Create /TN "WM-Dashboard Daily" /TR "\"%~dp0run_daily.bat\"" /SC DAILY /ST 09:00
cd /d "%~dp0"

rem 0) Repo aktuell ziehen (immer synchron bleiben). --autostash sichert lokale Aenderungen,
rem    --rebase haelt die Historie linear. Faellt still aus ohne Internet.
git pull --rebase --autostash >> data\snapshots\run_log.txt 2>&1

rem 1) Pipeline: Daten laden, simulieren, docs/index.html erzeugen
python -m src.pipeline.daily_matchday_run >> data\snapshots\run_log.txt 2>&1

rem 2) ALLES Getrackte committen + pushen, damit das GitHub-Repo immer aktuell ist
rem    (data/, .claude/, __pycache__ sind gitignored -> nur Code/quality/memory/docs).
git add -A >> data\snapshots\run_log.txt 2>&1
git commit -m "Daily run %date% %time%" >> data\snapshots\run_log.txt 2>&1 || echo keine Aenderung >> data\snapshots\run_log.txt
git push >> data\snapshots\run_log.txt 2>&1

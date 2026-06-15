@echo off
rem Hermes-Analyse-Schicht (LLM) — laeuft taeglich 09:15 per Windows Task Scheduler,
rem nach dem 09:00-Pipeline-Task (run_daily.bat). Schreibt Narrativ + Lernen, kein Quellcode.
rem Voraussetzung fuer UNBEAUFSICHTIGTEN Lauf: ANTHROPIC_API_KEY als Umgebungsvariable
rem (das Claude-Abo erlaubt keinen headless-Lauf). Ohne Key wird sauber uebersprungen.
rem Task-Setup (einmalig):
rem   schtasks /Create /TN "WM-Dashboard Hermes" /TR "\"%~dp0hermes_daily.bat\"" /SC DAILY /ST 09:15 /F
cd /d "%~dp0"
echo ===== Hermes %date% %time% ===== >> data\snapshots\hermes_log.txt

if "%ANTHROPIC_API_KEY%"=="" (
  echo Kein ANTHROPIC_API_KEY gesetzt - Hermes-LLM-Schicht uebersprungen. >> data\snapshots\hermes_log.txt
  echo Die deterministische Lernschicht ^(Pipeline + closing_loop-Report^) lief bereits um 09:00. >> data\snapshots\hermes_log.txt
  goto :end
)

"C:\Users\marin\.local\bin\claude.exe" -p "Lies HERMES.md in diesem Projekt und fuehre die taegliche Hermes-Analyse aus (Schritte 2 bis 5). Die Pipeline lief bereits heute Morgen. Lies den heutigen Snapshot data/processed/dashboard_data.json und die Dateien in memory/daily_runs/ vom heutigen Datum. Schreibe das Hermes-Narrativ in den heutigen closing_loop-Report (memory/daily_runs, Datei endet auf _closing_loop.md) unter der Ueberschrift Hermes-Analyse, und haenge einen datierten Eintrag an memory/learnings.md an. Halte dich strikt an die Leitplanken in HERMES.md und aendere KEINEN Quellcode." --permission-mode acceptEdits >> data\snapshots\hermes_log.txt 2>&1

:end
echo ===== Hermes fertig %date% %time% ===== >> data\snapshots\hermes_log.txt

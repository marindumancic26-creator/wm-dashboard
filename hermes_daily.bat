@echo off
rem Hermes-Analyse-Schicht (LLM) via CODEX — laeuft taeglich 09:15 per Windows Task Scheduler,
rem nach dem 09:00-Pipeline-Task (run_daily.bat). Schreibt Narrativ + Lernen, KEIN Quellcode.
rem
rem Laeuft headless ueber 'codex exec' mit deinem CODEX/ChatGPT-Login (im Abo enthalten,
rem KEIN Anthropic-Key, KEINE metered API-Kosten). Das loest das fruehere headless-claude-Problem.
rem Task-Setup (einmalig):
rem   schtasks /Create /TN "WM-Dashboard Hermes" /TR "\"%~dp0hermes_daily.bat\"" /SC DAILY /ST 09:15 /F
cd /d "%~dp0"
echo ===== Hermes (Codex) %date% %time% ===== >> data\snapshots\hermes_log.txt

rem OPENAI_API_KEY ausblenden -> Codex nutzt den ChatGPT-Login (abo-inklusive statt metered API).
set "OPENAI_API_KEY="

"C:\Users\marin\AppData\Roaming\npm\codex.cmd" exec -C "." -s workspace-write -c approval_policy="never" --skip-git-repo-check -o "data\snapshots\hermes_last.md" "Lies HERMES.md in diesem Projekt und fuehre die taegliche Hermes-Analyse aus (Schritte 2 bis 5). Die Pipeline lief heute Morgen bereits per run_daily.bat. Lies den heutigen Snapshot data/processed/dashboard_data.json und die heutigen Dateien in memory/daily_runs/. Schreibe das Hermes-Narrativ in den heutigen closing_loop-Report (Datei in memory/daily_runs/ die auf _closing_loop.md endet) unter der Ueberschrift '## Hermes-Analyse', und haenge einen datierten Eintrag an memory/learnings.md an. Halte dich strikt an die Leitplanken in HERMES.md und aendere KEINEN Quellcode." >> data\snapshots\hermes_log.txt 2>&1

rem Hermes-Output (Narrativ + learnings.md) noch heute syncen — Codex laeuft sandboxed ohne Git,
rem daher hier im normalen Shell committen+pushen (Credentials gespeichert).
git add -A >> data\snapshots\hermes_log.txt 2>&1
git commit -m "Hermes-Analyse %date%" >> data\snapshots\hermes_log.txt 2>&1 || echo keine Hermes-Aenderung >> data\snapshots\hermes_log.txt
git push >> data\snapshots\hermes_log.txt 2>&1

echo ===== Hermes fertig %date% %time% ===== >> data\snapshots\hermes_log.txt

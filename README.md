# WM 2026 — Prognose-Dashboard

Lokales Dashboard für FIFA-WM-2026-Spielprognosen: Ensemble aus Polymarket-Marktpreisen,
Elo/StatsBomb-Modell und heuristischem Whale-Signal, mit Monte-Carlo-Simulation.

> ⚠️ Keine Finanz- oder Wettberatung. Prognosemärkte können fehlerhaft, illiquide,
> manipuliert oder unvollständig sein.

## Schnellstart
```
pip install -r requirements.txt
python -m src.pipeline.daily_matchday_run   # Daten laden + simulieren (~1–2 min)
python app.py                               # Dashboard: http://127.0.0.1:5050
python -m tests.test_model                  # Sanity-Tests
```

## Aufs Handy (kostenlos, GitHub Pages)
Der Daily-Run erzeugt `docs/index.html` — eine self-contained Datei (Daten inline, kein Server).
1. Kostenloses GitHub-Repo anlegen, Projekt pushen (oder nur den `docs/`-Ordner).
2. Repo → **Settings → Pages → Source: Branch `main`, Ordner `/docs`**.
3. URL `https://<dein-user>.github.io/<repo>` am Handy öffnen, zum Homescreen hinzufügen.
4. Jeder `git push` nach einem Daily-Run aktualisiert die Handy-Ansicht.

Manuell exportieren: `python -m src.pipeline.export_static`. Alternativ via OneDrive-App öffnen.

## Täglicher Lauf (automatisiert)
Läuft per Windows Task Scheduler **täglich 09:00** automatisch (Task „WM-Dashboard Daily").
Manuell: `run_daily.bat`. Task-Verwaltung:
```
schtasks /Query  /TN "WM-Dashboard Daily"           # Status
schtasks /Run    /TN "WM-Dashboard Daily"           # sofort ausführen
schtasks /Change /TN "WM-Dashboard Daily" /ST 11:00 # Uhrzeit ändern
schtasks /Delete /TN "WM-Dashboard Daily" /F        # entfernen
```
Outputs: `data/snapshots/<datum>_<uhrzeit>.json`, `data/processed/dashboard_data.json`,
`memory/daily_runs/<datum>.md`, `memory/daily_runs/<datum>_closing_loop.md` (automatischer
Lern-Report), `memory/matches/<slug>.md` (Obsidian-kompatibel).

Die **narrative Hermes-Analyse** (tiefes Reasoning, Gewichtungsentscheidungen) liefert Claude
auf Anfrage — der deterministische Zahlen-Report entsteht täglich von selbst, ohne Claude.

## API-Keys (optional, kostenlos — schalten Zusatzquellen frei)
Datei `api_keys.json` im Projektroot anlegen:
```json
{ "odds_api": "DEIN_KEY", "football_data": "DEIN_KEY", "openweather": "OPTIONAL_KEY" }
```
- `odds_api` → [the-odds-api.com](https://the-odds-api.com) (Buchmacher-Quoten, Pinnacle, 4. Ensemble-Quelle)
- `football_data` → [football-data.org](https://www.football-data.org/client/register) (Ergebnisse → Brier-Kalibrierung)
- `openweather` → [openweathermap.org](https://openweathermap.org/api) (optional: Wetter-Kontext fürs Modell)

Alternativ als Umgebungsvariablen `ODDS_API_KEY` / `FOOTBALL_DATA_API_KEY`.
Ohne Keys laufen diese Quellen als `unavailable`, alles andere funktioniert normal.

## StatsBomb-API (optional)
Mit kostenpflichtigem Zugang: `SB_USERNAME`/`SB_PASSWORD` als Umgebungsvariablen setzen →
Client wechselt automatisch von Open Data (historisch, WM 2018/2022) auf API (`live`).

## Dokumentation
- [memory/project.md](memory/project.md) — Projektgedächtnis, offene Punkte
- [memory/data_sources.md](memory/data_sources.md) — Quellenstatus & Grenzen
- [memory/model_logic.md](memory/model_logic.md) — Modell- und Ensemble-Logik

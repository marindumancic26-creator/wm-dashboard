# Projektgedächtnis — WM 2026 Prognose-Dashboard

Stand: 2026-06-14

## Review-Abnahme (14.06.) — abgearbeitet
Security (DOM-XSS `esc()`, `</script>`-Breakout-Fix, Chart-SRI, Wallet-Anonymisierung im
Public-Export), ehrlicher Value-Tab (Warn-Banner), RPS-Metrik, Shin-De-Vig, Ausreißer-Filter,
Whale-Shift-Cap (max 8pp), UTC-aware Snapshots, Wetter-Forecast statt aktuell, Dependency-Pins,
GitHub-Actions-CI, LICENSE, Parser-/Mapping-Tests (28 Tests). **Elo wird live täglich aktualisiert**
(eloratings.net) → alter „Elo-Snapshot"-Gap gelöst.
**K.o.-Weiterkommen (14.06. gebaut, `knockout.py`):** 90-Min-1X2 + Verlängerung (1/3 Tor-Erwartung)
+ Elfmeter (~50/50). Stage-Erkennung über football-data.org-Fixtures (`results_client.fetch_fixtures`,
104 Spiele, Stages GROUP_STAGE…FINAL). Aktiviert sich automatisch ab den K.o.-Spielen; Dashboard
zeigt dann eine „Weiterkommen"-Zeile zusätzlich zum 90-Min-Ergebnis. Tests vorhanden.

**Echte Datengrenzen (bleiben offen — extern bedingt):**
- Lineup/Verletzung automatisch: keine freie Spieler-Stärkequelle → manuelles Override (`adjustments.json`).
- Wetter live: braucht OpenWeather-Key (Integration + Forecast-Logik fertig, inaktiv bis Key).
- Ensemble-Gewichte-Retuning: erst wenn Kalibrierung n≥~15 einen Edge belegt (aktuell n=5;
  Optimizer feuert ab n=8, sonst Prior — Schutz vor Overfitting).

## Ziel
Lokales Dashboard mit Prognosen für WM-2026-Spiele: 1X2, exaktes Ergebnis, Tore pro Team,
Gesamttore, Over/Under, Spielereignisse, Unsicherheitsbänder, Monte-Carlo-Verteilung.
Ensemble aus [[data_sources|drei Quellen]]: Polymarket-Marktpreise, Elo/StatsBomb-Modell, Whale-Signal.

## Architektur
- `src/data_sources/polymarket_client.py` — Gamma + Data API (öffentlich, kein Key)
- `src/data_sources/statsbomb_client.py` — statsbombpy; API-Modus nur mit `SB_USERNAME`/`SB_PASSWORD`, sonst Open Data
- `src/model/features.py` — Elo-Prior, StatsBomb-Korrektur, markt-implizite λ (Grid-Search)
- `src/model/whale_scoring.py` — heuristisches Wallet-Scoring mit Shrinkage
- `src/model/ensemble.py` — gewichtete Mischung, Renormalisierung bei Quellenausfall
- `src/model/monte_carlo.py` — 20.000 Läufe, Gamma-Parameterunsicherheit
- `src/pipeline/daily_matchday_run.py` — täglicher Lauf, Snapshots + Markdown
- `app.py` + `templates/dashboard.html` — Flask-Dashboard auf Port 5050

## Bedienung
- Täglicher Lauf: **automatisch per Task Scheduler 09:00** (Task „WM-Dashboard Daily");
  manuell `python -m src.pipeline.daily_matchday_run` oder `run_daily.bat`
- Dashboard: `python app.py` → http://127.0.0.1:5050 (nur zum Anschauen nötig)
- Tests: `python -m tests.test_model`
- Automatischer Lern-Report: `memory/daily_runs/<datum>_closing_loop.md` (deterministisch,
  ohne Claude). Narrative Hermes-Analyse on demand. Cloud-Agent verworfen, weil er keinen
  Zugriff auf die lokalen OneDrive-Dateien hätte ([[learnings]]).

## Wichtige Entscheidungen
Siehe [[model_logic]]. Kurz: Markt 50 % / Modell 30 % / Whale 20 % (Whale zusätzlich
konfidenz-gedämpft). Unabhängige Poisson-Tore, Baseline 2,6 Tore/Spiel,
Gastgeber-Bonus +60 Elo für USA/MEX/CAN.

## Wettmarkt & EV (Dashboard-Block „Wettmarkt & Expected Value")
- 1X2 + Über/Unter: echte API-Quoten (40 Bücher), EV konservativ, Value-Bets + Beobachtungsliste.
- Zusatzmärkte (BTTS/DC/DNB): Modell-Fairquoten immer sichtbar; recherchierte Web-/manuelle
  Quoten + EV erscheinen, sobald sie in `data/processed/extra_markets.json` stehen (key=slug).
  Diese Datei pflegt Claude bei On-Demand-Recherche oder aus Nutzer-Screenshots; sie wird vom
  Daily Run NICHT überschrieben (app.py merged sie beim Ausliefern). Server nach Code-Änderung
  an app.py neu starten, sonst greift der Merge nicht.

## Roadmap (nach Quant-Review 13.06.)
**Sofort/Danach — alle umgesetzt 13.06.:**
- [x] CLV-Capture + Log Loss/Hit-Rate/ROI in `calibration.py` → `_closing_loop.md` + Dashboard
- [x] `model_version`-Fingerprint (config.MODEL_VERSION) in jedem Snapshot
- [x] Datenqualitäts-Score (`data_quality.py`) als Einsatz-Gate (Ampel im Cockpit)
- [x] **Backtest-Harness** (`backtest.py`, WM 18/22, 5-fold-CV) → `memory/backtest_report.md`
- [x] **Bivariate-Poisson-Engine** mit getrennter Angriff/Abwehr (`attack_defense_lambdas`,
      ELO_PER_GOAL=240 marktkalibriert) — Modell-vs-Markt-Fehler 10,2 %→5,6 %
- [x] Dashboard-Cockpit (alle Spiele sortierbar) + Value-Ranking + CSV-Export + DQ-Ampel
- [x] σ-basierte konservative EV-Grenze + Liquiditäts-Gate (`value_betting.py`)

**Später — umgesetzt 13.06.:**
- [x] Höhe (`venue_client.py`, statisch via ESPN-Stadt) + Wetter (OpenWeather, optionaler Key)
- [x] Aufstellungs-/Verletzungs-**Override** (`injuries.py` + `data/processed/adjustments.json`) ins Modell
- [x] Quotenverlauf-Chart (`/api/odds-history` + Dashboard) — füllt sich über Snapshots
- [x] Kalibrierung-über-Zeit-Chart (kumulativer Brier); Reliability-Diagramm folgt ab n≈20
- [x] Korrelationsbewusstes Staking (Cap 2 %/Spiel + 6 % gesamt in `value_betting.portfolio`)
- [x] Schiedsrichter: bewusst weggelassen (keine saubere freie Quelle)
- [~] xG-Form: Engine nutzt FBref-xG automatisch, sobald für die WM gefüllt (aktuell Tor-basiert)
- [ ] ELO_PER_GOAL bei mehr Spielen nachjustieren (tests/tune_elo.py); Wetter-Key eintragen für Live-Wetter

## Gewichte & Handy (13.06., 2. Runde)
- [x] **Gewichts-Optimizer** (`weight_optimizer.py`): datenbasierte Empfehlung aus Kalibrierung
      (Inverse-LogLoss + Shrinkage α=n/(n+15)), erst ab n≥8, sonst Prior. Im Report+Dashboard,
      NICHT auto-angewandt. Aktuell n=1 → Prior. Bei genug Daten config.ENSEMBLE_WEIGHTS nachziehen.
      Offen/Caveat: Markt/Bücher/Kalshi korreliert → Block-Behandlung wäre sauberer.
- [x] **Static-Export** (`export_static.py` → `docs/index.html`, self-contained) fürs Handy/GitHub Pages.
      Dashboard-Template erkennt `window.__STATIC_DATA__` und läuft serverlos. Visuell verifiziert.

## Offene Punkte / nächste Schritte
- [x] StatsBomb Open-Data-Repo geklont (2026-06-12, nach Rücksprache, als Sparse-Clone 393 MB)
      → `C:\Users\marin\statsbomb-open-data` (außerhalb OneDrive; Override `STATSBOMB_OPEN_DATA_DIR`).
      Event-Level-xG (WM 18/22) fließt jetzt 50/50 mit Toren in die Angriffs-/Abwehrfaktoren ([[model_logic]]).
- [ ] Elo-Snapshot regelmäßig aktualisieren (aktuell statisch, [[data_sources]])
- [x] Dixon-Coles-Korrektur (rho=-0,10) umgesetzt 13.06. — analytisch + MC (Importance-Weighting),
      Remis +2–2,6 pp. Siehe [[learnings]] und [[model_logic]].
- [ ] Whale-Scoring: Backtesting gegen aufgelöste Gruppenspiele, sobald genug Spiele resolved sind
- [ ] Kalibrierungs-Tracking: prognostizierte vs. eingetretene Ergebnisse je Daily Run sammeln
- [ ] K.o.-Runden: Verlängerung/Elfmeterschießen modellieren (aktuell nur 90-Minuten-1X2 wie Polymarket)

## Verlauf
- 2026-06-13: Quellen 4–6 integriert: Kalshi (5. Ensemble-Quelle, API-Fallen siehe
  [[data_sources]] §8), ESPN-Status/Aufstellungen (Badge + Lineup-Panel), FBref-Turnierform
  via soccerdata (gedämpfter λ-Multiplikator). **USA-Bug behoben:** Polymarket-Slugs tragen
  US-Ostküsten-Daten; Discovery schließt jetzt den Vortag ein (späte Spiele = 03:00 MESZ).
  FotMob-API tot (404, Auth) → ESPN als Ersatz. Kalshi-Preise heute konsistent mit
  Polymarket/Pinnacle (±1 pp) — guter Sanity-Check.
- 2026-06-12 (spät): Drei neue Quellen integriert: (1) The Odds API (Pinnacle/Median, de-vigged,
  4. Ensemble-Quelle `books`, Gewichte jetzt 35/25/25/15), (2) eloratings.net live (244 Teams,
  ersetzt statischen Snapshot, Fallback bleibt), (3) football-data.org Ergebnisse +
  Brier-Kalibrierung je Quelle im Dashboard. Keys fehlen noch für (1)+(3) → `unavailable`-Fallback
  aktiv; Eintrag in `api_keys.json` oder Umgebungsvariablen genügt ([[data_sources]]).
  Beobachtung: Live-/beendete Spiele konvergieren im Markt Richtung Endstand (CAN-BIH 99,9 % Remis)
  — Anzeige „Spiel beendet/laufend" wäre ein sinnvoller nächster Schritt.
- 2026-06-12: Projekt aufgesetzt, erster erfolgreicher Daily Run (5 Spiele, Spieltag 12./13.06.).
  Fixes: Polymarket-Tag ist `fifa-world-cup` (nicht `world-cup`); Schweiz-Code ist `che`.

<!-- Hermes — automatischer Tages-Agent für das WM-Dashboard -->
# HERMES.md — Täglicher Lern-Agent

Dies ist die Anleitung für den **automatischen Tageslauf**. Ein geplanter Claude-Lauf (oder der
Nutzer) führt sie 1×/Tag aus. Ziel: jeden Tag aus den frischen Spielen lernen, die Prognosegüte
verfolgen und Gewichts-/Modellanpassungen vorschlagen — schnell, weil oft mehrere Spiele/Tag.

## Ablauf (in dieser Reihenfolge)

1. **Pipeline laufen lassen** (deterministisch, ohne LLM):
   ```
   cd "C:\Users\marin\OneDrive\Dokumente\Fußball wahrscheinlichkeit"
   python -m src.pipeline.daily_matchday_run
   ```
   Erzeugt: `data/snapshots/<ts>.json`, `data/processed/dashboard_data.json`,
   `docs/index.html`, `memory/daily_runs/<datum>.md`, `memory/daily_runs/<datum>_closing_loop.md`,
   `memory/matches/<slug>.md`. Bei Fehlern: `run_log.matches_failed` im Snapshot prüfen.

2. **Ergebnis lesen** — den deterministischen Lernreport + Kalibrierung:
   - `memory/daily_runs/<datum>_closing_loop.md` (Brier/RPS/LogLoss je Quelle, ROI/CLV, Auto-Flags)
   - `calibration` + `weights_suggestion` aus dem Snapshot/`dashboard_data.json`.

3. **Hermes-Narrativ schreiben** — die intelligente Schicht, die der deterministische Report
   bewusst offenlässt. Hänge sie an `memory/daily_runs/<datum>_closing_loop.md` unter
   `## Hermes-Analyse` an. Inhalt (kurz, konkret, mit Zahlen):
   - Welche Quelle kalibriert aktuell am besten/schlechtesten (rollierend, n beachten)?
   - Auffällige Treffer/Fehlprognosen des Tages — warum? (Elo-Snapshot veraltet? StatsBomb dünn?
     Markt-Modell-Diskrepanz?)
   - Schlägt das Ensemble den reinen Markt (Brier/RPS)? Wenn nicht: woran liegt's?
   - CLV/ROI-Tendenz (sobald Snapshots Tage auseinanderliegen).

4. **Lernen festhalten** — hänge an `memory/learnings.md` einen datierten Eintrag mit
   **konkreten, überprüfbaren** Lehren an (kein Bauchgefühl). Format:
   ```
   ## <YYYY-MM-DD>
   - [Beobachtung] <Quelle/Parameter> <Metrik vorher→nachher / n>
   - [Hypothese] <was das bedeutet>
   - [Aktion] <konkrete Anpassung ODER "abwarten bis n≥X">
   ```

5. **Gewichts-/Parameter-Empfehlung** — `weights_suggestion` lesen.
   - `status="prior"` (n < MIN_N=8): nichts ändern, nur notieren „n=… , warte".
   - `status="data-driven"`: die empfohlenen Gewichte im Narrativ nennen. **Nicht automatisch**
     `config.ENSEMBLE_WEIGHTS` ändern — das ist eine Menschen-Entscheidung (Real-Geld-Semantik,
     `MODEL_VERSION`-Vergleichbarkeit). Erst vorschlagen, bei klarer Datenlage (z.B. n≥15,
     stabil über mehrere Tage) zur Übernahme empfehlen.
   - Auto-Flags aus dem Report ernst nehmen (Whale hochvariant → defensiv bleiben; Modell
     schwach kalibriert → Elo/Gastgeber-Annahmen prüfen).

6. **Backtest gelegentlich** (nicht täglich nötig): `python -m src.model.backtest` validiert
   die Angriff/Abwehr-Struktur + rho out-of-sample gegen StatsBomb 2018/22. Bei Modelländerungen
   ausführen und `memory/backtest_report.md` prüfen.

## Leitplanken (wichtig)
- **Niemals** Stake-Caps, Liquiditäts-Gate, Korrelations-Cap oder den Disclaimer aufweichen.
- Keine automatische Gewichtsänderung vor **n≥8** (Überanpassung an Einzelspiele).
- Tests müssen grün bleiben, wenn Code angefasst wird:
  `python -m pytest quality/test_functional.py quality/test_regression.py tests/test_model.py -q`
- Markt/Bücher/Kalshi sind **korreliert** — nicht als drei unabhängige Belege werten.
- Qualitätssystem & bekannte offene Punkte: siehe `quality/` und `AGENTS.md`.

## Schnelles Lernen — warum das funktioniert
Bei mehreren Spielen/Tag wächst `n_resolved` rasch. Brier/RPS/LogLoss je Quelle und der
ROI/CLV-Track liefern nach wenigen Tagen ein belastbares Bild; `weight_optimizer` schlägt dann
datenbasierte Gewichte vor. Der Hermes-Eintrag in `memory/learnings.md` ist das Gedächtnis,
das jeden Tag genau einen Schritt klüger wird.

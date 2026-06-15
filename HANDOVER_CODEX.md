# Übergabe an Codex — WM-2026-Prognose-Dashboard

> Stand: 2026-06-15 · Autor: Claude (Opus 4.8). Dieses Dokument ist die Übergabe, damit du
> (Codex) hier kalt weitermachen kannst. Lies zuerst `AGENTS.md`, `HERMES.md` und `quality/`.

---

## 0. TL;DR — wo wir stehen
Funktionierendes, getestetes Quant-Dashboard für die FIFA WM 2026: zieht Prognosemärkte
(Polymarket, Kalshi), Buchmacherquoten und Fußballstatistik, berechnet 1X2-/Tor-/Value-Bet-
Wahrscheinlichkeiten, trackt die eigene Treffergüte und läuft **vollautomatisch** (3 Windows-
Tasks + Codex-Hermes-Lernschicht). Code ist sauber und durch ein vollständiges Quality-Playbook
gegangen (**10 Bugs gefunden, alle gefixt + TDD-verifiziert**). Suite grün:
`python -m pytest quality/test_functional.py quality/test_regression.py tests/test_model.py -q`.

---

## 1. Architektur (Fullstack-Sicht)

```
data_sources/                model/                         pipeline/
  polymarket_client   ─┐       features (λ-Engines,        daily_matchday_run (Orchestrator)
  odds_client (Bücher) │        Poisson, Dixon-Coles)        ↓ schreibt:
  kalshi_client        ├─►      ensemble (Quellen-Blend)    data/snapshots/<ts>.json
  elo_client           │        monte_carlo (gewichtet)     data/processed/dashboard_data.json
  fbref_client         │        value_betting (EV/Kelly)    docs/index.html (self-contained)
  statsbomb_client     │        data_quality (Ampel-Gate)   memory/daily_runs/*.md + matches/*.md
  espn/venue/results ──┘        calibration (Scoring+ROI+CLV+records)
                                weight_optimizer / closing_loop / knockout / whale_scoring / backtest
app.py  = Flask-Dashboard :5050 (TEMPLATES_AUTO_RELOAD=True)   templates/dashboard.html
```

Datenfluss pro Spiel: Polymarket-Discovery → Snapshot (Preise/Trades/Holder) →
`features.attack_defense_lambdas` (Elo+StatsBomb+Form+Venue) + Markt/Bücher/Kalshi/Whale-Probs →
`ensemble.blend_probs`/`blend_lambdas` → `monte_carlo.simulate` → `value_betting.evaluate_match`
→ `data_quality.score_match` → `apply_quality_gate` → Portfolio → Persistenz + Export.

**Graceful Degradation überall:** jede Quelle ist status-getaggt (`live`/`historical`/`estimated`/
`unavailable`) und fällt sauber zurück; die Pipeline läuft mit jeder Teilmenge an Quellen.

---

## 2. Das Modell (Quant-Sicht)

**Engine:** Bivariate Poisson mit getrennter Angriff/Abwehr (`features.attack_defense_lambdas`):
- Elo-Differenz → erwartete Tordifferenz (`ELO_PER_GOAL=240`, gegen Markt getunt via `tests/tune_elo.py`)
- StatsBomb-(xG-)Prior + FBref-Turnierform als geshrunkene Angriff/Abwehr-Multiplikatoren
- Dixon-Coles-Korrektur `rho=-0.10` (hebt 0:0/1:1, senkt 1:0/0:1)
- Spielort-Kontext (Höhe/Wetter), optionales Verletzungs-Override

**Ensemble:** gewichteter Blend aus market/books/kalshi/model/whale (`config.ENSEMBLE_WEIGHTS`),
renormalisiert bei Ausfall; **Whale-Gate** begrenzt die Whale-Verschiebung auf max. 0.08.
`blend_lambdas` leitet die MC-Torstruktur aus der besten Preisquelle ab (Polymarket > Bücher > Kalshi).

**Monte Carlo:** 20 000 Läufe, Parameter-Unsicherheit per Gamma-Sampling (CV=0.12),
Dixon-Coles per Importance-Weighting. **Unsicherheitsband = echte Parameter-Unsicherheit**
(seit BUG-002-Fix: feste λ-Resamples, invariant gegen `MC_RUNS`).

**Value/Staking:** konservative Untergrenze = `min(Modell, scharfer Markt) − Z·σ`, Viertel-Kelly,
per-Tier-Cap, per-Match-Korrelations-Cap, Portfolio-Cap, Liquiditäts-Gate (≥3 Bücher),
Datenqualitäts-Ampel-Gate (rot unterdrückt Value).

**Kalibrierung/Lernen:** Brier, LogLoss, **RPS (ordinal, der richtige Score für 1X2)**, Hit-Rate,
ROI, CLV, `model_version`. Leakage-Schutz (nur Pre-Kickoff-Snapshots). `weight_optimizer` schlägt
datenbasierte Gewichte vor (Inverse-LogLoss + Shrinkage, **nicht** auto-angewandt).

**Trefferbilanz (Cockpit, `calibration.records`):** favorit (Tendenz 1X2), favorit_klar (nur
Ensemble-p>50%), tore (Ü/U 2.5), beide_treffen (BTTS), ergebnis (exakter Endstand).

### Aktueller Performance-Stand (n=8 — winzig, NICHT signifikant)
| Metrik | Wert |
|--------|------|
| Favorit (Tendenz) | 4/8 · 50% |
| Favorit nur bei p>50% | 3/6 · 50% |
| Tore (Ü/U 2.5) | 3/8 · 37,5% |
| Beide treffen (BTTS) | 2/8 · 25% |
| Exaktes Ergebnis | 0/8 · 0% (erwartbar selten) |
| Ø Brier | Kalshi 0.650 · **Ensemble 0.650** · Markt 0.657 · Modell 0.725 |
| Gewichts-Vorschlag (n=8) | market 0.276 / books 0.244 / kalshi 0.147 / model 0.198 / whale 0.135 |

---

## 3. Quant-Bewertung — Stärken & Risiken (ehrlich)

**Stärken:** prinzipielle Unsicherheit (echte Parameter-Unsicherheit), konservatives Staking,
korrekte Scoring-Regeln (RPS), leakage-geschützte Kalibrierung, out-of-sample-validierte
Modellstruktur (`backtest.py`, WM18/22 5-fold), saubere Quellen-Degradation.

**Risiken / offene Quant-Punkte (Priorität für dich):**
1. **Korrelierte Quellen (HOCH):** market/books/kalshi sind alle „der Markt" → Inverse-LogLoss-
   Weighting **übergewichtet den Markt-Block**. `weight_optimizer` dokumentiert das, korrigiert
   es aber nicht. → Block-Behandlung einbauen (Markt-Block als EINE Stimme, dann intern aufteilen).
2. **Kleines n (HOCH):** alles auf n=8. Nichts ist signifikant. **Keine Gewichtsänderung vor n≥15–30**
   und Stabilität über mehrere Tage. Reliability-Diagramm erst ab ~n≥20 sinnvoll.
3. **Modell schlechter als Markt (HOCH):** Modell-Brier 0.725 > Markt 0.657. Gegen den Markt zu
   wetten auf Modell-Edge ist statistisch (noch) nicht gerechtfertigt. Value-„Chancen" kommen v.a.
   vom **unvalidierten Whale-Signal** — im Dashboard ehrlich so gelabelt. → ggf. Modellgewicht
   senken, bis es sich beweist; ELO_PER_GOAL/rho auf mehr Daten neu tunen (aktuell gegen Markt
   getunt → Risiko, den Markt statt die Realität zu fitten).
4. **Whale heuristisch (MITTEL):** keine verifizierte P&L-Historie öffentlich; hochvariant
   (Brier 0.001–1.74). Durch 0.08-Cap begrenzt — gut — aber speist weiter die Chancen-Liste.
5. **Stale Priors (MITTEL):** StatsBomb nur WM 2018/2022, kein 2026; FBref-xG für WM leer → nur
   Tor-Form als aktuelles Signal. CLV noch nicht messbar (Snapshots zu eng) — wird aussagekräftig,
   sobald Daily-Runs Tage im Voraus laufen.

**Quant-Roadmap (konkret):** (a) korrelationsbewusstes Weighting/Staking, (b) Reliability-Diagramm
+ Kalibrierungs-Plot ab n≥20, (c) ELO_PER_GOAL & rho datenbasiert nachtunen, (d) Modellgewicht
adaptiv an bewiesene Güte koppeln, (e) CLV-Tracking sobald Vorlauf da, (f) optional hierarchisches/
bayesianisches Team-Stärke-Modell statt Punkt-Schätzern.

---

## 4. Automation (läuft vollautomatisch)
| Task | Zeit | Was | Runner | Kosten |
|------|------|-----|--------|--------|
| WM-Dashboard Daily | 09:00 | pull → Pipeline → push | Python | – |
| WM-Dashboard Hermes | 09:15 | narrative Analyse + `memory/learnings.md` | **`codex exec`** (ChatGPT-Login) | abo-inklusive |
| WM-Dashboard Daily Abend | 23:00 | neue Tagesergebnisse → Kalibrierung → push | Python | – |

`run_daily.bat`: `git pull --rebase --autostash` → `python -m src.pipeline.daily_matchday_run` →
`git add -A` + commit + `git push`. `hermes_daily.bat`: `set "OPENAI_API_KEY="` (→ ChatGPT-Login,
kein Anthropic-Key) → `codex exec -C "." -s workspace-write -c approval_policy="never"` folgt
`HERMES.md` → danach git push. **`approval_policy="never"` ist Pflicht** (sonst hängt Codex).

---

## 5. Konventionen & Leitplanken (NICHT verletzen)
- **Niemals** Stake-Caps, Liquiditäts-Gate, Korrelations-Cap, Whale-Gate oder den Disclaimer aufweichen.
- **Keine Auto-Gewichtsänderung vor n≥8** (Default-Schutz); Übernahme erst bei stabiler Datenlage (n≥15+).
- **Tests müssen grün bleiben:** `python -m pytest quality/test_functional.py quality/test_regression.py tests/test_model.py -q`. Bei Code-Änderung an `monte_carlo`/`value_betting`/`ensemble` IMMER mitlaufen lassen.
- Markt/Bücher/Kalshi sind **korreliert** — nicht als drei unabhängige Belege werten.
- Kommentare/Strings auf Deutsch (Codebase-Stil). Module-Docstrings sind der Vertrag — Code-vs-Docstring nicht driften lassen.
- Secrets (`api_keys.json`) sind gitignored — niemals committen. Env-Vars haben Vorrang.
- Real-Geld-Semantik: Änderungen an Staking-Mathe / Whale-Gewicht / Tier-Schwellen sind Menschen-Entscheidung.

## 6. Stolperfallen (gelernt)
- Flask `debug=False` cachte das Template → neue Cockpit-Karten unsichtbar bis Server-Neustart. Fix: `TEMPLATES_AUTO_RELOAD=True`; Browser ggf. hart neu laden (Strg+F5).
- Codex läuft sandboxed → kein `git` darin (safe.directory) → Push steht NACH dem codex-Aufruf im Batch. Harmloser `rmcp transport`-Fehler beim Codex-Start ignorierbar.
- Projekt liegt in `C:\Users\marin\OneDrive\Dokumente\Fußball wahrscheinlichkeit` (Pfad mit ß + Leerzeichen). Polymarket-Tag `fifa-world-cup`, Slug `fifwc-<code>-<code>-<datum>` (US-Datum, ±1 Tag), Schweiz=`che`.
- `simulate(runs<200)` crashte früher (BUG-001, gefixt); `canonical_team(None)` crashte (BUG-010, gefixt).

## 7. Konkrete nächste Tasks für dich (priorisiert)
1. **Korrelationsbewusstes Weighting** in `weight_optimizer.py` (Markt-Block als eine Stimme). + Test.
2. **Reliability-/Kalibrierungs-Plot** im Dashboard, aktiv ab n≥20 (Daten kommen täglich).
3. **CLV-Tracking schärfen** sobald Snapshots Tage auseinanderliegen (`calibration._clv` ist da).
4. **ELO_PER_GOAL & rho neu tunen** auf der wachsenden echten Slate (nicht nur gegen Markt).
5. **Modellgewicht adaptiv** an gemessene Brier-Güte koppeln (vorsichtig, mit Cap).
6. Optional: Whale-Wallets im Cockpit als Polymarket-Profil-Links; weitere Trefferarten (DC/DNB).

## 8. Schnellstart
```
# Dashboard lokal:        python app.py            -> http://127.0.0.1:5050
# Einen Lauf manuell:     python -m src.pipeline.daily_matchday_run   (--skip-whales = schneller)
# Tests:                  python -m pytest quality/test_functional.py quality/test_regression.py tests/test_model.py -q
# Backtest (Modellstruktur): python -m src.model.backtest
# Quality-System:         quality/  (EXPLORATION, REQUIREMENTS, BUGS, writeups, COVERAGE_MATRIX)
```
Repo: github.com/marindumancic26-creator/wm-dashboard (origin/main, Auto-Sync via Daily-Tasks).

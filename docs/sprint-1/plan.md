# Sprint 1 — Prospektive Club-Lockbox

> Sprint Goal: Eine leakage-freie, append-only Shadow-Lockbox erzeugen und auswerten.
> Branch: bestehender lokaler Arbeitsbaum; kein Push ohne Nutzerfreigabe
> Estimated effort: ein fokussierter Implementierungs- und QA-Zyklus

## Prioritized Task List

| # | Task | Owner | Description |
|---|---|---|---|
| 1 | Manifest und Schemas | Sage | Kandidat, Cutoff, Hashes und Guardrails einfrieren |
| 2 | Append-only Store | Sage | atomare create-only JSON-Artefakte, Idempotenz, Konflikte |
| 3 | Prospektive Evaluation | Sage | gleiche Spiele, ehrliche Coverage, Versionstrennung |
| 4 | P0-Vertragstests | Sage | UTC, Leakage, Duplikate, Tamper, fehlendes Closing |
| 5 | Unabhängige QA | Ivy | Regression und Gate-Audit |

## Work Schedule

### Phase 1: Core

- Pure Validierung und kanonische Serialisierung
- Forecast/Closing/Result getrennt speichern
- Hash-Manifest und Integritätsprüfung

### Phase 2: Evaluation

- feste Cutoff-Regel und gepaarte Metriken
- roher Markt plus `alpha=0`-Ablation
- blockierende Coverage-/Stichproben-/Versions-Gates

### Phase 3: QA und Handoff

- gezielte Lockbox-Tests
- vollständige vorgeschriebene Suite
- Progress, Done und QA-Sign-off aktualisieren

## Success Criteria

- [ ] create-only und idempotent; Konflikte überschreiben niemals Daten
- [ ] alle Zeitstempel explizit UTC und strikt vor dem festen Cutoff
- [ ] fehlende Closing-Captures bleiben im Coverage-Nenner
- [ ] Kandidatenversionen werden nie gemeinsam aggregiert
- [ ] Rohmarkt und `alpha=0`-Kalibrator sind getrennte Benchmarks
- [ ] `auto_apply`, Prediction, Value und Stakes bleiben gesperrt
- [ ] vollständige Testsuite grün

## What's NOT in This Sprint

| Feature | Reason |
|---|---|
| automatische Wettfreigabe | statistische Prospektiv-Gates nicht erfüllt |
| produktive Club-Odds-Abfrage | eigener liga-spezifischer Adapter noch erforderlich |
| Dashboard-Umbau | Lockbox-Core und Evidenz zuerst |
| GitHub-Push/Deployment | nicht vom Nutzer autorisiert |


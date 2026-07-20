# Sprint 1 — Progress Tracker

## Task Status

| # | Task | Status | Notes |
|---|---|---|---|
| 1 | Team-Consilium | Done | Sage, Vega und Ivy read-only abgeschlossen |
| 2 | Manifest/Schemas | In progress | Erste Fassung durch QA abgelehnt; P0-Härtung läuft |
| 3 | Append-only Store | In progress | Datei-Atomizität okay, Population-Ledger fehlt noch |
| 4 | Evaluation/Gates | In progress | Normative Gates und Capture-Bindung werden ergänzt |
| 5 | QA/Sign-off | Blocked | 161 Tests grün, aber P0-Negativreproduktionen offen |

## Bugs Found

| # | Description | Severity | Status | Fix |
|---|---|---|---|---|
| 1 | Shadow-Export ist überschreibbar und nicht atomar | major | open | Sprint 1 |
| 2 | Historische Closing-Coverage filtert Missing vor dem Nenner | major | open | Lockbox-Evaluator getrennt korrekt bauen |
| 3 | Residual-Vorteil ist überwiegend Markt-Rekalibrierung | major | open | alpha=0-Ablation verpflichtend |
| 4 | Forecast-Löschung kann Coverage künstlich erhöhen | blocker | fixing | unveränderliches Population-Ledger |
| 5 | Rückdatierte Forecasts/zu frühe Resultate werden akzeptiert | blocker | fixing | strikte Typed-Schemas und Chronologie |
| 6 | Normative Gates lassen sich zur Laufzeit abschwächen | blocker | fixing | Gates vollständig im Manifest einfrieren |
| 7 | Forecast und Benchmark teilen nicht zwingend denselben Capture | major | fixing | capture_id-/Zeit-/Kickoff-Bindung |
| 8 | Signierte Artefakte zwischen Match-Pfaden wiederverwendbar | blocker | fixing | Payload-/Pfad-/Digest-Bindung |
| 9 | FINAL exakt zum Anstoß akzeptiert | blocker | fixing | manifestierte Result-Finalität und finished_at |
| 10 | Evaluationstermine unvollständig validiert | blocker | fixing | alle Checkpoints validieren und create-only verbrauchen |
| 11 | Bootstrap nutzt 2,5/97,5 statt einseitig 5/95 | blocker | fixing | protokollkonforme Quantile |
| 12 | Payload-Zeitstempel beweisen keinen realen Schreibzeitpunkt | blocker | fixing | systemseitiger Receipt-Zeitpunkt vor T-5 |
| 13 | Resultat besitzt keinen vertrauenswürdigen Writer-Receipt | blocker | fixing | written_at und Future-Result-Sperre |
| 14 | Checkpoint kann spätere Artefakte lesen/gelöscht neu entstehen | blocker | fixing | Zeitfenster und verkettete Evaluation-Receipts |
| 15 | Ein Saison-Epoch kann definitive Stichprobe nie erreichen | major | fixing | hashgebundene Multi-Epoch-Cohort-Auswertung |
| 16 | Completeness dupliziert das 98%-Coverage-Gate | major | fixing | informativ statt definitiver Konjunktion |

## Notes

Die bestehenden uncommitted Änderungen am Closing-Residual-Backtest gehören zum vorherigen
Arbeitsschritt und werden nicht überschrieben. Keine Produktivfreigabe in diesem Sprint.

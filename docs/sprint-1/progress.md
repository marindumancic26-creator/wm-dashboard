# Sprint 1 — Progress Tracker

## Task Status

| # | Task | Status | Notes |
|---|---|---|---|
| 1 | Team-Consilium | Done | Sage, Vega und Ivy read-only abgeschlossen |
| 2 | Manifest/Schemas | Done | vollständig typisiert, versioniert und hashgebunden |
| 3 | Append-only Store | Done | Population, Records, Reservations und Receipts create-only |
| 4 | Evaluation/Gates | Done | raw/alpha0, Liga, Guardrails, Checkpoints und Cohorts |
| 5 | QA/Sign-off | Done | 186 Tests grün; unabhängiger Race-/Governance-Sign-off |

## Bugs Found

| # | Description | Severity | Status | Fix |
|---|---|---|---|---|
| 1 | Shadow-Export war überschreibbar | major | fixed | separater append-only Lockbox-Store |
| 2 | Missing verschwand aus Coverage | major | fixed | Population-Ledger ist der Nenner |
| 3 | Modellanteil vs. Marktkalibrierung unklar | major | fixed | raw und alpha0 Pflichtbenchmarks |
| 4 | Forecast-Löschung erhöhte Coverage | blocker | fixed | Ledger- und Completeness-Prüfung |
| 5 | Backfill/zu frühe Resultate | blocker | fixed | trusted Writer-Receipts und Chronologie |
| 6 | Gates zur Laufzeit abschwächbar | blocker | fixed | normative Manifest-Gates |
| 7 | Capture-Bindung fehlte | major | fixed | identische capture_id/Zeit/Probs |
| 8 | Cross-match Envelope-Replay | blocker | fixed | Pfad/Payload/ID/Digest-Bindung |
| 9 | Falsche Finalitätsgrenze | blocker | fixed | finished_at, Mindestdauer, Quelle |
| 10 | Checkpoint-/Cohort-Peeking | blocker | fixed | Reservations, Receipt-Chain, Hypothesenregistry |
| 11 | Falsche Bootstrap-Quantile | blocker | fixed | einseitige 5/95-Quantile |
| 12 | Same-second Timestamp-Race | blocker | fixed | UTC-Receipts mit sechs Mikrosekundenstellen |
| 13 | Einzelepoch erreicht Langzeitschwelle nicht | major | fixed | disjunkte Multi-Epoch-Cohort-Auswertung |
| 14 | Completeness duplizierte Coverage | major | fixed | informativ; 98%-Gate bleibt normativ |

## Notes

Sprint 1 ist technisch abgeschlossen. Keine Produktivfreigabe: `release`, Auto-Apply,
Prediction, Value und Stakes bleiben false. Akzeptierte lokale Trust-Grenzen sind die nicht
extern attestierte Systemzeit und das fehlende externe WORM-/Transparency-Log.

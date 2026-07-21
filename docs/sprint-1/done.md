# Sprint 1 — Done

## What Was Built

- versioniertes, create-only Lockbox-Manifest und Population-Ledger
- strikt typisierte Forecast-, Closing-, Result- und Official-Close-Artefakte
- T-5-Capture-Bindung mit trusted Writer-Receipts und Mikrosekundenpräzision
- ehrliche Coverage über die vorab definierte Population
- raw-Closing- und alpha0-Pflichtbenchmarks mit ungerundeten RPS-/LogLoss-Deltas
- einseitiger Cluster-Bootstrap, Liga- und Guardrail-Gates
- create-only Checkpoint-Reservations, Receipt-Kette und Cohort-Hypothesenbindung
- disjunkte Multi-Epoch-Cohort-Auswertung ohne Retuning
- permanente Sperren für Release, Auto-Apply, Prediction, Value und Stakes

## What's NOT Done

- keine Live-Club-Odds-, Prognose- oder Resultquellen angebunden
- kein externer WORM-, Signatur- oder Transparency-Log-Anker
- keine extern attestierte Systemzeit
- keine allgemeine Amendment-Chain für spätere Fixture-Korrekturen
- Official Close wird gespeichert, aber noch nicht sekundär aggregiert

## Files Changed/Created

- `src/model/club_lockbox.py` — Lockbox-Core, Persistenz und Evaluation
- `tests/test_club_lockbox.py` — 41 Lockbox-/Angriffstests
- `PROJECT_BRIEF.md` — gemeinsamer Projektstatus
- `docs/lockbox-design.md` — Team-Consilium und Beschlüsse
- `docs/sprint-1/` — Plan, Protokoll, QA und Handoff

## Manual Setup Required

Keine Secrets oder Deployments. Vor Live-Shadowbetrieb müssen liga-spezifische Quoten- und
Resultadapter sowie ein externer Hash-Anker separat implementiert und freigegeben werden.

## Known Issues

Ein privilegierter Host kann lokale Uhr und Dateisystem manipulieren. Die lokale Lockbox ist
create-only und tamper-evident, aber ohne externen Anker kein kryptografisches WORM-System.

## Verification

- `python -m pytest -q` — 186 passed
- `python -m py_compile src/model/club_lockbox.py` — passed
- `git diff --check` — passed (nur erwarteter LF/CRLF-Hinweis)


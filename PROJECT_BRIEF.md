# PROJECT_BRIEF.md — Fußball-Wahrscheinlichkeit

> Last updated: 2026-07-20 | Sprint 1 | Status: In Progress

## 1. Project Overview

Das Projekt erzeugt täglich nachvollziehbare Fußball-Wahrscheinlichkeiten aus Markt-,
Buchmacher- und Statistikquellen. Der aktuelle Produktionspfad bedient die WM 2026; ein
Vereinsmodus läuft ausschließlich im Shadowbetrieb. Geldnahe Aussagen bleiben durch
Qualitäts-, Liquiditäts-, Korrelations- und Freigabe-Gates geschützt.

## 2. Concept / Product Description

Die Pipeline entdeckt Spiele, normalisiert Identitäten, erzeugt 1X2- und Tormodelle,
vergleicht sie mit Märkten und veröffentlicht ein statisches Dashboard. Der neue
Lockbox-Pfad friert prospektive Vereinsprognosen, Markt-Captures und spätere Resultate
getrennt und unveränderlich ein. Er dient nur dem Nachweis einer Out-of-sample-Edge und
schaltet weder Prognosen noch Value-Bets automatisch frei.

## 3. Tech Stack

- **Frontend:** selbstenthaltendes HTML-Dashboard
- **Backend:** Python 3, requests, NumPy/Pandas, dateibasierte JSON-Artefakte
- **Hosting:** GitHub Pages für das Dashboard; lokale Windows-Tasks für Daily Runs
- **Testing:** pytest, funktionale und Regressionstests
- **CI/CD:** GitHub Actions plus lokale Watchdog-Skripte

## 4. Architecture

```text
Fixture-Quellen -> kanonische Match-ID -> Shadow-Prognose/Markt-Capture
                                            |
                                            v
                              append-only Lockbox + Hash-Manifest
                                            |
Ergebnisquelle -----------------------------+
                                            v
                         gepaarte RPS-/LogLoss-Auswertung
                                            |
                                            v
                             blockierender Readiness-Report
```

## 5. Key Files Map

| Area | Path | Contents |
|---|---|---|
| Daily entry point | `src/pipeline/daily_matchday_run.py` | produktiver WM-Lauf |
| Club fixtures | `src/pipeline/club_shadow_run.py` | fixture-first Shadowlauf |
| Club validation | `src/model/club_backtest.py` | Walk-forward und Closing-Gates |
| Domain | `src/domain/football.py` | Identität und Pre-Kickoff-Replay |
| Lockbox | `src/model/club_lockbox.py` | append-only Core und Evaluation |
| Tests | `tests/test_model.py` | Modell-, Pipeline- und Lockbox-Verträge |
| Sprint docs | `docs/sprint-1/` | Plan, Fortschritt und Handoff |

## 6. Team Roles

| Agent | Name | Role |
|---|---|---|
| Producer | Remy | Scope, Koordination und Handoff |
| Backend | Sage | Lockbox-Core und Integration |
| Quant | Vega | Leakage, Benchmarks und Freigabe-Governance |
| QA | Ivy | unabhängige Tests und Sign-off |

## 7. Sprint Status

| Sprint | Name | Status | Scope |
|---|---|---|---|
| 1 | Prospektive Club-Lockbox | In Progress | unveränderliche Records, Evaluation, Tests |

## 8. Current State

**What works:** kanonische Club-Fixtures, Shadow-Quellen, historischer Walk-forward,
Closing-Gates und ein aggregiert knapp besserer Residualkandidat.

**What doesn't work yet:** Der bisherige Shadow-Export ist überschreibbar und enthält
keine eingefrorenen Prognosen/Quoten/Resultate. Eine Live-Club-Modell- und Quotenpipeline
ist noch nicht vollständig vorhanden.

**What's next:** Lockbox-Core abschließen, danach liga-spezifische Odds-Captures und echte
Shadow-Prognosen anbinden, ohne den Produktionspfad zu verändern.

## 9. Security Rules

1. Secrets bleiben ausschließlich in Umgebungsvariablen oder gitignorierten Key-Dateien.
2. Lockbox-Artefakte enthalten keine API-Keys, Header oder personenbezogenen Daten.
3. Rohartefakte sind create-only; Hash-/Schemafehler blockieren die Auswertung.
4. `auto_apply`, `prediction_allowed`, `value_allowed` und Stakes bleiben false.

## 10. How to Run Locally

```powershell
python -m src.pipeline.club_shadow_run --all --days 7
python -m pytest quality/test_functional.py quality/test_regression.py tests/test_model.py -q
```

## 11. How to Deploy

Dieser Sprint hat kein Deployment. Nach Tests werden Änderungen zunächst nur lokal bzw.
in einer Feature-Änderung geprüft. Die bestehende Daily-/Pages-Automation bleibt unberührt;
eine spätere Aktivierung erfordert die vollständigen Gates und menschliche Freigabe.

## 12. Cross-Chat Handoff Protocol

Jeder Sprint aktualisiert `docs/sprint-1/progress.md`, schreibt zum Abschluss
`docs/sprint-1/done.md` und aktualisiert die Abschnitte 7 und 8 dieses Briefs. Entscheidungen,
offene Risiken, Testresultate und manuelle Voraussetzungen werden in Dateien festgehalten.
Kein Agent darf annehmen, dass Chat-Kontext erhalten bleibt; das Repository ist das
gemeinsame Gedächtnis. Commits oder Pushes erfolgen nur nach ausdrücklicher Nutzerfreigabe.

## 13. Bug & Fix Tracking

Bestehende Qualitätsdefekte werden in `quality/BUGS.md` geführt. Neue Lockbox-Probleme
werden im Sprint-Tracker mit Reproduktion, Erwartung, Ist-Zustand und Schweregrad erfasst;
bei autorisiertem GitHub-Workflow werden daraus Issues. QA verändert keinen Produktivcode,
sondern meldet Befunde an Sage. Ein Sign-off nennt Testzahl, Passrate und Blocker explizit.

## 14. Multi-Repo Setup

Der importierte Skill empfiehlt getrennte Klone und Feature-Branches. In dieser Codex-
Sitzung teilen Subagenten technisch einen Arbeitsbaum; deshalb werden Schreibbereiche
seriell und rollenbasiert vergeben: Sage schreibt Core/Tests, Ivy prüft read-only, Remy
koordiniert Dokumentation. Es wird weder rebased noch force-pushed oder direkt gepusht.
Für eine spätere externe Teamarbeit gelten getrennte Klone, reguläre Merge-PRs und keine
Squash-/Rebase-Merges.


# Parameter-Tuning-Report

Status: **diagnostic**
n=90 | Diagnose ab n>=20 | Uebernahme erst ab n>=50

## Aktuelle Config

- ELO_PER_GOAL: `240.0`
- DIXON_COLES_RHO: `-0.1`
- BASELINE_TOTAL_GOALS: `2.6`

## rho-Anker

- rho: `-0.1` (config fallback, fallback)
- Hinweis: Keine StatsBomb-WM-Daten geladen.

## Headline: Walk-forward ELO_PER_GOAL

| ELO_PER_GOAL | RPS | LogLoss | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|
| 180 | 0.1419 | 0.6928 | 0.0098 | 45 |
| 200 | 0.1451 | 0.7079 | 0.0066 | 45 |
| 220 | 0.1484 | 0.7227 | 0.0033 | 45 |
| 240 | 0.1517 | 0.7364 | 0.0 | 45 |
| 260 | 0.1549 | 0.7494 | -0.0032 | 45 |
| 280 | 0.158 | 0.7612 | -0.0063 | 45 |
| 320 | 0.1637 | 0.7818 | -0.012 | 45 |

## Diagnose: In-sample Score-Flaeche

| ELO_PER_GOAL | RPS | LogLoss | Brier | Hit | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|---:|---:|
| 180 | 0.1558 | 0.7826 | 0.4527 | 0.7 | 0.0049 | 90 |
| 200 | 0.1572 | 0.7896 | 0.4566 | 0.7 | 0.0035 | 90 |
| 220 | 0.159 | 0.7977 | 0.4611 | 0.7 | 0.0017 | 90 |
| 240 | 0.1607 | 0.8038 | 0.4647 | 0.7 | 0.0 | 90 |
| 260 | 0.1625 | 0.8104 | 0.4686 | 0.7111 | -0.0018 | 90 |
| 280 | 0.1643 | 0.8173 | 0.4726 | 0.7111 | -0.0036 | 90 |
| 320 | 0.168 | 0.8309 | 0.4807 | 0.7111 | -0.0073 | 90 |

## Sanity: Live-rho-Grid (kein Treiber der Empfehlung)

| rho | RPS | LogLoss | Brier | Hit | n |
|---:|---:|---:|---:|---:|---:|
| 0.0 | 0.1601 | 0.7997 | 0.4611 | 0.7 | 90 |
| -0.05 | 0.1604 | 0.8015 | 0.4628 | 0.7 | 90 |
| -0.1 | 0.1607 | 0.8038 | 0.4647 | 0.7 | 90 |
| -0.15 | 0.1611 | 0.8065 | 0.4669 | 0.7 | 90 |
| -0.2 | 0.1615 | 0.8096 | 0.4695 | 0.7 | 90 |

## Kandidat

- ELO_PER_GOAL: `180.0`
- rho: `-0.1`
- Walk-forward RPS: `0.1419`
- Marge gegen aktuelle Config: `0.0098`
- stabil ueber Folds: `True`
- LogLoss-Guard OK: `True`
- Uebernahme-reif: `False`

## Input-Audit

- snapshots: `156`
- resolved: `91`
- entries: `519`
- missing_model_inputs: `126`
- missing_baseline_total_goals: `41`
- cases: `90`

_Keine automatische Aenderung an config.py. Parameter-Aenderungen bleiben Menschenentscheidung._

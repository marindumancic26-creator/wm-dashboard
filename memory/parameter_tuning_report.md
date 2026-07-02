# Parameter-Tuning-Report

Status: **diagnostic**
n=71 | Diagnose ab n>=20 | Uebernahme erst ab n>=50

## Aktuelle Config

- ELO_PER_GOAL: `240.0`
- DIXON_COLES_RHO: `-0.1`
- BASELINE_TOTAL_GOALS: `2.6`

## rho-Anker

- rho: `0.0` (backtest.py StatsBomb WM 2018/22, ok)

## Headline: Walk-forward ELO_PER_GOAL

| ELO_PER_GOAL | RPS | LogLoss | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|
| 180 | 0.1491 | 0.764 | 0.0075 | 36 |
| 200 | 0.1516 | 0.7761 | 0.0051 | 36 |
| 220 | 0.1543 | 0.788 | 0.0024 | 36 |
| 240 | 0.1567 | 0.7959 | 0.0 | 36 |
| 260 | 0.1589 | 0.803 | -0.0023 | 36 |
| 280 | 0.1611 | 0.8101 | -0.0044 | 36 |
| 320 | 0.1653 | 0.824 | -0.0087 | 36 |

## Diagnose: In-sample Score-Flaeche

| ELO_PER_GOAL | RPS | LogLoss | Brier | Hit | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|---:|---:|
| 180 | 0.1582 | 0.8217 | 0.4818 | 0.662 | 0.0025 | 71 |
| 200 | 0.1588 | 0.8257 | 0.4833 | 0.662 | 0.0019 | 71 |
| 220 | 0.1598 | 0.8311 | 0.4857 | 0.662 | 0.0009 | 71 |
| 240 | 0.1607 | 0.8344 | 0.4873 | 0.662 | 0.0 | 71 |
| 260 | 0.1619 | 0.8389 | 0.4894 | 0.662 | -0.0012 | 71 |
| 280 | 0.1632 | 0.844 | 0.492 | 0.662 | -0.0025 | 71 |
| 320 | 0.1661 | 0.8548 | 0.4977 | 0.662 | -0.0054 | 71 |

## Sanity: Live-rho-Grid (kein Treiber der Empfehlung)

| rho | RPS | LogLoss | Brier | Hit | n |
|---:|---:|---:|---:|---:|---:|
| 0.0 | 0.1607 | 0.8344 | 0.4873 | 0.662 | 71 |
| -0.05 | 0.1607 | 0.8337 | 0.4875 | 0.662 | 71 |
| -0.1 | 0.1608 | 0.8336 | 0.488 | 0.662 | 71 |
| -0.15 | 0.161 | 0.834 | 0.4889 | 0.662 | 71 |
| -0.2 | 0.1612 | 0.8349 | 0.49 | 0.662 | 71 |

## Kandidat

- ELO_PER_GOAL: `180.0`
- rho: `0.0`
- Walk-forward RPS: `0.1491`
- Marge gegen aktuelle Config: `0.0075`
- stabil ueber Folds: `False`
- LogLoss-Guard OK: `True`
- Uebernahme-reif: `False`

## Input-Audit

- snapshots: `77`
- resolved: `72`
- entries: `399`
- missing_model_inputs: `126`
- missing_baseline_total_goals: `40`
- cases: `71`

_Keine automatische Aenderung an config.py. Parameter-Aenderungen bleiben Menschenentscheidung._

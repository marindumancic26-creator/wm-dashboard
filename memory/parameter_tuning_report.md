# Parameter-Tuning-Report

Status: **diagnostic**
n=57 | Diagnose ab n>=20 | Uebernahme erst ab n>=50

## Aktuelle Config

- ELO_PER_GOAL: `240.0`
- DIXON_COLES_RHO: `-0.1`
- BASELINE_TOTAL_GOALS: `2.6`

## rho-Anker

- rho: `0.0` (backtest.py StatsBomb WM 2018/22, ok)

## Headline: Walk-forward ELO_PER_GOAL

| ELO_PER_GOAL | RPS | LogLoss | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|
| 180 | 0.1431 | 0.7752 | 0.0052 | 29 |
| 200 | 0.1447 | 0.7828 | 0.0037 | 29 |
| 220 | 0.1466 | 0.7916 | 0.0017 | 29 |
| 240 | 0.1483 | 0.7968 | 0.0 | 29 |
| 260 | 0.15 | 0.8022 | -0.0017 | 29 |
| 280 | 0.1517 | 0.8083 | -0.0034 | 29 |
| 320 | 0.1554 | 0.8211 | -0.0071 | 29 |

## Diagnose: In-sample Score-Flaeche

| ELO_PER_GOAL | RPS | LogLoss | Brier | Hit | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|---:|---:|
| 180 | 0.1638 | 0.8549 | 0.5062 | 0.6491 | 0.0011 | 57 |
| 200 | 0.1638 | 0.8566 | 0.5063 | 0.6491 | 0.0011 | 57 |
| 220 | 0.1644 | 0.8601 | 0.5074 | 0.6491 | 0.0005 | 57 |
| 240 | 0.1649 | 0.8613 | 0.5077 | 0.6491 | 0.0 | 57 |
| 260 | 0.1656 | 0.8639 | 0.5086 | 0.6491 | -0.0007 | 57 |
| 280 | 0.1666 | 0.8674 | 0.5101 | 0.6491 | -0.0017 | 57 |
| 320 | 0.1689 | 0.876 | 0.5141 | 0.6491 | -0.004 | 57 |

## Sanity: Live-rho-Grid (kein Treiber der Empfehlung)

| rho | RPS | LogLoss | Brier | Hit | n |
|---:|---:|---:|---:|---:|---:|
| 0.0 | 0.1649 | 0.8613 | 0.5077 | 0.6491 | 57 |
| -0.05 | 0.1649 | 0.8599 | 0.5076 | 0.6491 | 57 |
| -0.1 | 0.1649 | 0.859 | 0.5078 | 0.6491 | 57 |
| -0.15 | 0.165 | 0.8588 | 0.5083 | 0.6491 | 57 |
| -0.2 | 0.1651 | 0.859 | 0.5091 | 0.6491 | 57 |

## Kandidat

- ELO_PER_GOAL: `180.0`
- rho: `0.0`
- Walk-forward RPS: `0.1431`
- Marge gegen aktuelle Config: `0.0052`
- stabil ueber Folds: `False`
- LogLoss-Guard OK: `True`
- Uebernahme-reif: `False`

## Input-Audit

- snapshots: `69`
- resolved: `58`
- entries: `359`
- missing_model_inputs: `126`
- missing_baseline_total_goals: `40`
- cases: `57`

_Keine automatische Aenderung an config.py. Parameter-Aenderungen bleiben Menschenentscheidung._

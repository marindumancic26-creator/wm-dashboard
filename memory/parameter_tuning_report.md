# Parameter-Tuning-Report

Status: **diagnostic**
n=89 | Diagnose ab n>=20 | Uebernahme erst ab n>=50

## Aktuelle Config

- ELO_PER_GOAL: `240.0`
- DIXON_COLES_RHO: `-0.1`
- BASELINE_TOTAL_GOALS: `2.6`

## rho-Anker

- rho: `0.0` (backtest.py StatsBomb WM 2018/22, ok)

## Headline: Walk-forward ELO_PER_GOAL

| ELO_PER_GOAL | RPS | LogLoss | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|
| 180 | 0.1514 | 0.7177 | 0.0069 | 45 |
| 200 | 0.1535 | 0.7281 | 0.0048 | 45 |
| 220 | 0.1558 | 0.7392 | 0.0025 | 45 |
| 240 | 0.1583 | 0.7499 | 0.0 | 45 |
| 260 | 0.1608 | 0.7604 | -0.0026 | 45 |
| 280 | 0.1633 | 0.7701 | -0.0051 | 45 |
| 320 | 0.168 | 0.7875 | -0.0098 | 45 |

## Diagnose: In-sample Score-Flaeche

| ELO_PER_GOAL | RPS | LogLoss | Brier | Hit | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|---:|---:|
| 180 | 0.1553 | 0.7801 | 0.4512 | 0.6966 | 0.0045 | 89 |
| 200 | 0.1566 | 0.7867 | 0.4544 | 0.6966 | 0.0032 | 89 |
| 220 | 0.1583 | 0.7944 | 0.4584 | 0.6966 | 0.0015 | 89 |
| 240 | 0.1598 | 0.8003 | 0.4616 | 0.6966 | 0.0 | 89 |
| 260 | 0.1615 | 0.8067 | 0.4651 | 0.7079 | -0.0017 | 89 |
| 280 | 0.1633 | 0.8133 | 0.4688 | 0.7079 | -0.0035 | 89 |
| 320 | 0.1669 | 0.8263 | 0.4764 | 0.7079 | -0.0071 | 89 |

## Sanity: Live-rho-Grid (kein Treiber der Empfehlung)

| rho | RPS | LogLoss | Brier | Hit | n |
|---:|---:|---:|---:|---:|---:|
| 0.0 | 0.1598 | 0.8003 | 0.4616 | 0.6966 | 89 |
| -0.05 | 0.1601 | 0.8019 | 0.4632 | 0.6966 | 89 |
| -0.1 | 0.1604 | 0.8041 | 0.465 | 0.6966 | 89 |
| -0.15 | 0.1608 | 0.8067 | 0.4672 | 0.6966 | 89 |
| -0.2 | 0.1612 | 0.8098 | 0.4697 | 0.6966 | 89 |

## Kandidat

- ELO_PER_GOAL: `180.0`
- rho: `0.0`
- Walk-forward RPS: `0.1514`
- Marge gegen aktuelle Config: `0.0069`
- stabil ueber Folds: `False`
- LogLoss-Guard OK: `True`
- Uebernahme-reif: `False`

## Input-Audit

- snapshots: `153`
- resolved: `90`
- entries: `512`
- missing_model_inputs: `126`
- missing_baseline_total_goals: `41`
- cases: `89`

_Keine automatische Aenderung an config.py. Parameter-Aenderungen bleiben Menschenentscheidung._

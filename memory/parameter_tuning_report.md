# Parameter-Tuning-Report

Status: **diagnostic**
n=88 | Diagnose ab n>=20 | Uebernahme erst ab n>=50

## Aktuelle Config

- ELO_PER_GOAL: `240.0`
- DIXON_COLES_RHO: `-0.1`
- BASELINE_TOTAL_GOALS: `2.6`

## rho-Anker

- rho: `0.0` (backtest.py StatsBomb WM 2018/22, ok)

## Headline: Walk-forward ELO_PER_GOAL

| ELO_PER_GOAL | RPS | LogLoss | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|
| 180 | 0.1497 | 0.714 | 0.0068 | 44 |
| 200 | 0.1517 | 0.7244 | 0.0048 | 44 |
| 220 | 0.154 | 0.7356 | 0.0025 | 44 |
| 240 | 0.1565 | 0.7465 | 0.0 | 44 |
| 260 | 0.1591 | 0.7571 | -0.0026 | 44 |
| 280 | 0.1616 | 0.7669 | -0.0051 | 44 |
| 320 | 0.1663 | 0.7844 | -0.0098 | 44 |

## Diagnose: In-sample Score-Flaeche

| ELO_PER_GOAL | RPS | LogLoss | Brier | Hit | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|---:|---:|
| 180 | 0.1545 | 0.779 | 0.4504 | 0.6932 | 0.0045 | 88 |
| 200 | 0.1558 | 0.7856 | 0.4536 | 0.6932 | 0.0032 | 88 |
| 220 | 0.1574 | 0.7933 | 0.4576 | 0.6932 | 0.0016 | 88 |
| 240 | 0.159 | 0.7991 | 0.4608 | 0.6932 | 0.0 | 88 |
| 260 | 0.1607 | 0.8055 | 0.4643 | 0.7045 | -0.0017 | 88 |
| 280 | 0.1624 | 0.8122 | 0.468 | 0.7045 | -0.0034 | 88 |
| 320 | 0.166 | 0.8253 | 0.4756 | 0.7045 | -0.007 | 88 |

## Sanity: Live-rho-Grid (kein Treiber der Empfehlung)

| rho | RPS | LogLoss | Brier | Hit | n |
|---:|---:|---:|---:|---:|---:|
| 0.0 | 0.159 | 0.7991 | 0.4608 | 0.6932 | 88 |
| -0.05 | 0.1592 | 0.8006 | 0.4623 | 0.6932 | 88 |
| -0.1 | 0.1595 | 0.8027 | 0.464 | 0.6932 | 88 |
| -0.15 | 0.1599 | 0.8051 | 0.4661 | 0.6932 | 88 |
| -0.2 | 0.1603 | 0.8081 | 0.4685 | 0.6932 | 88 |

## Kandidat

- ELO_PER_GOAL: `180.0`
- rho: `0.0`
- Walk-forward RPS: `0.1497`
- Marge gegen aktuelle Config: `0.0068`
- stabil ueber Folds: `False`
- LogLoss-Guard OK: `True`
- Uebernahme-reif: `False`

## Input-Audit

- snapshots: `148`
- resolved: `89`
- entries: `505`
- missing_model_inputs: `126`
- missing_baseline_total_goals: `41`
- cases: `88`

_Keine automatische Aenderung an config.py. Parameter-Aenderungen bleiben Menschenentscheidung._

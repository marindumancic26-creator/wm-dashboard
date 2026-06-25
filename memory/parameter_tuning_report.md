# Parameter-Tuning-Report

Status: **diagnostic**
n=46 | Diagnose ab n>=20 | Uebernahme erst ab n>=50

## Aktuelle Config

- ELO_PER_GOAL: `240.0`
- DIXON_COLES_RHO: `-0.1`
- BASELINE_TOTAL_GOALS: `2.6`

## rho-Anker

- rho: `0.0` (backtest.py StatsBomb WM 2018/22, ok)

## Headline: Walk-forward ELO_PER_GOAL

| ELO_PER_GOAL | RPS | LogLoss | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|
| 180 | 0.1502 | 0.7507 | 0.0068 | 23 |
| 200 | 0.1525 | 0.7588 | 0.0044 | 23 |
| 220 | 0.155 | 0.7676 | 0.0019 | 23 |
| 240 | 0.157 | 0.7718 | 0.0 | 23 |
| 260 | 0.1588 | 0.7762 | -0.0018 | 23 |
| 280 | 0.1606 | 0.7815 | -0.0036 | 23 |
| 320 | 0.1643 | 0.7934 | -0.0074 | 23 |

## Diagnose: In-sample Score-Flaeche

| ELO_PER_GOAL | RPS | LogLoss | Brier | Hit | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|---:|---:|
| 180 | 0.1665 | 0.8602 | 0.5109 | 0.6739 | 0.0004 | 46 |
| 200 | 0.1664 | 0.86 | 0.5103 | 0.6739 | 0.0005 | 46 |
| 220 | 0.1667 | 0.8619 | 0.5107 | 0.6739 | 0.0002 | 46 |
| 240 | 0.1669 | 0.8611 | 0.5099 | 0.6739 | 0.0 | 46 |
| 260 | 0.1673 | 0.862 | 0.5098 | 0.6739 | -0.0004 | 46 |
| 280 | 0.168 | 0.8643 | 0.5105 | 0.6739 | -0.0011 | 46 |
| 320 | 0.1699 | 0.8711 | 0.5133 | 0.6739 | -0.003 | 46 |

## Sanity: Live-rho-Grid (kein Treiber der Empfehlung)

| rho | RPS | LogLoss | Brier | Hit | n |
|---:|---:|---:|---:|---:|---:|
| 0.0 | 0.1669 | 0.8611 | 0.5099 | 0.6739 | 46 |
| -0.05 | 0.1669 | 0.8603 | 0.5104 | 0.6739 | 46 |
| -0.1 | 0.1671 | 0.86 | 0.5112 | 0.6739 | 46 |
| -0.15 | 0.1673 | 0.8603 | 0.5122 | 0.6739 | 46 |
| -0.2 | 0.1675 | 0.8611 | 0.5136 | 0.6739 | 46 |

## Kandidat

- ELO_PER_GOAL: `180.0`
- rho: `0.0`
- Walk-forward RPS: `0.1502`
- Marge gegen aktuelle Config: `0.0068`
- stabil ueber Folds: `False`
- LogLoss-Guard OK: `True`
- Uebernahme-reif: `False`

## Input-Audit

- snapshots: `64`
- resolved: `47`
- entries: `331`
- missing_model_inputs: `126`
- missing_baseline_total_goals: `39`
- cases: `46`

_Keine automatische Aenderung an config.py. Parameter-Aenderungen bleiben Menschenentscheidung._

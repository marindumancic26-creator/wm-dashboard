# Parameter-Tuning-Report

Status: **diagnostic**
n=83 | Diagnose ab n>=20 | Uebernahme erst ab n>=50

## Aktuelle Config

- ELO_PER_GOAL: `240.0`
- DIXON_COLES_RHO: `-0.1`
- BASELINE_TOTAL_GOALS: `2.6`

## rho-Anker

- rho: `0.0` (backtest.py StatsBomb WM 2018/22, ok)

## Headline: Walk-forward ELO_PER_GOAL

| ELO_PER_GOAL | RPS | LogLoss | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|
| 180 | 0.1452 | 0.7021 | 0.007 | 42 |
| 200 | 0.1473 | 0.7131 | 0.005 | 42 |
| 220 | 0.1497 | 0.7251 | 0.0026 | 42 |
| 240 | 0.1522 | 0.7367 | 0.0 | 42 |
| 260 | 0.1549 | 0.748 | -0.0026 | 42 |
| 280 | 0.1575 | 0.7585 | -0.0053 | 42 |
| 320 | 0.1625 | 0.7773 | -0.0103 | 42 |

## Diagnose: In-sample Score-Flaeche

| ELO_PER_GOAL | RPS | LogLoss | Brier | Hit | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|---:|---:|
| 180 | 0.157 | 0.7935 | 0.4614 | 0.6867 | 0.0037 | 83 |
| 200 | 0.158 | 0.7991 | 0.4639 | 0.6867 | 0.0027 | 83 |
| 220 | 0.1594 | 0.806 | 0.4672 | 0.6867 | 0.0013 | 83 |
| 240 | 0.1607 | 0.8111 | 0.4699 | 0.6867 | 0.0 | 83 |
| 260 | 0.1622 | 0.8169 | 0.473 | 0.6988 | -0.0015 | 83 |
| 280 | 0.1638 | 0.823 | 0.4763 | 0.6988 | -0.0031 | 83 |
| 320 | 0.1671 | 0.8354 | 0.4833 | 0.6988 | -0.0064 | 83 |

## Sanity: Live-rho-Grid (kein Treiber der Empfehlung)

| rho | RPS | LogLoss | Brier | Hit | n |
|---:|---:|---:|---:|---:|---:|
| 0.0 | 0.1607 | 0.8111 | 0.4699 | 0.6867 | 83 |
| -0.05 | 0.1609 | 0.8121 | 0.4711 | 0.6867 | 83 |
| -0.1 | 0.1611 | 0.8136 | 0.4725 | 0.6867 | 83 |
| -0.15 | 0.1614 | 0.8156 | 0.4743 | 0.6867 | 83 |
| -0.2 | 0.1617 | 0.8181 | 0.4763 | 0.6867 | 83 |

## Kandidat

- ELO_PER_GOAL: `180.0`
- rho: `0.0`
- Walk-forward RPS: `0.1452`
- Marge gegen aktuelle Config: `0.007`
- stabil ueber Folds: `False`
- LogLoss-Guard OK: `True`
- Uebernahme-reif: `False`

## Input-Audit

- snapshots: `96`
- resolved: `84`
- entries: `480`
- missing_model_inputs: `126`
- missing_baseline_total_goals: `40`
- cases: `83`

_Keine automatische Aenderung an config.py. Parameter-Aenderungen bleiben Menschenentscheidung._

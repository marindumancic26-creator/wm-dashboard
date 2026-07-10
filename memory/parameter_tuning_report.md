# Parameter-Tuning-Report

Status: **diagnostic**
n=85 | Diagnose ab n>=20 | Uebernahme erst ab n>=50

## Aktuelle Config

- ELO_PER_GOAL: `240.0`
- DIXON_COLES_RHO: `-0.1`
- BASELINE_TOTAL_GOALS: `2.6`

## rho-Anker

- rho: `0.0` (backtest.py StatsBomb WM 2018/22, ok)

## Headline: Walk-forward ELO_PER_GOAL

| ELO_PER_GOAL | RPS | LogLoss | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|
| 180 | 0.1499 | 0.7141 | 0.0063 | 43 |
| 200 | 0.1516 | 0.7243 | 0.0045 | 43 |
| 220 | 0.1538 | 0.7354 | 0.0023 | 43 |
| 240 | 0.1562 | 0.7462 | 0.0 | 43 |
| 260 | 0.1586 | 0.7569 | -0.0025 | 43 |
| 280 | 0.1611 | 0.7668 | -0.0049 | 43 |
| 320 | 0.1658 | 0.7845 | -0.0096 | 43 |

## Diagnose: In-sample Score-Flaeche

| ELO_PER_GOAL | RPS | LogLoss | Brier | Hit | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|---:|---:|
| 180 | 0.1577 | 0.7925 | 0.4606 | 0.6824 | 0.0037 | 85 |
| 200 | 0.1587 | 0.7982 | 0.4631 | 0.6824 | 0.0027 | 85 |
| 220 | 0.1601 | 0.8051 | 0.4665 | 0.6824 | 0.0013 | 85 |
| 240 | 0.1614 | 0.8102 | 0.4692 | 0.6824 | 0.0 | 85 |
| 260 | 0.1629 | 0.816 | 0.4722 | 0.6941 | -0.0015 | 85 |
| 280 | 0.1645 | 0.8221 | 0.4755 | 0.6941 | -0.0031 | 85 |
| 320 | 0.1678 | 0.8345 | 0.4826 | 0.6941 | -0.0064 | 85 |

## Sanity: Live-rho-Grid (kein Treiber der Empfehlung)

| rho | RPS | LogLoss | Brier | Hit | n |
|---:|---:|---:|---:|---:|---:|
| 0.0 | 0.1614 | 0.8102 | 0.4692 | 0.6824 | 85 |
| -0.05 | 0.1616 | 0.8115 | 0.4705 | 0.6824 | 85 |
| -0.1 | 0.1619 | 0.8133 | 0.4721 | 0.6824 | 85 |
| -0.15 | 0.1622 | 0.8155 | 0.474 | 0.6824 | 85 |
| -0.2 | 0.1626 | 0.8183 | 0.4762 | 0.6824 | 85 |

## Kandidat

- ELO_PER_GOAL: `180.0`
- rho: `0.0`
- Walk-forward RPS: `0.1499`
- Marge gegen aktuelle Config: `0.0063`
- stabil ueber Folds: `False`
- LogLoss-Guard OK: `True`
- Uebernahme-reif: `False`

## Input-Audit

- snapshots: `106`
- resolved: `86`
- entries: `492`
- missing_model_inputs: `126`
- missing_baseline_total_goals: `41`
- cases: `85`

_Keine automatische Aenderung an config.py. Parameter-Aenderungen bleiben Menschenentscheidung._

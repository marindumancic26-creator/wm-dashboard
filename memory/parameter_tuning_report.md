# Parameter-Tuning-Report

Status: **diagnostic**
n=69 | Diagnose ab n>=20 | Uebernahme erst ab n>=50

## Aktuelle Config

- ELO_PER_GOAL: `240.0`
- DIXON_COLES_RHO: `-0.1`
- BASELINE_TOTAL_GOALS: `2.6`

## rho-Anker

- rho: `0.0` (backtest.py StatsBomb WM 2018/22, ok)

## Headline: Walk-forward ELO_PER_GOAL

| ELO_PER_GOAL | RPS | LogLoss | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|
| 180 | 0.147 | 0.7568 | 0.0066 | 35 |
| 200 | 0.1491 | 0.7677 | 0.0045 | 35 |
| 220 | 0.1515 | 0.7786 | 0.0021 | 35 |
| 240 | 0.1536 | 0.7862 | 0.0 | 35 |
| 260 | 0.1557 | 0.7933 | -0.0021 | 35 |
| 280 | 0.1577 | 0.8005 | -0.0041 | 35 |
| 320 | 0.1618 | 0.8147 | -0.0082 | 35 |

## Diagnose: In-sample Score-Flaeche

| ELO_PER_GOAL | RPS | LogLoss | Brier | Hit | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|---:|---:|
| 180 | 0.1595 | 0.8294 | 0.4877 | 0.6522 | 0.0019 | 69 |
| 200 | 0.1598 | 0.8328 | 0.4887 | 0.6522 | 0.0016 | 69 |
| 220 | 0.1607 | 0.8376 | 0.4907 | 0.6522 | 0.0007 | 69 |
| 240 | 0.1614 | 0.8405 | 0.4919 | 0.6522 | 0.0 | 69 |
| 260 | 0.1625 | 0.8446 | 0.4938 | 0.6522 | -0.0011 | 69 |
| 280 | 0.1637 | 0.8494 | 0.4961 | 0.6522 | -0.0023 | 69 |
| 320 | 0.1664 | 0.8598 | 0.5014 | 0.6522 | -0.005 | 69 |

## Sanity: Live-rho-Grid (kein Treiber der Empfehlung)

| rho | RPS | LogLoss | Brier | Hit | n |
|---:|---:|---:|---:|---:|---:|
| 0.0 | 0.1614 | 0.8405 | 0.4919 | 0.6522 | 69 |
| -0.05 | 0.1614 | 0.8395 | 0.4919 | 0.6522 | 69 |
| -0.1 | 0.1615 | 0.839 | 0.4922 | 0.6522 | 69 |
| -0.15 | 0.1616 | 0.8391 | 0.4928 | 0.6522 | 69 |
| -0.2 | 0.1617 | 0.8398 | 0.4937 | 0.6522 | 69 |

## Kandidat

- ELO_PER_GOAL: `180.0`
- rho: `0.0`
- Walk-forward RPS: `0.147`
- Marge gegen aktuelle Config: `0.0066`
- stabil ueber Folds: `False`
- LogLoss-Guard OK: `True`
- Uebernahme-reif: `False`

## Input-Audit

- snapshots: `75`
- resolved: `70`
- entries: `391`
- missing_model_inputs: `126`
- missing_baseline_total_goals: `39`
- cases: `69`

_Keine automatische Aenderung an config.py. Parameter-Aenderungen bleiben Menschenentscheidung._

# Parameter-Tuning-Report

Status: **diagnostic**
n=31 | Diagnose ab n>=20 | Uebernahme erst ab n>=50

## Aktuelle Config

- ELO_PER_GOAL: `240.0`
- DIXON_COLES_RHO: `-0.1`
- BASELINE_TOTAL_GOALS: `2.6`

## rho-Anker

- rho: `0.0` (backtest.py StatsBomb WM 2018/22, ok)

## Headline: Walk-forward ELO_PER_GOAL

| ELO_PER_GOAL | RPS | LogLoss | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|
| 180 | 0.1509 | 0.7234 | 0.0023 | 16 |
| 200 | 0.151 | 0.7246 | 0.0022 | 16 |
| 220 | 0.1519 | 0.7298 | 0.0014 | 16 |
| 240 | 0.1532 | 0.7363 | 0.0 | 16 |
| 260 | 0.155 | 0.7448 | -0.0018 | 16 |
| 280 | 0.1569 | 0.7533 | -0.0037 | 16 |
| 320 | 0.161 | 0.7699 | -0.0078 | 16 |

## Diagnose: In-sample Score-Flaeche

| ELO_PER_GOAL | RPS | LogLoss | Brier | Hit | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|---:|---:|
| 180 | 0.1784 | 0.9175 | 0.5583 | 0.6129 | -0.0043 | 31 |
| 200 | 0.1764 | 0.911 | 0.5528 | 0.6129 | -0.0023 | 31 |
| 220 | 0.1751 | 0.9077 | 0.549 | 0.6129 | -0.001 | 31 |
| 240 | 0.1741 | 0.9041 | 0.5452 | 0.6129 | 0.0 | 31 |
| 260 | 0.1736 | 0.9038 | 0.5432 | 0.6129 | 0.0005 | 31 |
| 280 | 0.1737 | 0.9051 | 0.5423 | 0.6129 | 0.0004 | 31 |
| 320 | 0.1745 | 0.9101 | 0.5427 | 0.6129 | -0.0004 | 31 |

## Sanity: Live-rho-Grid (kein Treiber der Empfehlung)

| rho | RPS | LogLoss | Brier | Hit | n |
|---:|---:|---:|---:|---:|---:|
| 0.0 | 0.1741 | 0.9041 | 0.5452 | 0.6129 | 31 |
| -0.05 | 0.1739 | 0.9012 | 0.5443 | 0.6129 | 31 |
| -0.1 | 0.1738 | 0.8989 | 0.5437 | 0.6129 | 31 |
| -0.15 | 0.1738 | 0.8973 | 0.5434 | 0.6129 | 31 |
| -0.2 | 0.1738 | 0.8962 | 0.5434 | 0.6129 | 31 |

## Kandidat

- ELO_PER_GOAL: `180.0`
- rho: `0.0`
- Walk-forward RPS: `0.1509`
- Marge gegen aktuelle Config: `0.0023`
- stabil ueber Folds: `False`
- LogLoss-Guard OK: `True`
- Uebernahme-reif: `False`

## Input-Audit

- snapshots: `59`
- resolved: `32`
- entries: `260`
- missing_model_inputs: `126`
- missing_baseline_total_goals: `40`
- cases: `31`

_Keine automatische Aenderung an config.py. Parameter-Aenderungen bleiben Menschenentscheidung._

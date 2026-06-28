# Parameter-Tuning-Report

Status: **diagnostic**
n=63 | Diagnose ab n>=20 | Uebernahme erst ab n>=50

## Aktuelle Config

- ELO_PER_GOAL: `240.0`
- DIXON_COLES_RHO: `-0.1`
- BASELINE_TOTAL_GOALS: `2.6`

## rho-Anker

- rho: `0.0` (backtest.py StatsBomb WM 2018/22, ok)

## Headline: Walk-forward ELO_PER_GOAL

| ELO_PER_GOAL | RPS | LogLoss | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|
| 180 | 0.1248 | 0.7008 | 0.0088 | 32 |
| 200 | 0.1277 | 0.7144 | 0.0058 | 32 |
| 220 | 0.1309 | 0.7276 | 0.0027 | 32 |
| 240 | 0.1335 | 0.7369 | 0.0 | 32 |
| 260 | 0.1362 | 0.746 | -0.0026 | 32 |
| 280 | 0.1387 | 0.7551 | -0.0052 | 32 |
| 320 | 0.1437 | 0.7728 | -0.0102 | 32 |

## Diagnose: In-sample Score-Flaeche

| ELO_PER_GOAL | RPS | LogLoss | Brier | Hit | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|---:|---:|
| 180 | 0.154 | 0.8295 | 0.4887 | 0.6508 | 0.0021 | 63 |
| 200 | 0.1544 | 0.8329 | 0.4897 | 0.6508 | 0.0017 | 63 |
| 220 | 0.1553 | 0.8377 | 0.4916 | 0.6508 | 0.0008 | 63 |
| 240 | 0.1561 | 0.8405 | 0.4927 | 0.6508 | 0.0 | 63 |
| 260 | 0.1571 | 0.8445 | 0.4944 | 0.6508 | -0.001 | 63 |
| 280 | 0.1584 | 0.8493 | 0.4966 | 0.6508 | -0.0023 | 63 |
| 320 | 0.1611 | 0.8599 | 0.5019 | 0.6508 | -0.005 | 63 |

## Sanity: Live-rho-Grid (kein Treiber der Empfehlung)

| rho | RPS | LogLoss | Brier | Hit | n |
|---:|---:|---:|---:|---:|---:|
| 0.0 | 0.1561 | 0.8405 | 0.4927 | 0.6508 | 63 |
| -0.05 | 0.156 | 0.838 | 0.492 | 0.6508 | 63 |
| -0.1 | 0.1559 | 0.8362 | 0.4916 | 0.6508 | 63 |
| -0.15 | 0.1559 | 0.8349 | 0.4915 | 0.6508 | 63 |
| -0.2 | 0.1559 | 0.8342 | 0.4917 | 0.6508 | 63 |

## Kandidat

- ELO_PER_GOAL: `180.0`
- rho: `0.0`
- Walk-forward RPS: `0.1248`
- Marge gegen aktuelle Config: `0.0088`
- stabil ueber Folds: `True`
- LogLoss-Guard OK: `True`
- Uebernahme-reif: `False`

## Input-Audit

- snapshots: `72`
- resolved: `64`
- entries: `379`
- missing_model_inputs: `126`
- missing_baseline_total_goals: `40`
- cases: `63`

_Keine automatische Aenderung an config.py. Parameter-Aenderungen bleiben Menschenentscheidung._

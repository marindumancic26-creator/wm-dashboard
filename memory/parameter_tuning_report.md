# Parameter-Tuning-Report

Status: **diagnostic**
n=90 | Diagnose ab n>=20 | Uebernahme erst ab n>=50

## Aktuelle Config

- ELO_PER_GOAL: `240.0`
- DIXON_COLES_RHO: `-0.1`
- BASELINE_TOTAL_GOALS: `2.6`

## rho-Anker

- rho: `0.0` (backtest.py StatsBomb WM 2018/22, ok)

## Headline: Walk-forward ELO_PER_GOAL

| ELO_PER_GOAL | RPS | LogLoss | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|
| 180 | 0.1412 | 0.6848 | 0.0095 | 45 |
| 200 | 0.1443 | 0.6994 | 0.0065 | 45 |
| 220 | 0.1475 | 0.7137 | 0.0032 | 45 |
| 240 | 0.1507 | 0.727 | 0.0 | 45 |
| 260 | 0.1539 | 0.7395 | -0.0031 | 45 |
| 280 | 0.1569 | 0.751 | -0.0062 | 45 |
| 320 | 0.1624 | 0.7709 | -0.0117 | 45 |

## Diagnose: In-sample Score-Flaeche

| ELO_PER_GOAL | RPS | LogLoss | Brier | Hit | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|---:|---:|
| 180 | 0.1554 | 0.7791 | 0.4503 | 0.7 | 0.0047 | 90 |
| 200 | 0.1568 | 0.7859 | 0.4537 | 0.7 | 0.0033 | 90 |
| 220 | 0.1585 | 0.7938 | 0.4578 | 0.7 | 0.0016 | 90 |
| 240 | 0.1601 | 0.7997 | 0.4611 | 0.7 | 0.0 | 90 |
| 260 | 0.1618 | 0.8062 | 0.4648 | 0.7111 | -0.0017 | 90 |
| 280 | 0.1636 | 0.8129 | 0.4685 | 0.7111 | -0.0035 | 90 |
| 320 | 0.1673 | 0.826 | 0.4762 | 0.7111 | -0.0072 | 90 |

## Sanity: Live-rho-Grid (kein Treiber der Empfehlung)

| rho | RPS | LogLoss | Brier | Hit | n |
|---:|---:|---:|---:|---:|---:|
| 0.0 | 0.1601 | 0.7997 | 0.4611 | 0.7 | 90 |
| -0.05 | 0.1604 | 0.8015 | 0.4628 | 0.7 | 90 |
| -0.1 | 0.1607 | 0.8038 | 0.4647 | 0.7 | 90 |
| -0.15 | 0.1611 | 0.8065 | 0.4669 | 0.7 | 90 |
| -0.2 | 0.1615 | 0.8096 | 0.4695 | 0.7 | 90 |

## Kandidat

- ELO_PER_GOAL: `180.0`
- rho: `0.0`
- Walk-forward RPS: `0.1412`
- Marge gegen aktuelle Config: `0.0095`
- stabil ueber Folds: `True`
- LogLoss-Guard OK: `True`
- Uebernahme-reif: `False`

## Input-Audit

- snapshots: `158`
- resolved: `91`
- entries: `519`
- missing_model_inputs: `126`
- missing_baseline_total_goals: `41`
- cases: `90`

_Keine automatische Aenderung an config.py. Parameter-Aenderungen bleiben Menschenentscheidung._

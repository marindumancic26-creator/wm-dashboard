# Parameter-Tuning-Report

Status: **diagnostic**
n=66 | Diagnose ab n>=20 | Uebernahme erst ab n>=50

## Aktuelle Config

- ELO_PER_GOAL: `240.0`
- DIXON_COLES_RHO: `-0.1`
- BASELINE_TOTAL_GOALS: `2.6`

## rho-Anker

- rho: `0.0` (backtest.py StatsBomb WM 2018/22, ok)

## Headline: Walk-forward ELO_PER_GOAL

| ELO_PER_GOAL | RPS | LogLoss | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|
| 180 | 0.1482 | 0.7679 | 0.0056 | 33 |
| 200 | 0.1499 | 0.7777 | 0.0039 | 33 |
| 220 | 0.152 | 0.7876 | 0.0018 | 33 |
| 240 | 0.1538 | 0.7942 | 0.0 | 33 |
| 260 | 0.1556 | 0.8004 | -0.0018 | 33 |
| 280 | 0.1574 | 0.807 | -0.0036 | 33 |
| 320 | 0.1611 | 0.8201 | -0.0073 | 33 |

## Diagnose: In-sample Score-Flaeche

| ELO_PER_GOAL | RPS | LogLoss | Brier | Hit | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|---:|---:|
| 180 | 0.1625 | 0.8463 | 0.4996 | 0.6364 | 0.001 | 66 |
| 200 | 0.1625 | 0.8483 | 0.4998 | 0.6364 | 0.001 | 66 |
| 220 | 0.163 | 0.852 | 0.501 | 0.6364 | 0.0005 | 66 |
| 240 | 0.1635 | 0.8538 | 0.5016 | 0.6364 | 0.0 | 66 |
| 260 | 0.1643 | 0.857 | 0.5028 | 0.6364 | -0.0008 | 66 |
| 280 | 0.1653 | 0.8611 | 0.5046 | 0.6364 | -0.0018 | 66 |
| 320 | 0.1676 | 0.8703 | 0.5091 | 0.6364 | -0.0041 | 66 |

## Sanity: Live-rho-Grid (kein Treiber der Empfehlung)

| rho | RPS | LogLoss | Brier | Hit | n |
|---:|---:|---:|---:|---:|---:|
| 0.0 | 0.1635 | 0.8538 | 0.5016 | 0.6364 | 66 |
| -0.05 | 0.1635 | 0.8523 | 0.5013 | 0.6364 | 66 |
| -0.1 | 0.1635 | 0.8514 | 0.5012 | 0.6364 | 66 |
| -0.15 | 0.1635 | 0.8511 | 0.5015 | 0.6364 | 66 |
| -0.2 | 0.1636 | 0.8513 | 0.5021 | 0.6364 | 66 |

## Kandidat

- ELO_PER_GOAL: `180.0`
- rho: `0.0`
- Walk-forward RPS: `0.1482`
- Marge gegen aktuelle Config: `0.0056`
- stabil ueber Folds: `False`
- LogLoss-Guard OK: `True`
- Uebernahme-reif: `False`

## Input-Audit

- snapshots: `72`
- resolved: `67`
- entries: `388`
- missing_model_inputs: `126`
- missing_baseline_total_goals: `39`
- cases: `66`

_Keine automatische Aenderung an config.py. Parameter-Aenderungen bleiben Menschenentscheidung._

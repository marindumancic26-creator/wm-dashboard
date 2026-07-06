# Parameter-Tuning-Report

Status: **diagnostic**
n=80 | Diagnose ab n>=20 | Uebernahme erst ab n>=50

## Aktuelle Config

- ELO_PER_GOAL: `240.0`
- DIXON_COLES_RHO: `-0.1`
- BASELINE_TOTAL_GOALS: `2.6`

## rho-Anker

- rho: `0.0` (backtest.py StatsBomb WM 2018/22, ok)

## Headline: Walk-forward ELO_PER_GOAL

| ELO_PER_GOAL | RPS | LogLoss | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|
| 180 | 0.147 | 0.7128 | 0.0068 | 40 |
| 200 | 0.1489 | 0.7236 | 0.0049 | 40 |
| 220 | 0.1513 | 0.7351 | 0.0025 | 40 |
| 240 | 0.1538 | 0.7464 | 0.0 | 40 |
| 260 | 0.1564 | 0.7574 | -0.0026 | 40 |
| 280 | 0.159 | 0.7677 | -0.0052 | 40 |
| 320 | 0.164 | 0.7861 | -0.0102 | 40 |

## Diagnose: In-sample Score-Flaeche

| ELO_PER_GOAL | RPS | LogLoss | Brier | Hit | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|---:|---:|
| 180 | 0.1594 | 0.8064 | 0.4703 | 0.675 | 0.0031 | 80 |
| 200 | 0.1602 | 0.8112 | 0.4723 | 0.675 | 0.0023 | 80 |
| 220 | 0.1614 | 0.8174 | 0.4753 | 0.675 | 0.0011 | 80 |
| 240 | 0.1625 | 0.8218 | 0.4775 | 0.675 | 0.0 | 80 |
| 260 | 0.1639 | 0.827 | 0.4802 | 0.6875 | -0.0014 | 80 |
| 280 | 0.1653 | 0.8327 | 0.4832 | 0.6875 | -0.0028 | 80 |
| 320 | 0.1685 | 0.8444 | 0.4897 | 0.6875 | -0.006 | 80 |

## Sanity: Live-rho-Grid (kein Treiber der Empfehlung)

| rho | RPS | LogLoss | Brier | Hit | n |
|---:|---:|---:|---:|---:|---:|
| 0.0 | 0.1625 | 0.8218 | 0.4775 | 0.675 | 80 |
| -0.05 | 0.1627 | 0.8225 | 0.4785 | 0.675 | 80 |
| -0.1 | 0.1629 | 0.8237 | 0.4797 | 0.675 | 80 |
| -0.15 | 0.1631 | 0.8255 | 0.4813 | 0.675 | 80 |
| -0.2 | 0.1635 | 0.8277 | 0.4831 | 0.675 | 80 |

## Kandidat

- ELO_PER_GOAL: `180.0`
- rho: `0.0`
- Walk-forward RPS: `0.147`
- Marge gegen aktuelle Config: `0.0068`
- stabil ueber Folds: `False`
- LogLoss-Guard OK: `True`
- Uebernahme-reif: `False`

## Input-Audit

- snapshots: `92`
- resolved: `81`
- entries: `463`
- missing_model_inputs: `126`
- missing_baseline_total_goals: `41`
- cases: `80`

_Keine automatische Aenderung an config.py. Parameter-Aenderungen bleiben Menschenentscheidung._

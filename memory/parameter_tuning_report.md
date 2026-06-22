# Parameter-Tuning-Report

Status: **diagnostic**
n=33 | Diagnose ab n>=20 | Uebernahme erst ab n>=50

## Aktuelle Config

- ELO_PER_GOAL: `240.0`
- DIXON_COLES_RHO: `-0.1`
- BASELINE_TOTAL_GOALS: `2.6`

## rho-Anker

- rho: `0.0` (backtest.py StatsBomb WM 2018/22, ok)

## Headline: Walk-forward ELO_PER_GOAL

| ELO_PER_GOAL | RPS | LogLoss | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|
| 180 | 0.1546 | 0.7739 | 0.0015 | 17 |
| 200 | 0.1543 | 0.7741 | 0.0018 | 17 |
| 220 | 0.155 | 0.7785 | 0.0011 | 17 |
| 240 | 0.1561 | 0.7842 | 0.0 | 17 |
| 260 | 0.1576 | 0.7918 | -0.0015 | 17 |
| 280 | 0.1593 | 0.7997 | -0.0032 | 17 |
| 320 | 0.163 | 0.8149 | -0.0069 | 17 |

## Diagnose: In-sample Score-Flaeche

| ELO_PER_GOAL | RPS | LogLoss | Brier | Hit | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|---:|---:|
| 180 | 0.1769 | 0.9247 | 0.5629 | 0.6061 | -0.0037 | 33 |
| 200 | 0.1751 | 0.919 | 0.5579 | 0.6061 | -0.0019 | 33 |
| 220 | 0.1741 | 0.9163 | 0.5545 | 0.6061 | -0.0009 | 33 |
| 240 | 0.1732 | 0.9134 | 0.5511 | 0.6061 | 0.0 | 33 |
| 260 | 0.173 | 0.9136 | 0.5493 | 0.6061 | 0.0002 | 33 |
| 280 | 0.1731 | 0.9152 | 0.5487 | 0.6061 | 0.0001 | 33 |
| 320 | 0.1741 | 0.9204 | 0.5494 | 0.6061 | -0.0009 | 33 |

## Sanity: Live-rho-Grid (kein Treiber der Empfehlung)

| rho | RPS | LogLoss | Brier | Hit | n |
|---:|---:|---:|---:|---:|---:|
| 0.0 | 0.1732 | 0.9134 | 0.5511 | 0.6061 | 33 |
| -0.05 | 0.173 | 0.9096 | 0.5497 | 0.6061 | 33 |
| -0.1 | 0.1728 | 0.9065 | 0.5487 | 0.6061 | 33 |
| -0.15 | 0.1727 | 0.9041 | 0.5479 | 0.6061 | 33 |
| -0.2 | 0.1726 | 0.9022 | 0.5475 | 0.6061 | 33 |

## Kandidat

- ELO_PER_GOAL: `200.0`
- rho: `0.0`
- Walk-forward RPS: `0.1543`
- Marge gegen aktuelle Config: `0.0018`
- stabil ueber Folds: `False`
- LogLoss-Guard OK: `True`
- Uebernahme-reif: `False`

## Input-Audit

- snapshots: `60`
- resolved: `34`
- entries: `278`
- missing_model_inputs: `126`
- missing_baseline_total_goals: `39`
- cases: `33`

_Keine automatische Aenderung an config.py. Parameter-Aenderungen bleiben Menschenentscheidung._

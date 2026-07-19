# Parameter-Tuning-Report

Status: **diagnostic**
n=91 | Diagnose ab n>=20 | Uebernahme erst ab n>=50

## Aktuelle Config

- ELO_PER_GOAL: `240.0`
- DIXON_COLES_RHO: `-0.1`
- BASELINE_TOTAL_GOALS: `2.6`

## rho-Anker

- rho: `0.0` (backtest.py StatsBomb WM 2018/22, ok)

## Headline: Walk-forward ELO_PER_GOAL

| ELO_PER_GOAL | RPS | LogLoss | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|
| 180 | 0.145 | 0.6943 | 0.0089 | 46 |
| 200 | 0.1479 | 0.7081 | 0.0061 | 46 |
| 220 | 0.1509 | 0.7218 | 0.003 | 46 |
| 240 | 0.1539 | 0.7345 | 0.0 | 46 |
| 260 | 0.157 | 0.7465 | -0.003 | 46 |
| 280 | 0.1598 | 0.7575 | -0.0059 | 46 |
| 320 | 0.1652 | 0.7768 | -0.0112 | 46 |

## Diagnose: In-sample Score-Flaeche

| ELO_PER_GOAL | RPS | LogLoss | Brier | Hit | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|---:|---:|
| 180 | 0.1572 | 0.7828 | 0.453 | 0.6923 | 0.0044 | 91 |
| 200 | 0.1585 | 0.7894 | 0.4562 | 0.6923 | 0.0031 | 91 |
| 220 | 0.1601 | 0.797 | 0.4601 | 0.6923 | 0.0015 | 91 |
| 240 | 0.1616 | 0.8027 | 0.4633 | 0.6923 | 0.0 | 91 |
| 260 | 0.1633 | 0.809 | 0.4668 | 0.7033 | -0.0017 | 91 |
| 280 | 0.165 | 0.8155 | 0.4705 | 0.7033 | -0.0034 | 91 |
| 320 | 0.1686 | 0.8284 | 0.478 | 0.7033 | -0.007 | 91 |

## Sanity: Live-rho-Grid (kein Treiber der Empfehlung)

| rho | RPS | LogLoss | Brier | Hit | n |
|---:|---:|---:|---:|---:|---:|
| 0.0 | 0.1616 | 0.8027 | 0.4633 | 0.6923 | 91 |
| -0.05 | 0.1619 | 0.8047 | 0.4651 | 0.6923 | 91 |
| -0.1 | 0.1622 | 0.8071 | 0.4671 | 0.6923 | 91 |
| -0.15 | 0.1626 | 0.81 | 0.4694 | 0.6923 | 91 |
| -0.2 | 0.1631 | 0.8133 | 0.472 | 0.6923 | 91 |

## Kandidat

- ELO_PER_GOAL: `180.0`
- rho: `0.0`
- Walk-forward RPS: `0.145`
- Marge gegen aktuelle Config: `0.0089`
- stabil ueber Folds: `True`
- LogLoss-Guard OK: `True`
- Uebernahme-reif: `False`

## Input-Audit

- snapshots: `164`
- resolved: `92`
- entries: `524`
- missing_model_inputs: `126`
- missing_baseline_total_goals: `41`
- cases: `91`

_Keine automatische Aenderung an config.py. Parameter-Aenderungen bleiben Menschenentscheidung._

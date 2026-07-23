# Parameter-Tuning-Report

Status: **diagnostic**
n=92 | Diagnose ab n>=20 | Uebernahme erst ab n>=50

## Aktuelle Config

- ELO_PER_GOAL: `240.0`
- DIXON_COLES_RHO: `-0.1`
- BASELINE_TOTAL_GOALS: `2.6`

## rho-Anker

- rho: `0.0` (backtest.py StatsBomb WM 2018/22, ok)

## Headline: Walk-forward ELO_PER_GOAL

| ELO_PER_GOAL | RPS | LogLoss | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|
| 180 | 0.1495 | 0.708 | 0.0088 | 46 |
| 200 | 0.1524 | 0.7214 | 0.0059 | 46 |
| 220 | 0.1554 | 0.7346 | 0.003 | 46 |
| 240 | 0.1583 | 0.747 | 0.0 | 46 |
| 260 | 0.1613 | 0.7588 | -0.0029 | 46 |
| 280 | 0.1641 | 0.7694 | -0.0058 | 46 |
| 320 | 0.1693 | 0.7882 | -0.011 | 46 |

## Diagnose: In-sample Score-Flaeche

| ELO_PER_GOAL | RPS | LogLoss | Brier | Hit | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|---:|---:|
| 180 | 0.1581 | 0.7841 | 0.4539 | 0.6957 | 0.0045 | 92 |
| 200 | 0.1594 | 0.7907 | 0.4572 | 0.6957 | 0.0032 | 92 |
| 220 | 0.161 | 0.7983 | 0.4611 | 0.6957 | 0.0016 | 92 |
| 240 | 0.1626 | 0.8041 | 0.4644 | 0.6957 | 0.0 | 92 |
| 260 | 0.1643 | 0.8104 | 0.4679 | 0.7065 | -0.0017 | 92 |
| 280 | 0.166 | 0.8169 | 0.4715 | 0.7065 | -0.0034 | 92 |
| 320 | 0.1696 | 0.8297 | 0.479 | 0.7065 | -0.007 | 92 |

## Sanity: Live-rho-Grid (kein Treiber der Empfehlung)

| rho | RPS | LogLoss | Brier | Hit | n |
|---:|---:|---:|---:|---:|---:|
| 0.0 | 0.1626 | 0.8041 | 0.4644 | 0.6957 | 92 |
| -0.05 | 0.1629 | 0.8061 | 0.4661 | 0.6957 | 92 |
| -0.1 | 0.1632 | 0.8087 | 0.4682 | 0.6957 | 92 |
| -0.15 | 0.1636 | 0.8117 | 0.4706 | 0.6957 | 92 |
| -0.2 | 0.1641 | 0.8151 | 0.4733 | 0.6957 | 92 |

## Kandidat

- ELO_PER_GOAL: `180.0`
- rho: `0.0`
- Walk-forward RPS: `0.1495`
- Marge gegen aktuelle Config: `0.0088`
- stabil ueber Folds: `True`
- LogLoss-Guard OK: `True`
- Uebernahme-reif: `False`

## Input-Audit

- snapshots: `181`
- resolved: `93`
- entries: `530`
- missing_model_inputs: `126`
- missing_baseline_total_goals: `41`
- cases: `92`

_Keine automatische Aenderung an config.py. Parameter-Aenderungen bleiben Menschenentscheidung._

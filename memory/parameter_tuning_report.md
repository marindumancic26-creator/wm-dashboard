# Parameter-Tuning-Report

Status: **diagnostic**
n=27 | Diagnose ab n>=20 | Uebernahme erst ab n>=50

## Aktuelle Config

- ELO_PER_GOAL: `240.0`
- DIXON_COLES_RHO: `-0.1`
- BASELINE_TOTAL_GOALS: `2.6`

## rho-Anker

- rho: `0.0` (backtest.py StatsBomb WM 2018/22, ok)

## Headline: Walk-forward ELO_PER_GOAL

| ELO_PER_GOAL | RPS | LogLoss | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|
| 180 | 0.1516 | 0.6954 | 0.0087 | 14 |
| 200 | 0.1541 | 0.7062 | 0.0062 | 14 |
| 220 | 0.1571 | 0.719 | 0.0032 | 14 |
| 240 | 0.1603 | 0.7316 | 0.0 | 14 |
| 260 | 0.1636 | 0.7437 | -0.0032 | 14 |
| 280 | 0.1668 | 0.7549 | -0.0064 | 14 |
| 320 | 0.1727 | 0.7752 | -0.0125 | 14 |

## Diagnose: In-sample Score-Flaeche

| ELO_PER_GOAL | RPS | LogLoss | Brier | Hit | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|---:|---:|
| 180 | 0.1903 | 0.9599 | 0.583 | 0.5926 | -0.0041 | 27 |
| 200 | 0.1885 | 0.9539 | 0.5785 | 0.5926 | -0.0023 | 27 |
| 220 | 0.1873 | 0.9508 | 0.5753 | 0.5926 | -0.0011 | 27 |
| 240 | 0.1862 | 0.9467 | 0.5716 | 0.5926 | 0.0 | 27 |
| 260 | 0.1857 | 0.9454 | 0.5695 | 0.5926 | 0.0005 | 27 |
| 280 | 0.1856 | 0.9456 | 0.5685 | 0.5926 | 0.0006 | 27 |
| 320 | 0.1861 | 0.9486 | 0.5684 | 0.5926 | 0.0001 | 27 |

## Sanity: Live-rho-Grid (kein Treiber der Empfehlung)

| rho | RPS | LogLoss | Brier | Hit | n |
|---:|---:|---:|---:|---:|---:|
| 0.0 | 0.1862 | 0.9467 | 0.5716 | 0.5926 | 27 |
| -0.05 | 0.1861 | 0.9446 | 0.571 | 0.5926 | 27 |
| -0.1 | 0.186 | 0.943 | 0.5707 | 0.5926 | 27 |
| -0.15 | 0.186 | 0.9422 | 0.5707 | 0.5926 | 27 |
| -0.2 | 0.1861 | 0.9419 | 0.571 | 0.5926 | 27 |

## Kandidat

- ELO_PER_GOAL: `180.0`
- rho: `0.0`
- Walk-forward RPS: `0.1516`
- Marge gegen aktuelle Config: `0.0087`
- stabil ueber Folds: `True`
- LogLoss-Guard OK: `True`
- Uebernahme-reif: `False`

## Input-Audit

- snapshots: `53`
- resolved: `28`
- entries: `240`
- missing_model_inputs: `126`
- missing_baseline_total_goals: `40`
- cases: `27`

_Keine automatische Aenderung an config.py. Parameter-Aenderungen bleiben Menschenentscheidung._

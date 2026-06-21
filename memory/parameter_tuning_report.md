# Parameter-Tuning-Report

Status: **diagnostic**
n=30 | Diagnose ab n>=20 | Uebernahme erst ab n>=50

## Aktuelle Config

- ELO_PER_GOAL: `240.0`
- DIXON_COLES_RHO: `-0.1`
- BASELINE_TOTAL_GOALS: `2.6`

## rho-Anker

- rho: `0.0` (backtest.py StatsBomb WM 2018/22, ok)

## Headline: Walk-forward ELO_PER_GOAL

| ELO_PER_GOAL | RPS | LogLoss | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|
| 180 | 0.1607 | 0.7659 | 0.0025 | 15 |
| 200 | 0.1608 | 0.7671 | 0.0024 | 15 |
| 220 | 0.1618 | 0.7727 | 0.0014 | 15 |
| 240 | 0.1632 | 0.7796 | 0.0 | 15 |
| 260 | 0.1649 | 0.7871 | -0.0017 | 15 |
| 280 | 0.1668 | 0.7946 | -0.0036 | 15 |
| 320 | 0.1707 | 0.8092 | -0.0075 | 15 |

## Diagnose: In-sample Score-Flaeche

| ELO_PER_GOAL | RPS | LogLoss | Brier | Hit | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|---:|---:|
| 180 | 0.1842 | 0.9452 | 0.5765 | 0.6 | -0.0045 | 30 |
| 200 | 0.1821 | 0.9385 | 0.5709 | 0.6 | -0.0024 | 30 |
| 220 | 0.1809 | 0.935 | 0.5669 | 0.6 | -0.0012 | 30 |
| 240 | 0.1797 | 0.9313 | 0.563 | 0.6 | 0.0 | 30 |
| 260 | 0.1792 | 0.9303 | 0.5607 | 0.6 | 0.0005 | 30 |
| 280 | 0.1792 | 0.9309 | 0.5595 | 0.6 | 0.0005 | 30 |
| 320 | 0.1798 | 0.9344 | 0.5593 | 0.6 | -0.0001 | 30 |

## Sanity: Live-rho-Grid (kein Treiber der Empfehlung)

| rho | RPS | LogLoss | Brier | Hit | n |
|---:|---:|---:|---:|---:|---:|
| 0.0 | 0.1797 | 0.9313 | 0.563 | 0.6 | 30 |
| -0.05 | 0.1796 | 0.9283 | 0.562 | 0.6 | 30 |
| -0.1 | 0.1795 | 0.9259 | 0.5614 | 0.6 | 30 |
| -0.15 | 0.1794 | 0.9241 | 0.561 | 0.6 | 30 |
| -0.2 | 0.1794 | 0.923 | 0.561 | 0.6 | 30 |

## Kandidat

- ELO_PER_GOAL: `180.0`
- rho: `0.0`
- Walk-forward RPS: `0.1607`
- Marge gegen aktuelle Config: `0.0025`
- stabil ueber Folds: `False`
- LogLoss-Guard OK: `True`
- Uebernahme-reif: `False`

## Input-Audit

- snapshots: `53`
- resolved: `31`
- entries: `253`
- missing_model_inputs: `126`
- missing_baseline_total_goals: `39`
- cases: `30`

_Keine automatische Aenderung an config.py. Parameter-Aenderungen bleiben Menschenentscheidung._

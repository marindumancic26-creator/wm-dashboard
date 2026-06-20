# Parameter-Tuning-Report

Status: **diagnostic**
n=26 | Diagnose ab n>=20 | Uebernahme erst ab n>=50

## Aktuelle Config

- ELO_PER_GOAL: `240.0`
- DIXON_COLES_RHO: `-0.1`
- BASELINE_TOTAL_GOALS: `2.6`

## rho-Anker

- rho: `0.0` (backtest.py StatsBomb WM 2018/22, ok)

## Headline: Walk-forward ELO_PER_GOAL

| ELO_PER_GOAL | RPS | LogLoss | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|
| 180 | 0.1555 | 0.7085 | 0.0062 | 13 |
| 200 | 0.157 | 0.7164 | 0.0047 | 13 |
| 220 | 0.1591 | 0.727 | 0.0025 | 13 |
| 240 | 0.1616 | 0.7379 | 0.0 | 13 |
| 260 | 0.1643 | 0.7485 | -0.0026 | 13 |
| 280 | 0.1669 | 0.7585 | -0.0053 | 13 |
| 320 | 0.1721 | 0.7767 | -0.0105 | 13 |

## Diagnose: In-sample Score-Flaeche

| ELO_PER_GOAL | RPS | LogLoss | Brier | Hit | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|---:|---:|
| 180 | 0.1937 | 0.9766 | 0.5958 | 0.5769 | -0.0059 | 26 |
| 200 | 0.1912 | 0.9686 | 0.5897 | 0.5769 | -0.0034 | 26 |
| 220 | 0.1895 | 0.9637 | 0.5853 | 0.5769 | -0.0017 | 26 |
| 240 | 0.1878 | 0.9582 | 0.5804 | 0.5769 | 0.0 | 26 |
| 260 | 0.1869 | 0.9556 | 0.5774 | 0.5769 | 0.0009 | 26 |
| 280 | 0.1864 | 0.9548 | 0.5755 | 0.5769 | 0.0014 | 26 |
| 320 | 0.1863 | 0.956 | 0.574 | 0.5769 | 0.0015 | 26 |

## Sanity: Live-rho-Grid (kein Treiber der Empfehlung)

| rho | RPS | LogLoss | Brier | Hit | n |
|---:|---:|---:|---:|---:|---:|
| 0.0 | 0.1878 | 0.9582 | 0.5804 | 0.5769 | 26 |
| -0.05 | 0.1877 | 0.9555 | 0.5795 | 0.5769 | 26 |
| -0.1 | 0.1876 | 0.9535 | 0.5788 | 0.5769 | 26 |
| -0.15 | 0.1875 | 0.9522 | 0.5785 | 0.5769 | 26 |
| -0.2 | 0.1875 | 0.9515 | 0.5784 | 0.5769 | 26 |

## Kandidat

- ELO_PER_GOAL: `180.0`
- rho: `0.0`
- Walk-forward RPS: `0.1555`
- Marge gegen aktuelle Config: `0.0062`
- stabil ueber Folds: `False`
- LogLoss-Guard OK: `True`
- Uebernahme-reif: `False`

## Input-Audit

- snapshots: `50`
- resolved: `27`
- entries: `236`
- missing_model_inputs: `126`
- missing_baseline_total_goals: `39`
- cases: `26`

_Keine automatische Aenderung an config.py. Parameter-Aenderungen bleiben Menschenentscheidung._

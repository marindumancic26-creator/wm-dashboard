# Parameter-Tuning-Report

Status: **diagnostic**
n=22 | Diagnose ab n>=20 | Uebernahme erst ab n>=50

## Aktuelle Config

- ELO_PER_GOAL: `240.0`
- DIXON_COLES_RHO: `-0.1`
- BASELINE_TOTAL_GOALS: `2.6`

## rho-Anker

- rho: `0.0` (backtest.py StatsBomb WM 2018/22, ok)

## Headline: Walk-forward ELO_PER_GOAL

| ELO_PER_GOAL | RPS | LogLoss | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|
| 180 | 0.1186 | 0.6114 | 0.0123 | 11 |
| 200 | 0.1224 | 0.6288 | 0.0085 | 11 |
| 220 | 0.1266 | 0.646 | 0.0043 | 11 |
| 240 | 0.1309 | 0.6625 | 0.0 | 11 |
| 260 | 0.1353 | 0.6783 | -0.0044 | 11 |
| 280 | 0.1395 | 0.6928 | -0.0086 | 11 |
| 320 | 0.1473 | 0.7186 | -0.0164 | 11 |

## Diagnose: In-sample Score-Flaeche

| ELO_PER_GOAL | RPS | LogLoss | Brier | Hit | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|---:|---:|
| 180 | 0.1911 | 1.0098 | 0.6185 | 0.5455 | -0.0067 | 22 |
| 200 | 0.1883 | 1.001 | 0.6118 | 0.5455 | -0.0039 | 22 |
| 220 | 0.1863 | 0.9946 | 0.6065 | 0.5455 | -0.0019 | 22 |
| 240 | 0.1844 | 0.9873 | 0.6007 | 0.5455 | 0.0 | 22 |
| 260 | 0.1832 | 0.9834 | 0.5968 | 0.5455 | 0.0012 | 22 |
| 280 | 0.1826 | 0.9817 | 0.5943 | 0.5455 | 0.0018 | 22 |
| 320 | 0.1823 | 0.9816 | 0.5919 | 0.5455 | 0.0021 | 22 |

## Sanity: Live-rho-Grid (kein Treiber der Empfehlung)

| rho | RPS | LogLoss | Brier | Hit | n |
|---:|---:|---:|---:|---:|---:|
| 0.0 | 0.1844 | 0.9873 | 0.6007 | 0.5455 | 22 |
| -0.05 | 0.184 | 0.9815 | 0.598 | 0.5455 | 22 |
| -0.1 | 0.1836 | 0.9766 | 0.5957 | 0.5455 | 22 |
| -0.15 | 0.1832 | 0.9724 | 0.5937 | 0.5455 | 22 |
| -0.2 | 0.1829 | 0.969 | 0.592 | 0.5455 | 22 |

## Kandidat

- ELO_PER_GOAL: `180.0`
- rho: `0.0`
- Walk-forward RPS: `0.1186`
- Marge gegen aktuelle Config: `0.0123`
- stabil ueber Folds: `True`
- LogLoss-Guard OK: `True`
- Uebernahme-reif: `False`

## Input-Audit

- snapshots: `49`
- resolved: `23`
- entries: `224`
- missing_model_inputs: `126`
- missing_baseline_total_goals: `40`
- cases: `22`

_Keine automatische Aenderung an config.py. Parameter-Aenderungen bleiben Menschenentscheidung._

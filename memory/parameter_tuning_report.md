# Parameter-Tuning-Report

Status: **diagnostic**
n=41 | Diagnose ab n>=20 | Uebernahme erst ab n>=50

## Aktuelle Config

- ELO_PER_GOAL: `240.0`
- DIXON_COLES_RHO: `-0.1`
- BASELINE_TOTAL_GOALS: `2.6`

## rho-Anker

- rho: `0.0` (backtest.py StatsBomb WM 2018/22, ok)

## Headline: Walk-forward ELO_PER_GOAL

| ELO_PER_GOAL | RPS | LogLoss | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|
| 180 | 0.1417 | 0.7604 | 0.0074 | 21 |
| 200 | 0.1442 | 0.7697 | 0.0048 | 21 |
| 220 | 0.147 | 0.7804 | 0.0021 | 21 |
| 240 | 0.1491 | 0.7855 | 0.0 | 21 |
| 260 | 0.1509 | 0.7905 | -0.0019 | 21 |
| 280 | 0.1528 | 0.7964 | -0.0037 | 21 |
| 320 | 0.1566 | 0.8093 | -0.0076 | 21 |

## Diagnose: In-sample Score-Flaeche

| ELO_PER_GOAL | RPS | LogLoss | Brier | Hit | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|---:|---:|
| 180 | 0.1679 | 0.8829 | 0.5313 | 0.6585 | 0.0003 | 41 |
| 200 | 0.1678 | 0.883 | 0.5303 | 0.6585 | 0.0004 | 41 |
| 220 | 0.1682 | 0.885 | 0.5302 | 0.6585 | 0.0 | 41 |
| 240 | 0.1682 | 0.8836 | 0.5288 | 0.6585 | 0.0 | 41 |
| 260 | 0.1685 | 0.8839 | 0.528 | 0.6585 | -0.0003 | 41 |
| 280 | 0.1691 | 0.8858 | 0.5282 | 0.6585 | -0.0009 | 41 |
| 320 | 0.1708 | 0.892 | 0.5301 | 0.6585 | -0.0026 | 41 |

## Sanity: Live-rho-Grid (kein Treiber der Empfehlung)

| rho | RPS | LogLoss | Brier | Hit | n |
|---:|---:|---:|---:|---:|---:|
| 0.0 | 0.1682 | 0.8836 | 0.5288 | 0.6585 | 41 |
| -0.05 | 0.1682 | 0.8812 | 0.5286 | 0.6585 | 41 |
| -0.1 | 0.1682 | 0.8793 | 0.5286 | 0.6585 | 41 |
| -0.15 | 0.1682 | 0.8781 | 0.529 | 0.6585 | 41 |
| -0.2 | 0.1684 | 0.8774 | 0.5297 | 0.6585 | 41 |

## Kandidat

- ELO_PER_GOAL: `180.0`
- rho: `0.0`
- Walk-forward RPS: `0.1417`
- Marge gegen aktuelle Config: `0.0074`
- stabil ueber Folds: `False`
- LogLoss-Guard OK: `True`
- Uebernahme-reif: `False`

## Input-Audit

- snapshots: `63`
- resolved: `42`
- entries: `321`
- missing_model_inputs: `126`
- missing_baseline_total_goals: `39`
- cases: `41`

_Keine automatische Aenderung an config.py. Parameter-Aenderungen bleiben Menschenentscheidung._

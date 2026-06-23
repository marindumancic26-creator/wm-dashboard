# Parameter-Tuning-Report

Status: **diagnostic**
n=37 | Diagnose ab n>=20 | Uebernahme erst ab n>=50

## Aktuelle Config

- ELO_PER_GOAL: `240.0`
- DIXON_COLES_RHO: `-0.1`
- BASELINE_TOTAL_GOALS: `2.6`

## rho-Anker

- rho: `0.0` (backtest.py StatsBomb WM 2018/22, ok)

## Headline: Walk-forward ELO_PER_GOAL

| ELO_PER_GOAL | RPS | LogLoss | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|
| 180 | 0.1217 | 0.6557 | 0.0082 | 19 |
| 200 | 0.1241 | 0.6657 | 0.0057 | 19 |
| 220 | 0.1269 | 0.6774 | 0.003 | 19 |
| 240 | 0.1298 | 0.6899 | 0.0 | 19 |
| 260 | 0.1329 | 0.7033 | -0.0031 | 19 |
| 280 | 0.1359 | 0.7159 | -0.0061 | 19 |
| 320 | 0.1418 | 0.7389 | -0.012 | 19 |

## Diagnose: In-sample Score-Flaeche

| ELO_PER_GOAL | RPS | LogLoss | Brier | Hit | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|---:|---:|
| 180 | 0.1664 | 0.8692 | 0.5232 | 0.6486 | -0.0013 | 37 |
| 200 | 0.1655 | 0.8667 | 0.5203 | 0.6486 | -0.0004 | 37 |
| 220 | 0.1653 | 0.8665 | 0.5188 | 0.6486 | -0.0002 | 37 |
| 240 | 0.1651 | 0.8664 | 0.5172 | 0.6486 | 0.0 | 37 |
| 260 | 0.1655 | 0.8689 | 0.5171 | 0.6486 | -0.0004 | 37 |
| 280 | 0.1662 | 0.8725 | 0.5178 | 0.6486 | -0.0011 | 37 |
| 320 | 0.1681 | 0.8811 | 0.5208 | 0.6486 | -0.003 | 37 |

## Sanity: Live-rho-Grid (kein Treiber der Empfehlung)

| rho | RPS | LogLoss | Brier | Hit | n |
|---:|---:|---:|---:|---:|---:|
| 0.0 | 0.1651 | 0.8664 | 0.5172 | 0.6486 | 37 |
| -0.05 | 0.165 | 0.8639 | 0.5166 | 0.6486 | 37 |
| -0.1 | 0.165 | 0.862 | 0.5164 | 0.6486 | 37 |
| -0.15 | 0.165 | 0.8607 | 0.5164 | 0.6486 | 37 |
| -0.2 | 0.1651 | 0.86 | 0.5167 | 0.6486 | 37 |

## Kandidat

- ELO_PER_GOAL: `180.0`
- rho: `0.0`
- Walk-forward RPS: `0.1217`
- Marge gegen aktuelle Config: `0.0082`
- stabil ueber Folds: `True`
- LogLoss-Guard OK: `True`
- Uebernahme-reif: `False`

## Input-Audit

- snapshots: `62`
- resolved: `38`
- entries: `310`
- missing_model_inputs: `126`
- missing_baseline_total_goals: `39`
- cases: `37`

_Keine automatische Aenderung an config.py. Parameter-Aenderungen bleiben Menschenentscheidung._

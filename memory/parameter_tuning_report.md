# Parameter-Tuning-Report

Status: **diagnostic**
n=62 | Diagnose ab n>=20 | Uebernahme erst ab n>=50

## Aktuelle Config

- ELO_PER_GOAL: `240.0`
- DIXON_COLES_RHO: `-0.1`
- BASELINE_TOTAL_GOALS: `2.6`

## rho-Anker

- rho: `0.0` (backtest.py StatsBomb WM 2018/22, ok)

## Headline: Walk-forward ELO_PER_GOAL

| ELO_PER_GOAL | RPS | LogLoss | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|
| 180 | 0.1274 | 0.7128 | 0.0082 | 31 |
| 200 | 0.1302 | 0.7256 | 0.0054 | 31 |
| 220 | 0.1331 | 0.7381 | 0.0025 | 31 |
| 240 | 0.1356 | 0.7467 | 0.0 | 31 |
| 260 | 0.1381 | 0.7553 | -0.0025 | 31 |
| 280 | 0.1404 | 0.764 | -0.0049 | 31 |
| 320 | 0.1452 | 0.7809 | -0.0096 | 31 |

## Diagnose: In-sample Score-Flaeche

| ELO_PER_GOAL | RPS | LogLoss | Brier | Hit | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|---:|---:|
| 180 | 0.1558 | 0.8376 | 0.4946 | 0.6452 | 0.0017 | 62 |
| 200 | 0.1561 | 0.8404 | 0.4952 | 0.6452 | 0.0014 | 62 |
| 220 | 0.1568 | 0.8448 | 0.4968 | 0.6452 | 0.0007 | 62 |
| 240 | 0.1575 | 0.8471 | 0.4976 | 0.6452 | 0.0 | 62 |
| 260 | 0.1584 | 0.8508 | 0.499 | 0.6452 | -0.0009 | 62 |
| 280 | 0.1595 | 0.8553 | 0.501 | 0.6452 | -0.002 | 62 |
| 320 | 0.1622 | 0.8653 | 0.506 | 0.6452 | -0.0047 | 62 |

## Sanity: Live-rho-Grid (kein Treiber der Empfehlung)

| rho | RPS | LogLoss | Brier | Hit | n |
|---:|---:|---:|---:|---:|---:|
| 0.0 | 0.1575 | 0.8471 | 0.4976 | 0.6452 | 62 |
| -0.05 | 0.1573 | 0.8445 | 0.4968 | 0.6452 | 62 |
| -0.1 | 0.1573 | 0.8425 | 0.4963 | 0.6452 | 62 |
| -0.15 | 0.1572 | 0.841 | 0.4961 | 0.6452 | 62 |
| -0.2 | 0.1572 | 0.8402 | 0.4962 | 0.6452 | 62 |

## Kandidat

- ELO_PER_GOAL: `180.0`
- rho: `0.0`
- Walk-forward RPS: `0.1274`
- Marge gegen aktuelle Config: `0.0082`
- stabil ueber Folds: `False`
- LogLoss-Guard OK: `True`
- Uebernahme-reif: `False`

## Input-Audit

- snapshots: `71`
- resolved: `63`
- entries: `374`
- missing_model_inputs: `126`
- missing_baseline_total_goals: `40`
- cases: `62`

_Keine automatische Aenderung an config.py. Parameter-Aenderungen bleiben Menschenentscheidung._

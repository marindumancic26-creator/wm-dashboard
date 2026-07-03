# Parameter-Tuning-Report

Status: **diagnostic**
n=74 | Diagnose ab n>=20 | Uebernahme erst ab n>=50

## Aktuelle Config

- ELO_PER_GOAL: `240.0`
- DIXON_COLES_RHO: `-0.1`
- BASELINE_TOTAL_GOALS: `2.6`

## rho-Anker

- rho: `0.0` (backtest.py StatsBomb WM 2018/22, ok)

## Headline: Walk-forward ELO_PER_GOAL

| ELO_PER_GOAL | RPS | LogLoss | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|
| 180 | 0.1434 | 0.7411 | 0.0078 | 37 |
| 200 | 0.1459 | 0.7539 | 0.0053 | 37 |
| 220 | 0.1488 | 0.7664 | 0.0024 | 37 |
| 240 | 0.1512 | 0.7749 | 0.0 | 37 |
| 260 | 0.1535 | 0.7826 | -0.0023 | 37 |
| 280 | 0.1558 | 0.7903 | -0.0046 | 37 |
| 320 | 0.1602 | 0.805 | -0.009 | 37 |

## Diagnose: In-sample Score-Flaeche

| ELO_PER_GOAL | RPS | LogLoss | Brier | Hit | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|---:|---:|
| 180 | 0.1549 | 0.8052 | 0.4699 | 0.6757 | 0.0033 | 74 |
| 200 | 0.1557 | 0.8103 | 0.4721 | 0.6757 | 0.0025 | 74 |
| 220 | 0.157 | 0.8165 | 0.475 | 0.6757 | 0.0012 | 74 |
| 240 | 0.1582 | 0.8206 | 0.4771 | 0.6757 | 0.0 | 74 |
| 260 | 0.1595 | 0.8258 | 0.4797 | 0.6757 | -0.0013 | 74 |
| 280 | 0.161 | 0.8314 | 0.4826 | 0.6757 | -0.0028 | 74 |
| 320 | 0.1642 | 0.843 | 0.489 | 0.6757 | -0.006 | 74 |

## Sanity: Live-rho-Grid (kein Treiber der Empfehlung)

| rho | RPS | LogLoss | Brier | Hit | n |
|---:|---:|---:|---:|---:|---:|
| 0.0 | 0.1582 | 0.8206 | 0.4771 | 0.6757 | 74 |
| -0.05 | 0.1582 | 0.8203 | 0.4776 | 0.6757 | 74 |
| -0.1 | 0.1584 | 0.8205 | 0.4783 | 0.6757 | 74 |
| -0.15 | 0.1585 | 0.8212 | 0.4794 | 0.6757 | 74 |
| -0.2 | 0.1588 | 0.8224 | 0.4807 | 0.6757 | 74 |

## Kandidat

- ELO_PER_GOAL: `180.0`
- rho: `0.0`
- Walk-forward RPS: `0.1434`
- Marge gegen aktuelle Config: `0.0078`
- stabil ueber Folds: `True`
- LogLoss-Guard OK: `True`
- Uebernahme-reif: `False`

## Input-Audit

- snapshots: `82`
- resolved: `75`
- entries: `419`
- missing_model_inputs: `126`
- missing_baseline_total_goals: `40`
- cases: `74`

_Keine automatische Aenderung an config.py. Parameter-Aenderungen bleiben Menschenentscheidung._

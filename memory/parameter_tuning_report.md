# Parameter-Tuning-Report

Status: **diagnostic**
n=75 | Diagnose ab n>=20 | Uebernahme erst ab n>=50

## Aktuelle Config

- ELO_PER_GOAL: `240.0`
- DIXON_COLES_RHO: `-0.1`
- BASELINE_TOTAL_GOALS: `2.6`

## rho-Anker

- rho: `0.0` (backtest.py StatsBomb WM 2018/22, ok)

## Headline: Walk-forward ELO_PER_GOAL

| ELO_PER_GOAL | RPS | LogLoss | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|
| 180 | 0.1472 | 0.75 | 0.0071 | 38 |
| 200 | 0.1495 | 0.7619 | 0.0048 | 38 |
| 220 | 0.1521 | 0.7737 | 0.0022 | 38 |
| 240 | 0.1544 | 0.7815 | 0.0 | 38 |
| 260 | 0.1565 | 0.7887 | -0.0021 | 38 |
| 280 | 0.1587 | 0.7959 | -0.0043 | 38 |
| 320 | 0.1628 | 0.8099 | -0.0084 | 38 |

## Diagnose: In-sample Score-Flaeche

| ELO_PER_GOAL | RPS | LogLoss | Brier | Hit | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|---:|---:|
| 180 | 0.1567 | 0.8088 | 0.4724 | 0.6667 | 0.003 | 75 |
| 200 | 0.1574 | 0.8136 | 0.4743 | 0.6667 | 0.0023 | 75 |
| 220 | 0.1586 | 0.8195 | 0.4771 | 0.6667 | 0.0011 | 75 |
| 240 | 0.1597 | 0.8234 | 0.479 | 0.6667 | 0.0 | 75 |
| 260 | 0.1609 | 0.8283 | 0.4815 | 0.68 | -0.0012 | 75 |
| 280 | 0.1624 | 0.8337 | 0.4843 | 0.68 | -0.0027 | 75 |
| 320 | 0.1654 | 0.845 | 0.4904 | 0.68 | -0.0057 | 75 |

## Sanity: Live-rho-Grid (kein Treiber der Empfehlung)

| rho | RPS | LogLoss | Brier | Hit | n |
|---:|---:|---:|---:|---:|---:|
| 0.0 | 0.1597 | 0.8234 | 0.479 | 0.6667 | 75 |
| -0.05 | 0.1598 | 0.8233 | 0.4796 | 0.6667 | 75 |
| -0.1 | 0.1599 | 0.8238 | 0.4805 | 0.6667 | 75 |
| -0.15 | 0.1601 | 0.8247 | 0.4817 | 0.6667 | 75 |
| -0.2 | 0.1604 | 0.8262 | 0.4833 | 0.6667 | 75 |

## Kandidat

- ELO_PER_GOAL: `180.0`
- rho: `0.0`
- Walk-forward RPS: `0.1472`
- Marge gegen aktuelle Config: `0.0071`
- stabil ueber Folds: `True`
- LogLoss-Guard OK: `True`
- Uebernahme-reif: `False`

## Input-Audit

- snapshots: `83`
- resolved: `76`
- entries: `426`
- missing_model_inputs: `126`
- missing_baseline_total_goals: `40`
- cases: `75`

_Keine automatische Aenderung an config.py. Parameter-Aenderungen bleiben Menschenentscheidung._

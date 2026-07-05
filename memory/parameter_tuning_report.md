# Parameter-Tuning-Report

Status: **diagnostic**
n=78 | Diagnose ab n>=20 | Uebernahme erst ab n>=50

## Aktuelle Config

- ELO_PER_GOAL: `240.0`
- DIXON_COLES_RHO: `-0.1`
- BASELINE_TOTAL_GOALS: `2.6`

## rho-Anker

- rho: `0.0` (backtest.py StatsBomb WM 2018/22, ok)

## Headline: Walk-forward ELO_PER_GOAL

| ELO_PER_GOAL | RPS | LogLoss | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|
| 180 | 0.1418 | 0.727 | 0.0072 | 39 |
| 200 | 0.1441 | 0.7391 | 0.005 | 39 |
| 220 | 0.1467 | 0.7518 | 0.0024 | 39 |
| 240 | 0.149 | 0.7607 | 0.0 | 39 |
| 260 | 0.1514 | 0.7688 | -0.0023 | 39 |
| 280 | 0.1536 | 0.7769 | -0.0046 | 39 |
| 320 | 0.158 | 0.7924 | -0.009 | 39 |

## Diagnose: In-sample Score-Flaeche

| ELO_PER_GOAL | RPS | LogLoss | Brier | Hit | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|---:|---:|
| 180 | 0.1538 | 0.7932 | 0.4618 | 0.6795 | 0.0035 | 78 |
| 200 | 0.1547 | 0.7986 | 0.4641 | 0.6795 | 0.0026 | 78 |
| 220 | 0.1561 | 0.8054 | 0.4673 | 0.6795 | 0.0012 | 78 |
| 240 | 0.1573 | 0.8103 | 0.4698 | 0.6795 | 0.0 | 78 |
| 260 | 0.1588 | 0.816 | 0.4727 | 0.6923 | -0.0015 | 78 |
| 280 | 0.1604 | 0.8221 | 0.476 | 0.6923 | -0.0031 | 78 |
| 320 | 0.1637 | 0.8344 | 0.4828 | 0.6923 | -0.0064 | 78 |

## Sanity: Live-rho-Grid (kein Treiber der Empfehlung)

| rho | RPS | LogLoss | Brier | Hit | n |
|---:|---:|---:|---:|---:|---:|
| 0.0 | 0.1573 | 0.8103 | 0.4698 | 0.6795 | 78 |
| -0.05 | 0.1575 | 0.8105 | 0.4706 | 0.6795 | 78 |
| -0.1 | 0.1577 | 0.8113 | 0.4717 | 0.6795 | 78 |
| -0.15 | 0.1579 | 0.8125 | 0.4731 | 0.6795 | 78 |
| -0.2 | 0.1582 | 0.8143 | 0.4748 | 0.6795 | 78 |

## Kandidat

- ELO_PER_GOAL: `180.0`
- rho: `0.0`
- Walk-forward RPS: `0.1418`
- Marge gegen aktuelle Config: `0.0072`
- stabil ueber Folds: `False`
- LogLoss-Guard OK: `True`
- Uebernahme-reif: `False`

## Input-Audit

- snapshots: `88`
- resolved: `79`
- entries: `449`
- missing_model_inputs: `126`
- missing_baseline_total_goals: `40`
- cases: `78`

_Keine automatische Aenderung an config.py. Parameter-Aenderungen bleiben Menschenentscheidung._

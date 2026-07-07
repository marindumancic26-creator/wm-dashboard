# Parameter-Tuning-Report

Status: **diagnostic**
n=82 | Diagnose ab n>=20 | Uebernahme erst ab n>=50

## Aktuelle Config

- ELO_PER_GOAL: `240.0`
- DIXON_COLES_RHO: `-0.1`
- BASELINE_TOTAL_GOALS: `2.6`

## rho-Anker

- rho: `0.0` (backtest.py StatsBomb WM 2018/22, ok)

## Headline: Walk-forward ELO_PER_GOAL

| ELO_PER_GOAL | RPS | LogLoss | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|
| 180 | 0.1487 | 0.7169 | 0.0069 | 41 |
| 200 | 0.1507 | 0.7276 | 0.0049 | 41 |
| 220 | 0.153 | 0.739 | 0.0025 | 41 |
| 240 | 0.1556 | 0.7501 | 0.0 | 41 |
| 260 | 0.1581 | 0.761 | -0.0026 | 41 |
| 280 | 0.1607 | 0.771 | -0.0052 | 41 |
| 320 | 0.1656 | 0.7891 | -0.01 | 41 |

## Diagnose: In-sample Score-Flaeche

| ELO_PER_GOAL | RPS | LogLoss | Brier | Hit | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|---:|---:|
| 180 | 0.1588 | 0.8021 | 0.4668 | 0.6829 | 0.0036 | 82 |
| 200 | 0.1598 | 0.8074 | 0.4693 | 0.6829 | 0.0026 | 82 |
| 220 | 0.1612 | 0.8139 | 0.4725 | 0.6829 | 0.0012 | 82 |
| 240 | 0.1624 | 0.8187 | 0.4751 | 0.6829 | 0.0 | 82 |
| 260 | 0.1639 | 0.8242 | 0.478 | 0.6951 | -0.0015 | 82 |
| 280 | 0.1654 | 0.8301 | 0.4812 | 0.6951 | -0.003 | 82 |
| 320 | 0.1687 | 0.842 | 0.4879 | 0.6951 | -0.0063 | 82 |

## Sanity: Live-rho-Grid (kein Treiber der Empfehlung)

| rho | RPS | LogLoss | Brier | Hit | n |
|---:|---:|---:|---:|---:|---:|
| 0.0 | 0.1624 | 0.8187 | 0.4751 | 0.6829 | 82 |
| -0.05 | 0.1626 | 0.8197 | 0.4762 | 0.6829 | 82 |
| -0.1 | 0.1629 | 0.8212 | 0.4777 | 0.6829 | 82 |
| -0.15 | 0.1632 | 0.8232 | 0.4794 | 0.6829 | 82 |
| -0.2 | 0.1635 | 0.8256 | 0.4814 | 0.6829 | 82 |

## Kandidat

- ELO_PER_GOAL: `180.0`
- rho: `0.0`
- Walk-forward RPS: `0.1487`
- Marge gegen aktuelle Config: `0.0069`
- stabil ueber Folds: `False`
- LogLoss-Guard OK: `True`
- Uebernahme-reif: `False`

## Input-Audit

- snapshots: `95`
- resolved: `83`
- entries: `475`
- missing_model_inputs: `126`
- missing_baseline_total_goals: `41`
- cases: `82`

_Keine automatische Aenderung an config.py. Parameter-Aenderungen bleiben Menschenentscheidung._

# Parameter-Tuning-Report

Status: **diagnostic**
n=76 | Diagnose ab n>=20 | Uebernahme erst ab n>=50

## Aktuelle Config

- ELO_PER_GOAL: `240.0`
- DIXON_COLES_RHO: `-0.1`
- BASELINE_TOTAL_GOALS: `2.6`

## rho-Anker

- rho: `0.0` (backtest.py StatsBomb WM 2018/22, ok)

## Headline: Walk-forward ELO_PER_GOAL

| ELO_PER_GOAL | RPS | LogLoss | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|
| 180 | 0.1454 | 0.742 | 0.0068 | 38 |
| 200 | 0.1474 | 0.7533 | 0.0048 | 38 |
| 220 | 0.1499 | 0.7653 | 0.0023 | 38 |
| 240 | 0.1522 | 0.7736 | 0.0 | 38 |
| 260 | 0.1544 | 0.7812 | -0.0022 | 38 |
| 280 | 0.1565 | 0.7888 | -0.0043 | 38 |
| 320 | 0.1608 | 0.8035 | -0.0086 | 38 |

## Diagnose: In-sample Score-Flaeche

| ELO_PER_GOAL | RPS | LogLoss | Brier | Hit | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|---:|---:|
| 180 | 0.1547 | 0.8002 | 0.4666 | 0.6711 | 0.0032 | 76 |
| 200 | 0.1555 | 0.8051 | 0.4686 | 0.6711 | 0.0024 | 76 |
| 220 | 0.1568 | 0.8114 | 0.4715 | 0.6711 | 0.0011 | 76 |
| 240 | 0.1579 | 0.8158 | 0.4738 | 0.6711 | 0.0 | 76 |
| 260 | 0.1593 | 0.8211 | 0.4764 | 0.6842 | -0.0014 | 76 |
| 280 | 0.1608 | 0.827 | 0.4795 | 0.6842 | -0.0029 | 76 |
| 320 | 0.164 | 0.8389 | 0.486 | 0.6842 | -0.0061 | 76 |

## Sanity: Live-rho-Grid (kein Treiber der Empfehlung)

| rho | RPS | LogLoss | Brier | Hit | n |
|---:|---:|---:|---:|---:|---:|
| 0.0 | 0.1579 | 0.8158 | 0.4738 | 0.6711 | 76 |
| -0.05 | 0.158 | 0.8158 | 0.4744 | 0.6711 | 76 |
| -0.1 | 0.1582 | 0.8163 | 0.4753 | 0.6711 | 76 |
| -0.15 | 0.1584 | 0.8173 | 0.4766 | 0.6711 | 76 |
| -0.2 | 0.1586 | 0.8188 | 0.4781 | 0.6711 | 76 |

## Kandidat

- ELO_PER_GOAL: `180.0`
- rho: `0.0`
- Walk-forward RPS: `0.1454`
- Marge gegen aktuelle Config: `0.0068`
- stabil ueber Folds: `True`
- LogLoss-Guard OK: `True`
- Uebernahme-reif: `False`

## Input-Audit

- snapshots: `85`
- resolved: `77`
- entries: `434`
- missing_model_inputs: `126`
- missing_baseline_total_goals: `40`
- cases: `76`

_Keine automatische Aenderung an config.py. Parameter-Aenderungen bleiben Menschenentscheidung._

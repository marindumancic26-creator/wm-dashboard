# Parameter-Tuning-Report

Status: **diagnostic**
n=77 | Diagnose ab n>=20 | Uebernahme erst ab n>=50

## Aktuelle Config

- ELO_PER_GOAL: `240.0`
- DIXON_COLES_RHO: `-0.1`
- BASELINE_TOTAL_GOALS: `2.6`

## rho-Anker

- rho: `0.0` (backtest.py StatsBomb WM 2018/22, ok)

## Headline: Walk-forward ELO_PER_GOAL

| ELO_PER_GOAL | RPS | LogLoss | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|
| 180 | 0.1474 | 0.7453 | 0.0071 | 39 |
| 200 | 0.1495 | 0.7569 | 0.0049 | 39 |
| 220 | 0.1521 | 0.7691 | 0.0023 | 39 |
| 240 | 0.1544 | 0.7775 | 0.0 | 39 |
| 260 | 0.1567 | 0.7852 | -0.0022 | 39 |
| 280 | 0.1589 | 0.7929 | -0.0044 | 39 |
| 320 | 0.1632 | 0.8076 | -0.0088 | 39 |

## Diagnose: In-sample Score-Flaeche

| ELO_PER_GOAL | RPS | LogLoss | Brier | Hit | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|---:|---:|
| 180 | 0.1556 | 0.8012 | 0.4672 | 0.6753 | 0.0034 | 77 |
| 200 | 0.1565 | 0.8062 | 0.4694 | 0.6753 | 0.0025 | 77 |
| 220 | 0.1578 | 0.8127 | 0.4724 | 0.6753 | 0.0012 | 77 |
| 240 | 0.159 | 0.8172 | 0.4747 | 0.6753 | 0.0 | 77 |
| 260 | 0.1604 | 0.8226 | 0.4775 | 0.6883 | -0.0014 | 77 |
| 280 | 0.1619 | 0.8285 | 0.4806 | 0.6883 | -0.0029 | 77 |
| 320 | 0.1651 | 0.8405 | 0.4872 | 0.6883 | -0.0061 | 77 |

## Sanity: Live-rho-Grid (kein Treiber der Empfehlung)

| rho | RPS | LogLoss | Brier | Hit | n |
|---:|---:|---:|---:|---:|---:|
| 0.0 | 0.159 | 0.8172 | 0.4747 | 0.6753 | 77 |
| -0.05 | 0.1591 | 0.8174 | 0.4755 | 0.6753 | 77 |
| -0.1 | 0.1593 | 0.8181 | 0.4766 | 0.6753 | 77 |
| -0.15 | 0.1595 | 0.8193 | 0.4779 | 0.6753 | 77 |
| -0.2 | 0.1598 | 0.821 | 0.4796 | 0.6753 | 77 |

## Kandidat

- ELO_PER_GOAL: `180.0`
- rho: `0.0`
- Walk-forward RPS: `0.1474`
- Marge gegen aktuelle Config: `0.0071`
- stabil ueber Folds: `True`
- LogLoss-Guard OK: `True`
- Uebernahme-reif: `False`

## Input-Audit

- snapshots: `87`
- resolved: `78`
- entries: `441`
- missing_model_inputs: `126`
- missing_baseline_total_goals: `40`
- cases: `77`

_Keine automatische Aenderung an config.py. Parameter-Aenderungen bleiben Menschenentscheidung._

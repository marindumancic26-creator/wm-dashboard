# Parameter-Tuning-Report

Status: **diagnostic**
n=84 | Diagnose ab n>=20 | Uebernahme erst ab n>=50

## Aktuelle Config

- ELO_PER_GOAL: `240.0`
- DIXON_COLES_RHO: `-0.1`
- BASELINE_TOTAL_GOALS: `2.6`

## rho-Anker

- rho: `0.0` (backtest.py StatsBomb WM 2018/22, ok)

## Headline: Walk-forward ELO_PER_GOAL

| ELO_PER_GOAL | RPS | LogLoss | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|
| 180 | 0.1523 | 0.7229 | 0.0057 | 42 |
| 200 | 0.1538 | 0.7324 | 0.0042 | 42 |
| 220 | 0.1558 | 0.7429 | 0.0022 | 42 |
| 240 | 0.158 | 0.7533 | 0.0 | 42 |
| 260 | 0.1604 | 0.7635 | -0.0024 | 42 |
| 280 | 0.1627 | 0.7731 | -0.0047 | 42 |
| 320 | 0.1672 | 0.7903 | -0.0092 | 42 |

## Diagnose: In-sample Score-Flaeche

| ELO_PER_GOAL | RPS | LogLoss | Brier | Hit | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|---:|---:|
| 180 | 0.159 | 0.7979 | 0.4645 | 0.6786 | 0.0034 | 84 |
| 200 | 0.1599 | 0.8031 | 0.4668 | 0.6786 | 0.0025 | 84 |
| 220 | 0.1612 | 0.8097 | 0.4699 | 0.6786 | 0.0012 | 84 |
| 240 | 0.1624 | 0.8144 | 0.4724 | 0.6786 | 0.0 | 84 |
| 260 | 0.1638 | 0.82 | 0.4752 | 0.6905 | -0.0014 | 84 |
| 280 | 0.1653 | 0.8259 | 0.4784 | 0.6905 | -0.0029 | 84 |
| 320 | 0.1686 | 0.8379 | 0.4852 | 0.6905 | -0.0062 | 84 |

## Sanity: Live-rho-Grid (kein Treiber der Empfehlung)

| rho | RPS | LogLoss | Brier | Hit | n |
|---:|---:|---:|---:|---:|---:|
| 0.0 | 0.1624 | 0.8144 | 0.4724 | 0.6786 | 84 |
| -0.05 | 0.1626 | 0.8157 | 0.4736 | 0.6786 | 84 |
| -0.1 | 0.1629 | 0.8174 | 0.4752 | 0.6786 | 84 |
| -0.15 | 0.1632 | 0.8196 | 0.477 | 0.6786 | 84 |
| -0.2 | 0.1635 | 0.8223 | 0.4792 | 0.6786 | 84 |

## Kandidat

- ELO_PER_GOAL: `180.0`
- rho: `0.0`
- Walk-forward RPS: `0.1523`
- Marge gegen aktuelle Config: `0.0057`
- stabil ueber Folds: `False`
- LogLoss-Guard OK: `True`
- Uebernahme-reif: `False`

## Input-Audit

- snapshots: `100`
- resolved: `85`
- entries: `486`
- missing_model_inputs: `126`
- missing_baseline_total_goals: `41`
- cases: `84`

_Keine automatische Aenderung an config.py. Parameter-Aenderungen bleiben Menschenentscheidung._

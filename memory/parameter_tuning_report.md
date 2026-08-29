# Parameter-Tuning-Report

Status: **diagnostic**
n=92 | Diagnose ab n>=20 | Uebernahme erst ab n>=50

## Aktuelle Config

- ELO_PER_GOAL: `240.0`
- DIXON_COLES_RHO: `-0.1`
- BASELINE_TOTAL_GOALS: `2.6`

## rho-Anker

- rho: `-0.1` (config fallback, fallback)
- Hinweis: Keine StatsBomb-WM-Daten geladen.

## Headline: Walk-forward ELO_PER_GOAL

| ELO_PER_GOAL | RPS | LogLoss | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|
| 180 | 0.1504 | 0.717 | 0.009 | 46 |
| 200 | 0.1533 | 0.7308 | 0.0061 | 46 |
| 220 | 0.1564 | 0.7446 | 0.003 | 46 |
| 240 | 0.1594 | 0.7573 | 0.0 | 46 |
| 260 | 0.1624 | 0.7694 | -0.003 | 46 |
| 280 | 0.1653 | 0.7805 | -0.0059 | 46 |
| 320 | 0.1706 | 0.7998 | -0.0112 | 46 |

## Diagnose: In-sample Score-Flaeche

| ELO_PER_GOAL | RPS | LogLoss | Brier | Hit | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|---:|---:|
| 180 | 0.1585 | 0.7882 | 0.4565 | 0.6957 | 0.0047 | 92 |
| 200 | 0.1599 | 0.795 | 0.4603 | 0.6957 | 0.0033 | 92 |
| 220 | 0.1616 | 0.8028 | 0.4647 | 0.6957 | 0.0016 | 92 |
| 240 | 0.1632 | 0.8087 | 0.4682 | 0.6957 | 0.0 | 92 |
| 260 | 0.165 | 0.8152 | 0.472 | 0.7065 | -0.0018 | 92 |
| 280 | 0.1667 | 0.8219 | 0.4759 | 0.7065 | -0.0035 | 92 |
| 320 | 0.1704 | 0.8351 | 0.4838 | 0.7065 | -0.0072 | 92 |

## Sanity: Live-rho-Grid (kein Treiber der Empfehlung)

| rho | RPS | LogLoss | Brier | Hit | n |
|---:|---:|---:|---:|---:|---:|
| 0.0 | 0.1626 | 0.8041 | 0.4644 | 0.6957 | 92 |
| -0.05 | 0.1629 | 0.8061 | 0.4661 | 0.6957 | 92 |
| -0.1 | 0.1632 | 0.8087 | 0.4682 | 0.6957 | 92 |
| -0.15 | 0.1636 | 0.8117 | 0.4706 | 0.6957 | 92 |
| -0.2 | 0.1641 | 0.8151 | 0.4733 | 0.6957 | 92 |

## Kandidat

- ELO_PER_GOAL: `180.0`
- rho: `-0.1`
- Walk-forward RPS: `0.1504`
- Marge gegen aktuelle Config: `0.009`
- stabil ueber Folds: `True`
- LogLoss-Guard OK: `True`
- Uebernahme-reif: `False`

## Input-Audit

- snapshots: `282`
- resolved: `93`
- entries: `530`
- missing_model_inputs: `126`
- missing_baseline_total_goals: `41`
- cases: `92`

_Keine automatische Aenderung an config.py. Parameter-Aenderungen bleiben Menschenentscheidung._

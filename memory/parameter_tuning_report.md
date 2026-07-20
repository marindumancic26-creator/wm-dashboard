# Parameter-Tuning-Report

Status: **diagnostic**
n=91 | Diagnose ab n>=20 | Uebernahme erst ab n>=50

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
| 180 | 0.1458 | 0.7029 | 0.0092 | 46 |
| 200 | 0.1487 | 0.7172 | 0.0063 | 46 |
| 220 | 0.1519 | 0.7313 | 0.0031 | 46 |
| 240 | 0.155 | 0.7445 | 0.0 | 46 |
| 260 | 0.1581 | 0.7569 | -0.0031 | 46 |
| 280 | 0.161 | 0.7683 | -0.006 | 46 |
| 320 | 0.1665 | 0.7881 | -0.0115 | 46 |

## Diagnose: In-sample Score-Flaeche

| ELO_PER_GOAL | RPS | LogLoss | Brier | Hit | Marge RPS vs. aktuell | n |
|---:|---:|---:|---:|---:|---:|---:|
| 180 | 0.1576 | 0.7867 | 0.4555 | 0.6923 | 0.0046 | 91 |
| 200 | 0.159 | 0.7935 | 0.4592 | 0.6923 | 0.0032 | 91 |
| 220 | 0.1607 | 0.8013 | 0.4636 | 0.6923 | 0.0015 | 91 |
| 240 | 0.1622 | 0.8071 | 0.4671 | 0.6923 | 0.0 | 91 |
| 260 | 0.164 | 0.8136 | 0.4708 | 0.7033 | -0.0018 | 91 |
| 280 | 0.1657 | 0.8203 | 0.4747 | 0.7033 | -0.0035 | 91 |
| 320 | 0.1694 | 0.8336 | 0.4826 | 0.7033 | -0.0072 | 91 |

## Sanity: Live-rho-Grid (kein Treiber der Empfehlung)

| rho | RPS | LogLoss | Brier | Hit | n |
|---:|---:|---:|---:|---:|---:|
| 0.0 | 0.1616 | 0.8027 | 0.4633 | 0.6923 | 91 |
| -0.05 | 0.1619 | 0.8047 | 0.4651 | 0.6923 | 91 |
| -0.1 | 0.1622 | 0.8071 | 0.4671 | 0.6923 | 91 |
| -0.15 | 0.1626 | 0.81 | 0.4694 | 0.6923 | 91 |
| -0.2 | 0.1631 | 0.8133 | 0.472 | 0.6923 | 91 |

## Kandidat

- ELO_PER_GOAL: `180.0`
- rho: `-0.1`
- Walk-forward RPS: `0.1458`
- Marge gegen aktuelle Config: `0.0092`
- stabil ueber Folds: `True`
- LogLoss-Guard OK: `True`
- Uebernahme-reif: `False`

## Input-Audit

- snapshots: `167`
- resolved: `92`
- entries: `524`
- missing_model_inputs: `126`
- missing_baseline_total_goals: `41`
- cases: `91`

_Keine automatische Aenderung an config.py. Parameter-Aenderungen bleiben Menschenentscheidung._

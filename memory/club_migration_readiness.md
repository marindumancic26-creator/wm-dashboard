# Vereinsfussball Readiness-Gate

Status: **blocked**  
Auto-Apply: `False`  
Release: `blocked`  

## Shadow-Fixtures

- Status: `degraded`
- Quellen live: `7/8`
- Fixtures: `145`
- Identity pending: `0`

## Backtest

- Status: `diagnostic`
- Historie/OOS: `8908` / `7082`
- Modell-RPS: `0.2082`
- Markt-RPS: `0.1951`
- RPS-Abstand Modell minus Markt: `0.0131`

## Gates

- shadow_all_sources_live: `False`
- no_identity_pending: `True`
- shadow_mode_only: `True`
- prediction_and_value_locked: `True`
- backtest_all_competitions_diagnostic: `True`
- backtest_beats_naive: `True`
- backtest_logloss_guard: `True`
- backtest_beats_market: `False`
- world_cup_finished_confirmed: `False`
- human_approved: `False`

_Dieser Report ist ein Blocker/Pruefpunkt, kein Deployment-Schalter._

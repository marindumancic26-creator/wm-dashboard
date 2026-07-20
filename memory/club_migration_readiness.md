# Vereinsfussball Readiness-Gate

Status: **blocked**  
Auto-Apply: `False`  
Release: `blocked`  

## Shadow-Fixtures

- Status: `live`
- Quellen live: `8/8`
- Fixtures: `203`
- Identity pending: `0`

## Backtest

- Status: `diagnostic`
- Primaerer Kandidat: `decayed_dixon_coles`
- Historie/OOS: `8908` / `7082`
- Modell-RPS: `0.2015`
- Markt-RPS: `0.1944`
- RPS-Abstand Modell minus Markt: `0.0071`

## Gates

- shadow_all_sources_live: `True`
- no_identity_pending: `True`
- shadow_mode_only: `True`
- prediction_and_value_locked: `True`
- backtest_all_competitions_diagnostic: `True`
- backtest_beats_naive: `True`
- backtest_logloss_guard: `True`
- backtest_closing_market_outperformance: `False`
- world_cup_finished_confirmed: `True`
- human_approved: `True`

_Dieser Report ist ein Blocker/Pruefpunkt, kein Deployment-Schalter._

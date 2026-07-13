# Vereinsmodell Walk-forward-Report

Status: **diagnostic**  
Historie: 8908 Spiele; Out-of-sample: 7082  
rho fixiert auf aktuelle Config: `-0.1`  
Primaerer Kandidat: `decayed_dixon_coles`  
Freigabe: **BLOCKIERT** (Report-only, keine Auto-Uebernahme)

| Testsaison | Train n | Test n | Modell RPS | Naiv RPS | Markt RPS | Modell besser? |
|---:|---:|---:|---:|---:|---:|---|

## Wettbewerbe

- `premier_league`: Status `diagnostic`, Historie `1900`, OOS `1520`, Modell-RPS `0.2158`, Markt-RPS `0.1947`
- `la_liga`: Status `diagnostic`, Historie `1900`, OOS `1520`, Modell-RPS `0.2031`, Markt-RPS `0.1919`
- `bundesliga`: Status `diagnostic`, Historie `1530`, OOS `1224`, Modell-RPS `0.2068`, Markt-RPS `0.1953`
- `serie_a`: Status `diagnostic`, Historie `1900`, OOS `1520`, Modell-RPS `0.2022`, Markt-RPS `0.1901`
- `ligue_1`: Status `diagnostic`, Historie `1678`, OOS `1298`, Modell-RPS `0.2135`, Markt-RPS `0.2012`

## Folds je Wettbewerb

| premier_league 2022 | 380 | 380 | 0.2081 | 0.2291 | 0.1975 | True |
| premier_league 2023 | 760 | 380 | 0.195 | 0.234 | 0.1808 | True |
| premier_league 2024 | 1140 | 380 | 0.206 | 0.2356 | 0.1961 | True |
| premier_league 2025 | 1520 | 380 | 0.2083 | 0.2278 | 0.2044 | True |
| la_liga 2022 | 380 | 380 | 0.2096 | 0.228 | 0.2017 | True |
| la_liga 2023 | 760 | 380 | 0.1874 | 0.2241 | 0.1827 | True |
| la_liga 2024 | 1140 | 380 | 0.1955 | 0.2288 | 0.1876 | True |
| la_liga 2025 | 1520 | 380 | 0.1996 | 0.2234 | 0.1956 | True |
| bundesliga 2022 | 306 | 306 | 0.2073 | 0.2263 | 0.2043 | True |
| bundesliga 2023 | 612 | 306 | 0.1965 | 0.2283 | 0.1847 | True |
| bundesliga 2024 | 918 | 306 | 0.2125 | 0.2383 | 0.2016 | True |
| bundesliga 2025 | 1224 | 306 | 0.1945 | 0.2315 | 0.1907 | True |
| serie_a 2022 | 380 | 380 | 0.2003 | 0.2306 | 0.1955 | True |
| serie_a 2023 | 760 | 380 | 0.1921 | 0.2249 | 0.1845 | True |
| serie_a 2024 | 1140 | 380 | 0.1902 | 0.2285 | 0.1844 | True |
| serie_a 2025 | 1520 | 380 | 0.2005 | 0.2333 | 0.1962 | True |
| ligue_1 2022 | 380 | 380 | 0.205 | 0.2335 | 0.1977 | True |
| ligue_1 2023 | 760 | 306 | 0.2152 | 0.2328 | 0.2066 | True |
| ligue_1 2024 | 1066 | 306 | 0.2076 | 0.2362 | 0.2012 | True |
| ligue_1 2025 | 1372 | 306 | 0.2053 | 0.229 | 0.2003 | True |

## Gesamt (Out-of-sample)

- Modell: RPS `0.2015`, LogLoss `0.9898`, Treffer `0.5247` (n=7082)
- Naive Basisrate: RPS `0.2301`, LogLoss `1.0729`, Treffer `0.4373` (n=7082)
- Markt-Benchmark: RPS `0.1944`, LogLoss `0.967`, Treffer `0.5462` (n=7082)
- RPS-Abstand Modell minus Markt: `0.0071`

## Kandidaten

- `decayed_dixon_coles`: Status `diagnostic`, Modell-RPS `0.2015`, Markt-RPS `0.1944`, Delta-RPS `0.0071`, Closing-Gate `False`

## Gates

- minimum_history: `True`
- beats_naive_rps: `True`
- logloss_guard_vs_naive: `True`
- all_competitions_diagnostic: `True`
- market_benchmark_available: `True`
- beats_market_rps: `False`
- closing_market_outperformance: `False`
- closing_gate_closing_coverage: `{'n': 7082, 'covered': 7082, 'rate': 1.0, 'gate': True}`
- closing_gate_aggregate_delta_rps_lt_0: `False`
- closing_gate_aggregate_delta_logloss_lt_0: `False`
- closing_gate_bootstrap_upper95_delta_rps_lt_0: `False`
- closing_gate_bootstrap_upper95_delta_logloss_lt_0: `False`
- closing_gate_league_wins_both: `0`
- closing_gate_league_wins_required: `4`
- closing_gate_league_wins_gate: `False`
- closing_gate_closing_coverage_gate: `True`
- closing_gate_closing_market_outperformance: `False`
- closing_gate_delta_rps: `0.0071`
- closing_gate_delta_logloss: `0.0228`
- closing_gate_upper95_delta_rps: `0.0084`
- closing_gate_upper95_delta_logloss: `0.0264`

## Pflichtdiagnosen

### aufsteiger
- `ja`: n `1146`, Delta RPS `0.0104`, Delta LogLoss `0.035`
- `nein`: n `5936`, Delta RPS `0.0065`, Delta LogLoss `0.0205`
### erste_sechs_spieltage
- `ja`: n `350`, Delta RPS `0.0096`, Delta LogLoss `0.0336`
- `nein`: n `6732`, Delta RPS `0.007`, Delta LogLoss `0.0222`
### remis
- `ja`: n `1789`, Delta RPS `0.0027`, Delta LogLoss `0.0446`
- `nein`: n `5293`, Delta RPS `0.0086`, Delta LogLoss `0.0154`
### staerke_diff_decile
- `1`: n `708`, Delta RPS `0.0086`, Delta LogLoss `0.0216`
- `10`: n `709`, Delta RPS `0.0018`, Delta LogLoss `0.0103`
- `2`: n `708`, Delta RPS `0.0027`, Delta LogLoss `0.0128`
- `3`: n `708`, Delta RPS `0.0105`, Delta LogLoss `0.0298`
- `4`: n `708`, Delta RPS `0.0072`, Delta LogLoss `0.021`
- `5`: n `709`, Delta RPS `0.0106`, Delta LogLoss `0.0312`
- `6`: n `708`, Delta RPS `0.0107`, Delta LogLoss `0.0305`
- `7`: n `708`, Delta RPS `0.0077`, Delta LogLoss `0.0279`
- `8`: n `708`, Delta RPS `0.0067`, Delta LogLoss `0.0255`
- `9`: n `708`, Delta RPS `0.0048`, Delta LogLoss `0.0172`
### favoritenwahrscheinlichkeit
- `flach`: n `2399`, Delta RPS `0.0069`, Delta LogLoss `0.0203`
- `hoch`: n `1685`, Delta RPS `0.0033`, Delta LogLoss `0.0139`
- `mittel`: n `2998`, Delta RPS `0.0094`, Delta LogLoss `0.0297`
### erwartete_tore
- `hoch`: n `3927`, Delta RPS `0.0086`, Delta LogLoss `0.0273`
- `mittel`: n `3074`, Delta RPS `0.0055`, Delta LogLoss `0.0173`
- `niedrig`: n `81`, Delta RPS `0.0031`, Delta LogLoss `0.0094`
### liga
- `bundesliga`: n `1224`, Delta RPS `0.0074`, Delta LogLoss `0.0243`
- `la_liga`: n `1520`, Delta RPS `0.0061`, Delta LogLoss `0.0205`
- `ligue_1`: n `1298`, Delta RPS `0.0069`, Delta LogLoss `0.0213`
- `premier_league`: n `1520`, Delta RPS `0.0097`, Delta LogLoss `0.0301`
- `serie_a`: n `1520`, Delta RPS `0.0057`, Delta LogLoss `0.0178`
### saison
- `2022`: n `1826`, Delta RPS `0.0069`, Delta LogLoss `0.0213`
- `2023`: n `1752`, Delta RPS `0.0093`, Delta LogLoss `0.03`
- `2024`: n `1752`, Delta RPS `0.0081`, Delta LogLoss `0.0258`
- `2025`: n `1752`, Delta RPS `0.0042`, Delta LogLoss `0.014`

_Marktpreise wurden nicht trainiert oder optimiert; sie dienen nur als Diagnose._

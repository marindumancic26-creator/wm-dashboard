# Vereinsmodell Walk-forward-Report

Status: **diagnostic**  
Historie: 8908 Spiele; Out-of-sample: 7082  
rho fixiert auf aktuelle Config: `-0.1`  
Primaerer Kandidat: `closing_residual_blend`
Freigabe: **BLOCKIERT** (Report-only, keine Auto-Uebernahme)

## Wettbewerbe

- `premier_league`: Status `diagnostic`, Historie `1900`, OOS `1520`, Modell-RPS `0.1947`, Markt-RPS `0.1947`
- `la_liga`: Status `diagnostic`, Historie `1900`, OOS `1520`, Modell-RPS `0.1913`, Markt-RPS `0.1919`
- `bundesliga`: Status `diagnostic`, Historie `1530`, OOS `1224`, Modell-RPS `0.1954`, Markt-RPS `0.1953`
- `serie_a`: Status `diagnostic`, Historie `1900`, OOS `1520`, Modell-RPS `0.1897`, Markt-RPS `0.1901`
- `ligue_1`: Status `diagnostic`, Historie `1678`, OOS `1298`, Modell-RPS `0.2013`, Markt-RPS `0.2012`

## Tor-Modell-Folds je Wettbewerb

| Testsaison | Train n | Test n | Modell RPS | Naiv RPS | Markt RPS | Modell besser? |
|---:|---:|---:|---:|---:|---:|---|
| premier_league 2022 | 380 | 380 | 0.2293 | 0.2301 | 0.1975 | True |
| premier_league 2023 | 760 | 380 | 0.2026 | 0.2337 | 0.1808 | True |
| premier_league 2024 | 1140 | 380 | 0.2157 | 0.2358 | 0.1961 | True |
| premier_league 2025 | 1520 | 380 | 0.2157 | 0.2278 | 0.2044 | True |
| la_liga 2022 | 380 | 380 | 0.2152 | 0.2281 | 0.2017 | True |
| la_liga 2023 | 760 | 380 | 0.1913 | 0.2239 | 0.1827 | True |
| la_liga 2024 | 1140 | 380 | 0.1996 | 0.2287 | 0.1876 | True |
| la_liga 2025 | 1520 | 380 | 0.2065 | 0.2235 | 0.1956 | True |
| bundesliga 2022 | 306 | 306 | 0.208 | 0.2258 | 0.2043 | True |
| bundesliga 2023 | 612 | 306 | 0.213 | 0.2281 | 0.1847 | True |
| bundesliga 2024 | 918 | 306 | 0.2096 | 0.2394 | 0.2016 | True |
| bundesliga 2025 | 1224 | 306 | 0.1965 | 0.2314 | 0.1907 | True |
| serie_a 2022 | 380 | 380 | 0.2091 | 0.231 | 0.1955 | True |
| serie_a 2023 | 760 | 380 | 0.203 | 0.2251 | 0.1845 | True |
| serie_a 2024 | 1140 | 380 | 0.1909 | 0.2283 | 0.1844 | True |
| serie_a 2025 | 1520 | 380 | 0.2058 | 0.2333 | 0.1962 | True |
| ligue_1 2022 | 380 | 380 | 0.219 | 0.2331 | 0.1977 | True |
| ligue_1 2023 | 760 | 306 | 0.2134 | 0.2329 | 0.2066 | True |
| ligue_1 2024 | 1066 | 306 | 0.2139 | 0.2363 | 0.2012 | True |
| ligue_1 2025 | 1372 | 306 | 0.2064 | 0.2291 | 0.2003 | True |

## Residual-Auswahl je Testsaison

| Liga | Saison | Training n | Modellanteil | Markt-Temperatur | Remis-Faktor |
|---|---:|---:|---:|---:|---:|
| premier_league | 2022 | 0 | 0.000 | 1.00 | 1.00 |
| premier_league | 2023 | 380 | 0.000 | 0.95 | 0.95 |
| premier_league | 2024 | 760 | 0.000 | 0.90 | 1.00 |
| premier_league | 2025 | 1140 | 0.000 | 0.90 | 1.05 |
| la_liga | 2022 | 0 | 0.000 | 1.00 | 1.00 |
| la_liga | 2023 | 380 | 0.000 | 0.95 | 0.90 |
| la_liga | 2024 | 760 | 0.000 | 0.90 | 1.00 |
| la_liga | 2025 | 1140 | 0.000 | 0.90 | 1.00 |
| bundesliga | 2022 | 0 | 0.000 | 1.00 | 1.00 |
| bundesliga | 2023 | 306 | 0.100 | 0.95 | 1.05 |
| bundesliga | 2024 | 612 | 0.000 | 0.90 | 1.10 |
| bundesliga | 2025 | 918 | 0.000 | 0.95 | 1.10 |
| serie_a | 2022 | 0 | 0.000 | 1.00 | 1.00 |
| serie_a | 2023 | 380 | 0.000 | 0.90 | 1.05 |
| serie_a | 2024 | 760 | 0.000 | 0.90 | 1.10 |
| serie_a | 2025 | 1140 | 0.000 | 0.90 | 1.10 |
| ligue_1 | 2022 | 0 | 0.000 | 1.00 | 1.00 |
| ligue_1 | 2023 | 380 | 0.000 | 0.95 | 1.00 |
| ligue_1 | 2024 | 686 | 0.000 | 0.95 | 1.05 |
| ligue_1 | 2025 | 992 | 0.000 | 0.95 | 0.95 |

## Gesamt (Out-of-sample)

- Modell: RPS `0.1942`, LogLoss `0.9663`, Treffer `0.5459` (n=7082)
- Naive Basisrate: RPS `0.2301`, LogLoss `1.0729`, Treffer `0.4373` (n=7082)
- Markt-Benchmark: RPS `0.1944`, LogLoss `0.967`, Treffer `0.5462` (n=7082)
- RPS-Abstand Modell minus Markt: `-0.0002`

## Kandidaten

- `decayed_dixon_coles`: Status `diagnostic`, Modell-RPS `0.2015`, Markt-RPS `0.1944`, Delta-RPS `0.0071`, Closing-Gate `False`
- `closing_residual_blend`: Status `diagnostic`, Modell-RPS `0.1942`, Markt-RPS `0.1944`, Delta-RPS `-0.0002`, Closing-Gate `False`

## Gates

- minimum_history: `True`
- beats_naive_rps: `True`
- logloss_guard_vs_naive: `True`
- all_competitions_diagnostic: `True`
- market_benchmark_available: `True`
- beats_market_rps: `True`
- closing_market_outperformance: `False`
- closing_gate_closing_coverage: `{'n': 7082, 'covered': 7082, 'rate': 1.0, 'gate': True}`
- closing_gate_aggregate_delta_rps_lt_0: `True`
- closing_gate_aggregate_delta_logloss_lt_0: `True`
- closing_gate_bootstrap_upper95_delta_rps_lt_0: `False`
- closing_gate_bootstrap_upper95_delta_logloss_lt_0: `False`
- closing_gate_league_wins_both: `2`
- closing_gate_league_wins_required: `4`
- closing_gate_league_wins_gate: `False`
- closing_gate_closing_coverage_gate: `True`
- closing_gate_closing_market_outperformance: `False`
- closing_gate_delta_rps: `-0.0002`
- closing_gate_delta_logloss: `-0.0007`
- closing_gate_upper95_delta_rps: `-0.0`
- closing_gate_upper95_delta_logloss: `-0.0`

## Pflichtdiagnosen

### aufsteiger
- `ja`: n `1146`, Delta RPS `0.0`, Delta LogLoss `-0.0006`
- `nein`: n `5936`, Delta RPS `-0.0003`, Delta LogLoss `-0.0007`
### erste_sechs_spieltage
- `ja`: n `350`, Delta RPS `-0.0002`, Delta LogLoss `-0.0016`
- `nein`: n `6732`, Delta RPS `-0.0002`, Delta LogLoss `-0.0007`
### remis
- `ja`: n `1789`, Delta RPS `0.0033`, Delta LogLoss `0.0097`
- `nein`: n `5293`, Delta RPS `-0.0014`, Delta LogLoss `-0.0042`
### staerke_diff_decile
- `1`: n `708`, Delta RPS `-0.0004`, Delta LogLoss `-0.0029`
- `10`: n `709`, Delta RPS `-0.0006`, Delta LogLoss `-0.0029`
- `2`: n `708`, Delta RPS `0.0001`, Delta LogLoss `0.0008`
- `3`: n `708`, Delta RPS `-0.0003`, Delta LogLoss `-0.0007`
- `4`: n `708`, Delta RPS `-0.0003`, Delta LogLoss `-0.0001`
- `5`: n `709`, Delta RPS `0.0`, Delta LogLoss `-0.0006`
- `6`: n `708`, Delta RPS `0.0004`, Delta LogLoss `0.0025`
- `7`: n `708`, Delta RPS `0.0002`, Delta LogLoss `0.0005`
- `8`: n `708`, Delta RPS `-0.0004`, Delta LogLoss `-0.0016`
- `9`: n `708`, Delta RPS `-0.0006`, Delta LogLoss `-0.0023`
### favoritenwahrscheinlichkeit
- `flach`: n `2399`, Delta RPS `-0.0002`, Delta LogLoss `-0.0007`
- `hoch`: n `1685`, Delta RPS `-0.0006`, Delta LogLoss `-0.0025`
- `mittel`: n `2998`, Delta RPS `0.0`, Delta LogLoss `0.0002`
### erwartete_tore
- `hoch`: n `3927`, Delta RPS `-0.0002`, Delta LogLoss `-0.001`
- `mittel`: n `3074`, Delta RPS `-0.0002`, Delta LogLoss `-0.0004`
- `niedrig`: n `81`, Delta RPS `0.0006`, Delta LogLoss `-0.0001`
### liga
- `bundesliga`: n `1224`, Delta RPS `0.0001`, Delta LogLoss `-0.0003`
- `la_liga`: n `1520`, Delta RPS `-0.0006`, Delta LogLoss `-0.0012`
- `ligue_1`: n `1298`, Delta RPS `0.0001`, Delta LogLoss `0.0003`
- `premier_league`: n `1520`, Delta RPS `0.0`, Delta LogLoss `0.0`
- `serie_a`: n `1520`, Delta RPS `-0.0004`, Delta LogLoss `-0.0022`
### saison
- `2022`: n `1826`, Delta RPS `0.0`, Delta LogLoss `0.0`
- `2023`: n `1752`, Delta RPS `-0.0004`, Delta LogLoss `-0.0011`
- `2024`: n `1752`, Delta RPS `-0.0002`, Delta LogLoss `-0.001`
- `2025`: n `1752`, Delta RPS `-0.0002`, Delta LogLoss `-0.0009`

_Das Tor-Modell nutzt Marktpreise nie als Trainingsziel. Der explizit benannte Closing-Residualkandidat verwendet den Closing-Konsens als Eingabe; seine Korrekturparameter werden ausschliesslich auf frueheren Saisons gewaehlt._

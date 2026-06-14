# Modelllogik

Stand: 2026-06-13. Quellenstatus siehe [[data_sources]].

## 1. Wahrscheinlichkeitsquellen (1X2)
1. **Markt**: Polymarket-Preise der drei Ja/Nein-Märkte, normalisiert (Summe→1).
   Plus **Bücher** (Odds-API, entvigt) und **Kalshi** als weitere Marktquellen.
2. **Modell — Bivariate-Poisson-Engine mit getrennter Angriff/Abwehr**
   (`features.attack_defense_lambdas`, ersetzt seit 13.06. den `(w/(1−w))^0.7`-Hack):
   - Elo-Differenz → erwartete **Tordifferenz** GD = (Elo₁−Elo₂)/`ELO_PER_GOAL`
     (=240, gegen den Markt kalibriert via `tests/tune_elo.py`; ±2,2 gekappt).
   - λ₁/λ₂ = (Gesamttore 2,6 ± GD)/2.
   - **Angriffs-/Abwehr-Multiplikatoren** je Team aus StatsBomb-Historie (xG bevorzugt)
     + FBref-Turnierform, stichproben-geshrunken Richtung 1,0, opponent-adjustiert,
     Multiplikator auf [0,6; 1,6] gekappt.
   - Gastgeber-Bonus +60 Elo (USA/MEX/CAN). 1X2 analytisch mit Dixon-Coles (rho).
   - **Spielort-Kontext** (`venue_client.py`): Höhe (statisch, ESPN-Stadt→Tabelle) hebt
     Tore bei >1500 m leicht (Mexiko-Stadt +3,7 %), Höhen-Nationen +6 % λ; Wetter optional
     (OpenWeather-Key). Effekte klein/gekappt, als 'estimated' gelabelt.
   - **Verletzungs-/Aufstellungs-Override** (`injuries.py`, manuell in
     `data/processed/adjustments.json`): λ-Multiplikatoren je Team/Total, gekappt
     [0,7;1,3]. ESPN-Lineups werden angezeigt, aber NICHT automatisch modelliert
     (keine Spieler-Stärkewerte → Scheinpräzision vermieden).
   - **Backtest-Lehre** ([[learnings]]): Within-Tournament-Fitting von Angriff/Abwehr
     überfittet (3 Spiele/Team) → Elo-Backbone + starke Shrinkage ist die richtige Bauweise.
3. **Whale**: score-gewichtete Yes-Exposure der Top-Holder/Top-Trades je Ausgang (heuristisch).

## 2. Whale-Scoring (defensiv)
- Kandidaten: Top-12-Holder je Sieg-/Remis-Markt + BUY-Trades > $500.
- Pro Wallet aus öffentlicher Activity (max. 500 Einträge):
  Fußball-Trades (Keyword-Filter), Volumen, Ø-Einsatz, Recency, heuristische Hit-Rate
  (= distinct Märkte mit REDEEM / distinct gehandelte Märkte).
- **Shrinkage**: Konfidenz = n_fußball / (n_fußball + 25); Hit-Rate wird Richtung 0,5 gezogen.
  → Test `test_whale_small_sample_not_overweighted` garantiert: 3/3-Glückstreffer-Wallet
  schlägt nie konsistente 60-Trade-Wallet.
- Score = geshrunkene Hit-Rate × Recency-Faktor × (0,5 + 0,5·log-Volumen-Faktor) ∈ [0,1].
- Ensemble dämpft Whale-Gewicht zusätzlich: ×min(1, n_wallets/8) × (0,5+0,5·Ø-Konfidenz).

## 3. Ensemble
- Default-Gewichte: **Markt 0,30 / Bücher 0,25 / Kalshi 0,10 / Modell 0,20 / Whale 0,15**
  (config.ENSEMBLE_WEIGHTS). „Bücher" = entvigte Buchmacher-Quoten (Pinnacle bevorzugt) via
  The Odds API; „Kalshi" = zweiter Prognosemarkt (Bid/Ask-Mitte, normalisiert). Fehlende
  Quellen werden renormalisiert.
- Modell-λ wird zusätzlich mit der **In-Turnier-Form** (FBref) multipliziert:
  Faktor n/(n+3)-gedämpft, ±25 % gekappt (Test `test_form_factor_damped_and_capped`).
- Fällt eine Quelle aus → Renormalisierung der übrigen.
- Tor-Erwartungswerte des Ensembles: gewichtetes Mittel aus markt-impliziten λ
  (Grid-Search: welche (λ₁,λ₂) reproduzieren die Markt-1X2 am besten; Roundtrip-Test ±0,15)
  und Modell-λ. Whale-Gewicht fließt dem Markt-λ zu (beide preisbasiert).

## 4. Monte Carlo
- 20.000 Läufe; pro Lauf λ aus Gamma-Verteilung (CV 12 %) → Parameterunsicherheit.
- Poisson-Tore mit **Dixon-Coles-Korrektur** (rho=-0,10, config.DIXON_COLES_RHO): hebt
  0:0/1:1 an, senkt 1:0/0:1 → korrigiert die Remis-Unterschätzung. Im analytischen 1X2
  via tau-gewichtetem Grid, im MC via Importance-Weighting (Gewicht = tau(i,j)); beide
  Wege exakt konsistent (Test `test_mc_dixon_coles_matches_analytic`). rho=0 = reine Poisson.
- Outputs: 1X2 + 5–95 %-Band (200 Resample-Blöcke), Scoreline-Matrix (0–8),
  Torverteilungen je Team, Gesamttore, O/U 0,5–4,5, Ereignisse (BTTS, Clean Sheets,
  ≥2 Tore, Siegmarge ≥2).

## 5. Validierung (tests/test_model.py)
- Poisson-1X2 summiert zu 1; stärkeres Team hat höhere Siegquote.
- Markt-λ-Solver-Roundtrip (bekannte λ → 1X2 → λ wiedergefunden).
- MC ≈ analytisch (±3 pp), Verteilungen summieren zu 1, O/U konsistent zur Torverteilung.
- Ensemble renormalisiert bei fehlender Quelle.
- Kleine Whale-Stichproben werden nicht übergewichtet.

## 6. Value Betting / Expected Value (src/model/value_betting.py)
- **Echte Buchmacherquoten** via The Odds API (`regions=eu,uk`, `markets=h2h,totals`,
  ~40 Bücher inkl. Pinnacle, Tipico, Winamax DE, William Hill, Betfair, Unibet …).
  Bestquote je Auswahl über alle Bücher (Line-Shopping) + scharfer entvigter Konsens
  (Pinnacle bevorzugt, sonst Median).
- **Konservative Untergrenze (σ-basiert, seit 13.06.)** = Anker − Z·σ, mit
  Anker = min(Modell-p, scharfer Markt-p), Z=0,8, und σ aus MC-Bandbreite (90%-Intervall
  = 3,29σ) + Markt-Modell-Diskrepanz + Grundunsicherheit 0,03. Skaliert mit echter
  Unsicherheit statt fixem pp-Abschlag. Anker am Markt, NICHT am Modell (Modell empirisch
  schwächste Quelle, [[learnings]]).
- **Liquiditäts-Gate:** Value nur bei ≥3 Büchern; **Datenqualitäts-Gate** (`data_quality.py`):
  rote Ampel unterdrückt Value-Flags, gelbe halbiert Einsätze.
- EV = p_kons × Bestquote − 1; Break-even = 1/Quote; Value nur wenn p_kons > Break-even ∧ liquide.
- Bewertet nur Märkte mit echten Live-Quoten: **1X2 und Über/Unter**. Doppelte Chance/DNB
  nur als modell-faire Referenz, BTTS/Handicap on-demand per Web ([[data_sources]] §11).
- **Staking:** Viertel-Kelly, gekappt (low 2 % / med 1,5 % / high 0,75 % je Wette) × Datenqualitäts-
  Multiplikator, Gesamtexposure 6 % gedeckelt. Kein Martingale. Tests `test_value_betting_*`.
- **Chancen-Ranking** (`opportunities` + `opportunity_portfolio`, seit 14.06.): immer befülltes
  Ranking aller Auswahlen mit positivem EV auf der **Ensemble**-Schätzung (nicht der strengen
  Grenze), sortiert nach empfohlenem Einsatz. ⭐ markiert die, die auch die konservative Schwelle
  erreichen. Dashboard-Tab „Value & Wetten". Ehrlich getrennt von der (oft leeren) Strict-Liste.
- **Ausreißer-Filter** (`odds_client._filtered_best`): Best-Line-Shopping verwirft Quoten über
  Median × 1,5 (fehlerhafte/stale Einzelquoten) — verhindert absurden EV aus Datenfehlern.
- Dashboard ist in **Tabs** organisiert: Cockpit / Spiel-Detail / Value & Wetten / Kalibrierung.

## 8. Datenqualitäts-Score (src/model/data_quality.py)
Composite 0..1 aus Elo-Status, StatsBomb-Verfügbarkeit, Form-Spielen, Liquidität (n Bücher),
Markt-Dispersion (Einigkeit Markt/Bücher/Kalshi). Ampel green≥0,70 / amber≥0,45 / red.
Gate: green ×1,0, amber ×0,5, red ×0 Einsatz. Sichtbar als Ampel im Dashboard-Cockpit.

## 7. Closing-Loop-Kennzahlen (src/model/calibration.py)
- Je Quelle: **Brier**, **Log Loss** (−ln p_actual; bestraft Selbstsicherheit stärker),
  **Hit-Rate** (argmax == Ergebnis). Nur Pre-Kickoff-Snapshots (Leakage-Schutz).
- **Referenz-Wett-Policy:** 1 Einheit flat auf Ensemble-Favorit @ beste 1X2-Quote → **ROI**.
- **CLV** (Closing Line Value): Opening- vs. Closing-Snapshot. `model_beat_close` = bewegte
  sich der Markt in Richtung unserer Opening-Modell-Lehne; `clv_odds` = Opening-/Closing-Quote−1.
  Wird erst aussagekräftig, wenn Snapshots Tage auseinanderliegen (Daily-Run im Voraus).
- **model_version** (config.MODEL_VERSION, Hash aus Gewichten/rho/Baseline/cv) in jedem
  Snapshot → Kalibrierungs-Drift einer Modelländerung zuordenbar.

## Bekannte Annahmen / Schwächen
- Elo wird live von eloratings.net geladen (täglich aktuell); Markt korrigiert Restfehler im Blend.
- Aufstellungen/Verletzungen nur als manuelles Override (`adjustments.json`) — keine automatische
  Spieler-Stärkemodellierung (keine freie Datenquelle). Wetter/Höhe als kleiner, gelabelter Faktor.
- **K.o.-Runden:** Das Modell und die Polymarket-Match-Märkte prognostizieren das **90-Minuten-1X2**.
  Verlängerung/Elfmeterschießen (Weiterkommen) werden NICHT modelliert. In der K.o.-Phase ist die
  1X2-Prognose also das Ergebnis nach regulärer Spielzeit, nicht „wer kommt weiter" — bewusste Grenze.
- Ruhetage/Reisen nicht modelliert (Gruppenphase: für alle ähnlich, vertretbar).

# Datenquellen — Status, Grenzen, Labels

Stand: 2026-06-12. Labels im Dashboard: `live`, `cached`, `historical`, `estimated`, `unavailable`.

## 1. Polymarket (live)
- **Gamma API** `https://gamma-api.polymarket.com` — Events/Märkte/Preise, öffentlich, kein Key.
  - Match-Events: Slug `fifwc-<code1>-<code2>-<YYYY-MM-DD>`, Tag **`fifa-world-cup`** (nicht `world-cup`!).
  - Pro Spiel 3 Ja/Nein-Märkte (Heimsieg / Auswärtssieg / Remis) → 1X2 durch Normalisierung (Rohsumme ≈ 0,99–1,01).
  - Team-Codes weichen teils von FIFA ab: Schweiz = `che`.
- **Data API** `https://data-api.polymarket.com` — `/trades`, `/holders`, `/activity?user=` öffentlich.
- Doku: https://docs.polymarket.com/market-data/overview
- **Grenze:** Nur 1X2 pro Spiel; keine öffentlichen Over/Under- oder Correct-Score-Märkte pro Gruppenspiel
  gefunden (12.06.2026). Scorelines/Totals kommen daher aus markt-impliziten λ + Modell.

## 2. Polymarket Whale-Daten (estimated / heuristic)
**Dokumentierte Einschränkung:** Polymarket bietet **keine** saubere öffentliche
Pro-Nutzer-Erfolgshistorie (kein P&L pro aufgelöstem Markt, kein Brier Score, kein CLV).
Öffentlich: Top-Holder pro Markt, Trades pro Markt, Activity pro Wallet (TRADE/REDEEM).
- Ersatzlogik (siehe [[model_logic]]): REDEEM-Einträge ≈ gewonnene Positionen → heuristische
  Hit-Rate; Volumen, Recency, Fußball-Anteil, Shrinkage n/(n+25).
- Alle Wallet-Scores tragen `score_basis: "heuristic"` — **nicht audit-fest**.
- Echte CLV-/Brier-Berechnung bräuchte vollständige Preis- und Resolutionshistorie pro Markt
  (theoretisch über CLOB-Preishistorie möglich — offener Punkt).

## 3. StatsBomb (historical / api)
- **Open Data** (öffentlich): neueste Herren-WM = **2022**. Für die WM 2026 also nur
  historische Priors (Tore/Gegentore pro Spiel, WM 2018+2022, 40 Teams).
  Viele 2026-Teilnehmer (Kanada, Bosnien, Haiti, …) fehlen → Status `unavailable`, Modell nutzt nur Elo.
- **API-Modus**: aktiviert sich automatisch, wenn `SB_USERNAME`/`SB_PASSWORD` als
  Umgebungsvariablen gesetzt sind (kostenpflichtiger Hudl/StatsBomb-Zugang). Sauber getrennt
  in `statsbomb_client.py` (`data_mode()`); Label wechselt dann auf `live`.
- Event-Level-Daten: lokaler **Sparse-Clone** unter `C:\Users\marin\statsbomb-open-data`
  (`--depth 1 --filter=blob:none` + sparse-checkout nur auf competitions, matches/43 und die
  128 WM-Event-Dateien → 393 MB statt >20 GB; voller Shallow-Clone war zuvor abgebrochen).
  Außerhalb OneDrive; Override via `STATSBOMB_OPEN_DATA_DIR`. Weitere Spiele nachladen:
  `git sparse-checkout add /data/events/<match_id>.json`. Daraus wird xG für/gegen
  pro WM-Spiel (2018+2022) aggregiert und permanent gecacht (`data/raw/statsbomb_local_xg.json`
  — historische Daten ändern sich nicht). Pass-/360-Daten liegen im Klon, werden aber noch
  nicht modelliert.
- Doku: https://github.com/statsbomb/statsbombpy , https://github.com/statsbomb/open-data

## 4. Elo-Ratings (estimated)
- Statischer Snapshot in `src/config.py` (`ELO_RATINGS`), angelehnt an eloratings.net,
  Stand ~2026-06-01, **geschätzt/gerundet**. Fallback 1650 für fehlende Teams.
- Gastgeber-Bonus +60 Elo (USA/Mexiko/Kanada). Baseline 2,6 Tore/Spiel (WM-Gruppenphasen-Schnitt).
- **Pflegehinweis:** vor K.o.-Runde manuell aktualisieren.

## 5. eloratings.net (live, seit 2026-06-12)
- TSV-Endpunkte ohne Key: `World.tsv` (Code+Rating) + `en.teams.tsv` (Code→Name), 244 Teams.
- Cache 20 h (`data/raw/elo_ratings.json`). Fällt der Abruf aus → statischer Snapshot
  in `config.py` mit Label `estimated` (Test `test_elo_fallback_static`).

## 6. The Odds API (Buchmacher-Quoten; braucht Key)
- `the-odds-api.com`, Free Tier ~500 Requests/Monat. Key: Umgebungsvariable `ODDS_API_KEY`
  **oder** `api_keys.json` im Projektroot (`{"odds_api": "..."}`).
- Sport-Key `soccer_fifa_world_cup`, 3-Weg-H2H. **Pinnacle bevorzugt** (schärfster Markt),
  sonst Median über alle Bücher. Proportionales De-Vigging (Overround raus).
- 1 Request pro Daily Run (alle Spiele in einer Antwort), Cache 6 h. Ohne Key: `unavailable`,
  Ensemble renormalisiert ohne `books`.

## 7. football-data.org (offizielle Ergebnisse; braucht Key)
- Free Tier, Key: `FOOTBALL_DATA_API_KEY` oder `api_keys.json` (`{"football_data": "..."}`).
- Liefert beendete WM-Spiele inkl. `kickoff_utc` → **Kalibrierungs-Tracking**
  (`src/model/calibration.py`): Multiclass-Brier je Quelle (market/books/model/whale/ensemble).
  **Leakage-Schutz** (Fix 2026-06-13): Es zählt der letzte Snapshot **vor Anpfiff** —
  Post-Kickoff-Snapshots enthalten konvergierte Marktpreise und werden verworfen;
  Spiele ohne Pre-Kickoff-Stand werden gar nicht gewertet. Snapshots werden deshalb
  **pro Lauf** gespeichert (`data/snapshots/<datum>_<uhrzeit>.json`), nicht pro Tag.
  Keys liegen in `api_keys.json` (per `.gitignore` vom Repo ausgeschlossen).

## 8. Kalshi (live, kein Key; seit 2026-06-13)
- `api.elections.kalshi.com/trade-api/v2`, Serie **KXWCGAME** (3 Märkte/Spiel: Team1/Team2/TIE).
- **Stolperfallen:** KEIN `status=open`-Filter (spielnahe Events wechseln auf `active` und
  fielen sonst raus); Preise stehen in `*_dollars`-String-Feldern (0..1), die alten
  Integer-Cent-Felder sind leer. Bid/Ask-Mitte bevorzugt, sonst `last_price_dollars`.
- 5. Ensemble-Quelle (Gewicht 0,10). Es existieren auch `KXWCSCORE` (Correct Score),
  `KXWCTOTALGOAL`, `KXWCBTTS` → Ausbaustufe.

## 9. ESPN (live, inoffiziell, kein Key; seit 2026-06-13)
- `site.api.espn.com/.../soccer/fifa.world/scoreboard?dates=YYYYMMDD-YYYYMMDD`:
  Status (pre/in/post), Anstoß UTC, Zwischenstand. `summary?event=<id>`: Aufstellungen
  (~1 h vor Anpfiff). Nur Anzeige (Status-Badge, Lineup-Panel), fließt nicht ins Modell.
- Inoffiziell → defensiv, Label `live (unofficial)`. FotMob-API war die erste Wahl,
  liefert aber 404 (Auth eingeführt).

## 10. FBref-Turnierform via soccerdata (live; seit 2026-06-13)
- `soccerdata.FBref('INT-World Cup', '2026').read_schedule()` — umgeht Cloudflare per
  Headless-Chrome (~30–60 s) → Cache 20 h (`data/raw/fbref_form.json`), Fehler nie fatal.
- In-Turnier-Form: Tore für/gegen pro gespieltem Spiel; **xG-Spalten sind für die WM 2026
  noch leer** → tor-basiert mit automatischem xG-Upgrade, sobald FBref liefert.
- Fließt als gedämpfter Multiplikator ins Modell-λ: Gewicht n/(n+3), Kappung ±25 %.

## 11. Web-Odds auf Zuruf (Zusatzmärkte, best-effort; eingerichtet 13.06.)
- Für Märkte ohne Odds-API-Abdeckung (BTTS, Handicap, Doppelte Chance, DNB) macht Claude
  **auf Anfrage** eine Web-Recherche (WebSearch/WebFetch). **Getestet 13.06.:** direktes
  Fetchen von Buchmachern + Aggregatoren (bet365, Tipico, oddspedia, sportytrader) scheitert
  an 403/Bot-Schutz/JS. WebSearch liefert Snippet-Quoten (oft US-Books, amerik. Format,
  teils Eröffnungslinien) → **ungeprüft, einzelne Quelle, klar so labeln**.
- Für 1X2 + O/U ist die Odds-API (40 Bücher) strikt besser — Line-Shopping schlug die
  Web-/US-Quoten im Test (Brasilien-Sieg: API-Best 1,72 vs. bet365 1,57).
- **Gold-Standard für Zusatzmärkte bleibt ein Screenshot/Link vom Nutzer.** Kein
  Dauer-Scraper in der Pipeline (zu fragil).

## 12. Spielort/Höhe/Wetter (venue_client.py; seit 13.06.)
- Höhe: **statische** Stadt→(Höhe, lat, lon)-Tabelle für WC-2026-Orte, gematcht über
  ESPN-`venue.address.city` (ESPN-Client erfasst jetzt venue+city). Kein Key.
- Wetter: **OpenWeather** (`api_keys.json` → `openweather` ODER `OPENWEATHER_API_KEY`),
  optional. Ohne Key: Wetter `unavailable`, Höhe läuft trotzdem.
- Effekte klein/gekappt (Tor-Multiplikator [0,9;1,08]) und als `estimated` gelabelt.

## 13. Verletzungs-/Aufstellungs-Override (injuries.py; seit 13.06.)
- Manuell in `data/processed/adjustments.json` (Key = Spiel-Slug), λ-Multiplikatoren
  je Team/Total. ESPN-Lineups (~1h vor Anpfiff) werden nur angezeigt, nicht auto-modelliert.
- `_example_format`-Eintrag in der Datei dokumentiert das Format (wird ignoriert).

## 14. Quotenverlauf (/api/odds-history; seit 13.06.)
- Liest alle `data/snapshots/*.json`, gibt 1X2-Bestquoten + Markt/Ensemble-Probs als
  Zeitreihe je Slug → Dashboard-Chart. Wird mit Tage-im-Voraus-Läufen aussagekräftig.

## Nicht verfügbar / bewusst weggelassen
- **Schiedsrichter**: keine saubere freie Datenquelle, Refs spät angesetzt → bewusst nicht modelliert.
- Karten, Ecken, Spieler-Props: keine belastbare öffentliche Quelle angebunden → Dashboard
  zeigt nur simulationsableitbare Ereignisse (BTTS, Clean Sheet, Margen).
- Verletzungen/Aufstellungen: keine strukturierte freie Quelle; nicht modelliert (dokumentiert).

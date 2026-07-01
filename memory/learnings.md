# Closing-Loop-Learnings (Hermes)

Laufendes Protokoll: Prognose vs. Realität, abgeleitete Anpassungen. Nicht aus
Einzelspielen überlernen — Regeländerungen erst bei wiederkehrenden Signalen (n≥5).

## Spieltag 1–2 (11.–12.06.2026), Stand 13.06.

**Datenlage:** Nur Kanada–Bosnien hatte eine echte Vorab-Prognose (Projektstart 12.06.).
Mexiko–Südafrika und Korea–Tschechien sind Retrodiktionen (heutiges Modell, ohne
Turnierform; Elo minimal nachspiel-kontaminiert) — nur als Plausibilitätscheck werten.

| Spiel | Ergebnis | Modell-Tendenz | Brier (Modell) | Brier (Markt) | Brier (Ensemble) | Brier (Whale) |
|---|---|---|---|---|---|---|
| Mexiko–Südafrika | 2:0 | richtig (74 % MEX) | 0.112 (retro) | – | – | – |
| Korea–Tschechien | 2:1 | richtig (42 % KOR) | 0.506 (retro) | – | – | – |
| Kanada–Bosnien | 1:1 | falsch (59 % CAN) | 1.082 | **0.847** | 0.992 | 1.744 |

(Gleichverteilungs-Benchmark: 0.667. Bei einem Remis "verlieren" alle Favoriten-Quellen — normal.)

## Erkenntnisse (belegt)
1. **Markt < Ensemble < Modell < Whale** (Brier, Kanada-Spiel): Der Markt war am
   vorsichtigsten beim Remis (28 % vs. Modell 21 %) und lag damit am besten.
2. **Whale-Signal war die schlechteste Quelle** (86 % Kanada): Top-Holder waren long
   Kanada und verloren. Bestätigt die defensive Gewichtung (0,15, konfidenz-gedämpft).
   Erst nach ≥5 aufgelösten Spielen über Gewichtssenkung entscheiden.
3. **Kanada dominierte statistisch** (13:8 Schüsse, 61 % Ballbesitz, 9:4 Ecken, Bosnien
   20 Fouls) — die Favoriteneinschätzung war prozessual nicht absurd; Chancenverwertung
   fehlte. Einordnung: erheblicher Varianzanteil, kein reiner Modellfehler.
4. **Elo-Basis funktioniert** in beiden Retro-Spielen (Richtung korrekt, Mexiko fast perfekt).

## Hypothesen (plausibel, noch nicht belegt)
- Unabhängige Poisson **unterschätzt Remis** bei moderaten Favoriten → Dixon-Coles-
  Korrektur ist Priorität 1 (struktureller Standard-Fix, kein Overfitting auf 1 Spiel).
- Gastgeber-Bonus +60 ggf. zu hoch für Co-Gastgeber Kanada (Modell 66 % vs. Markt 54 %).
  Beobachten bei den nächsten CAN/MEX/USA-Spielen, noch nicht ändern.
- Tor-Baseline 2,6: bisher 2/3/2 Tore (Ø 2,33) — Stichprobe zu klein, keine Änderung.

## Prozess-Fixes (bereits umgesetzt)
- Snapshots pro Lauf statt pro Tag (Pre-Kickoff-Stände bleiben erhalten).
- Kalibrierung wertet nur Prognosen VOR Anpfiff (Leakage-Schutz).
- Datums-Matching ±1 Tag (Slug = US-Ostküste, football-data.org = UTC; Fix 13.06.).
- Ab jetzt entsteht für jedes Spiel automatisch eine saubere Closing-Line-Prognose →
  dieses Protokoll füllt sich aus [[data_sources|football-data.org]]-Auflösungen.

## Update 13.06. — Dixon-Coles umgesetzt + erste echte Pre-Kickoff-Auflösung

**Dixon-Coles (rho=-0,10)** in `poisson_1x2` UND Monte Carlo (per Importance-Weighting)
eingebaut. Effekt: Remis +2,0–2,6 pp (Kanada-Fall 20,9 %→22,9 %, Richtung Markt 27,6 %).
Tests 13/13 grün, MC↔Analytik unter DC konsistent (±3 pp). Begründung war strukturell
(bekannte Poisson-Schwäche), nicht aus dem Kanada-Spiel gelernt → kein Overfitting.

**USA–Paraguay 4:1** (erste saubere Pre-Kickoff-Auflösung, Prognose 22:33 UTC vor 01:00-Anpfiff):

| Quelle | Prognose USA | Brier | Rang |
|---|---|---|---|
| Whale | ~96 % | **0,001** | 1 |
| Ensemble | 48 % | 0,400 | 2 |
| Kalshi | 47 % | 0,419 | 3 |
| Markt | 47 % | 0,427 | 4 |
| Bücher | 46 % | 0,444 | 5 |
| Modell | ~25 % | 0,858 | 6 |

**Zentrales Learning — Whale ist hochvariant, nicht systematisch gut/schlecht:**
- Kanada–Bosnien: Whale Brier **1,744** (schlechteste Quelle, lag 86 % auf Kanada → Remis).
- USA–Paraguay: Whale Brier **0,001** (beste Quelle, lag ~96 % auf USA → 4:1).
- Über beide gemittelt ~0,87 ≈ Gleichverteilung. Das bestätigt die defensive Dämpfung
  EINDRÜCKLICH: Whale darf nie hoch gewichtet werden, weil es zwischen genial und
  wertlos schwankt. KEINE Gewichtserhöhung, auch wenn USA spektakulär aussah.

**Modell-Schwäche bestätigt:** Bei USA–Paraguay unterschätzte das Elo-Modell den
Gastgeber USA deutlich (25 % vs. Realität klarer Sieg). Gegensatz zu Kanada, wo der
Gastgeber-Bonus eher zu HOCH war. → Gastgeber-Effekt ist team-/gegnerabhängig, nicht
konstant +60. Weiter beobachten (USA, Mexiko, Kanada), noch nicht ändern (n=2).

**Offen für die nächsten Auflösungen** (heute Nacht: Katar–Schweiz, Brasilien–Marokko,
Haiti–Schottland — alle mit sauberen Pre-Kickoff-Ständen): Prüfen, ob Markt/Bücher/Kalshi
konsistent unter ~0,30 Brier landen (gut kalibriert) und ob das Ensemble sie schlägt.

## Update 13.06. (2) — Minimalversion CLV + erweiterte Kennzahlen umgesetzt
Nach Quant-Review umgesetzt: **Log Loss, Hit-Rate, ROI (Referenz-Policy: 1 Einheit auf
Ensemble-Favorit @ Bestquote), CLV** (Opening- vs. Closing-Snapshot) + **model_version**
(m-491f305c). Alles in `calibration.py`, sichtbar in `_closing_loop.md` + Dashboard.
- LogLoss bestätigt Brier-Ranking schärfer: Modell 1,37 (> Zufall 1,099, also überzeugt-falsch),
  Whale 0,028, Ensemble 0,726. Hit-Rate: alle außer Modell trafen den Favoriten (USA).
- ROI/CLV-Quoten noch n=0, weil alte USA-Paraguay-Snapshots keine `odds_1x2` hatten —
  füllt sich ab den Spielen ab 13.06. abends automatisch.
- **CLV wird erst aussagekräftig, wenn der 09:00-Job Tage im Voraus läuft** (aktuell
  Snapshots ~30 min eng → Marktbewegung ≈ Rauschen). Nächster echter Hebel: Backtest-Harness.

## Update 13.06. (3) — Roadmap-Rest umgesetzt + Backtest-Lehren
Umgesetzt: Datenqualitäts-Score+Gate, **Bivariate-Poisson-Engine** (getrennte Angriff/Abwehr,
ersetzt `(w/(1-w))^0.7`), Backtest-Harness, **σ-basierte EV-Grenze**+Liquiditäts-Gate,
Dashboard-Cockpit+Value-Ranking+CSV. 19 Tests grün.

**Backtest-Befund (wichtig, ehrlich):** Reines Within-Tournament-Fitting von Angriff/Abwehr
(`src/model/backtest.py`, 128 WM-Spiele 18/22, 5-fold-CV) **schlägt die Basisraten NICHT**
(LogLoss 1,70 vs. 1,06) — bei nur ~3 Spielen/Team überfittet der Fit massiv. Lehre:
**Elo-Backbone (gepoolte Historie) + stark geshrunkene Angriff/Abwehr ist die richtige
Bauweise** — genau was die Produktions-Engine macht. rho=0 war im Backtest minimal best,
aber im Rauschen; rho=−0,10 bleibt als Struktur-Prior (Literatur, große Datensätze) mit
diesem Caveat. ELO_PER_GOAL ist historisch NICHT backtestbar (kein altes Elo).

**Engine-Kalibrierung:** Neue Engine war zunächst überkonfident (Modell-vs-Markt-Fehler 10,2 %);
`ELO_PER_GOAL=240` (gegen Markt getunt) senkt ihn auf **5,6 %**. Markt bleibt Kalibrier-Proxy.

**Offene „später"-Punkte** (brauchen Daten/Quellen, die wir nicht haben → bewusst nicht erzwungen):
Reliability-Diagramm (n=1 zu wenig), Quotenverlauf-Charts (Snapshots noch eng), xG-Form
(FBref-xG für WM noch leer), Aufstellung/Verletzung ins Modell, Wetter/Höhe/Schiri (neue APIs,
erst nach Zustimmung), korrelationsbewusstes Staking.

## 2026-06-15
- [Beobachtung] Kalshi und Ensemble führen nach n=8 nahezu gleich: Kalshi Brier/RPS/LogLoss 0.6502/0.1928/1.0446, Ensemble 0.6502/0.1930/1.0622; Markt liegt knapp dahinter bei 0.6566/0.1953/1.0568.
- [Beobachtung] Modell bleibt schwach kalibriert: Brier 0.7247, RPS 0.2253, LogLoss 1.1436, Treffer 3/8; Whale ist mit n=4 und Brier-Spannweite 0.0014-1.4648 zu variant fuer hoehere Gewichtung.
- [Hypothese] Der kleine Ensemble-Vorsprung kommt eher aus punktueller Diversifikation als aus robuster Modellueberlegenheit; Markt/Buecher/Kalshi sind stark korreliert, und historische StatsBomb plus 0-Spiele-Form reichen noch nicht fuer verlaessliche Favoriten-Korrekturen.
- [Aktion] `weights_suggestion` nur notieren, nicht anwenden: vorgeschlagen Markt 0.276, Buecher 0.244, Kalshi 0.147, Modell 0.198, Whale 0.135 bei status=data-driven/n=8; abwarten bis n>=15 und Stabilitaet ueber mehrere Tage pruefen.

## 2026-06-16
- [Beobachtung] Nach n=12 fuehrt Kalshi den rollierenden Score: Brier/RPS/LogLoss 0.7376/0.2047/1.1539; Markt und Buecher liegen bei Brier 0.7431, Ensemble faellt auf 0.7729 und Modell auf 0.8317.
- [Beobachtung] Die drei neuen aufgeloesten Spiele vom 15.06. waren Remis; die Ensemble-Favoriten verfehlten alle drei, Referenz-Policy ROI steht bei -57.9 % ueber 11 Bets, CLV bleibt mit +0.93 % bei n=10 nur schwach positiv.
- [Hypothese] Das aktuelle Problem ist Draw-/Favoriten-Kalibrierung plus Whale-Varianz, nicht fehlende Live-Quellen: Elo/Buecher/Kalshi/ESPN live, StatsBomb historisch, Turnierform 0 Spiele; Whale verschlechtert die letzten drei Remis mit Brier 1.892-1.996.
- [Aktion] Keine Gewichte automatisch aendern: `weights_suggestion` data-driven/n=12 empfiehlt Markt 0.201, Buecher 0.202, Kalshi 0.205, Modell 0.303, Whale 0.088; abwarten bis n>=15 und stabile Mehrtages-Tendenz, Whale keinesfalls erhoehen.

## 2026-06-17
- [Beobachtung] Vier neue aufgeloeste Favoritensiege trafen die Ensemble-Headline-Picks: Tages-Brier/RPS/LogLoss fuer diese vier Spiele Ensemble 0.1204/0.0445/0.3248 vs. Markt 0.1280/0.0472/0.3354; Referenz-Policy +1.67 Einheiten, ROI rollierend -57.9% -> -31.3%.
- [Beobachtung] Rollierend fuehrt weiter Kalshi bei n=16: Brier/RPS/LogLoss 0.5854/0.1654/0.9495; Ensemble bleibt trotz gutem Tag hinter Markt/Kalshi mit 0.6098/0.1733/0.9907, Modell 0.6792/0.2072/1.0834, Whale 0.8013/0.2226/2.0079 bei n=11.
- [Hypothese] Der heutige Sprung ist ein Favoriten-Cluster und keine robuste Entwarnung: Whale war in den vier neuen Spielen stark, bleibt aber wegen frueherer Remis-Fehler hochvariant; das Modell trifft Favoriten, ist aber weniger scharf als Markt/Whale bei Norwegen und Oesterreich.
- [Aktion] `weights_suggestion` data-driven/n=16 nur notieren, nicht anwenden: empfohlen Markt 0.195, Buecher 0.195, Kalshi 0.198, Modell 0.307, Whale 0.106; abwarten bis n>=20 und Stabilitaet ueber mehrere Tage, besonders Ensemble-vs.-Markt und Modell-Kalibrierung.

## 2026-06-18

- [Beobachtung] Kalshi fuehrt rollierend bei n=19 mit Brier/RPS/LogLoss 0.541/0.159/0.893; Ensemble bleibt schlechter bei 0.562/0.166/0.928.
- [Beobachtung] Die drei neuen Aufloesungen vom 17.06.2026 trafen alle Ensemble-Picks; Tages-Brier: Whale 0.117, Kalshi 0.305, Ensemble 0.310, Modell 0.522.
- [Hypothese] Die juengsten Favoriten-Treffer verbessern die Tagesbilanz, loesen aber die strukturelle Ensemble-Schwaeche nicht, weil Modell-Brier 0.654 und Whale-LogLoss 1.640 weiter zu hoch sind.
- [Aktion] `weights_suggestion` data-driven/n=19 nur notieren, nicht anwenden; abwarten bis mindestens n>=20-25 und stabile Mehrtages-Tendenz, Parameter-Tuning prior/n=18 unveraendert lassen.

## 2026-06-19

- [Beobachtung] Rollierend fuehrt Kalshi bei n=23 mit Brier/RPS/LogLoss 0.516/0.150/0.862; Ensemble bleibt mit 0.536/0.157/0.892 schlechter als Polymarkt 0.520/0.151/0.866.
- [Beobachtung] Die 4 neuen Aufloesungen liefern Tages-Brier Modell 0.383, Markt 0.397, Kalshi 0.399, Ensemble 0.410, Whale 0.630; Referenz-ROI steigt von -11.7% auf -7.8%, CLV faellt von -0.97% auf -1.32%.
- [Hypothese] Der heutige Modell-Vorsprung ist noch kein stabiles Signal, weil Whale-Remisfehler und die rollierende Ensemble-Unterperformance gegen Markt/Kalshi weiter dominieren.
- [Aktion] `weights_suggestion` data-driven/n=23 nur notieren: 0.189/0.182/0.191/0.318/0.120 fuer Polymarkt/Buchmacher/Kalshi/Modell/Whale; keine Auto-Uebernahme, bis n>=30 und Ensemble-vs.-Markt mehrere Tage stabil positiv ist.

## 2026-06-22

- [Beobachtung] Kalshi fuehrt rollierend bei n=34 mit Brier/RPS/LogLoss 0.495/0.147/0.833; Ensemble liegt bei 0.505/0.151/0.849 und damit +0.008 Brier hinter Polymarkt.
- [Beobachtung] Referenz-Policy bleibt negativ: 32 Wetten, 62% Trefferquote, ROI -1.3%, CLV -0.49%; Whale bleibt hochvariant mit Brier-Spannweite 0.000-1.996 ueber 29 Spiele.
- [Hypothese] Das vorgeschlagene hoehere Modellgewicht 0.341 ist noch nicht robust genug, weil die Modellkalibrierung Brier 0.558 hat und das Ensemble den Markt weiterhin nicht schlaegt.
- [Aktion] `weights_suggestion` nur notieren: 0.177/0.174/0.178/0.341/0.130 fuer Polymarkt/Buchmacher/Kalshi/Modell/Whale; keine Auto-Uebernahme bis Ensemble-vs.-Markt mehrere Tage positiv ist.

## 2026-06-25

- [Beobachtung] Rollierend fuehrt Kalshi bei n=47 mit Brier/RPS/LogLoss 0.461/0.144/0.789; Ensemble liegt mit 0.468/0.148/0.801 weiter hinter Polymarkt 0.464/0.145/0.793.
- [Beobachtung] Seit 24.06. kamen 5 Aufloesungen dazu: Ensemble 4/5 richtig, Tages-Brier ca. 0.349; groesster Fehler RSA-Korea mit Ensemble-Brier 1.203 und Whale-Brier 1.945.
- [Hypothese] Das Ensemble profitiert kurzfristig von Favoritenclustern, aber Modell- und Whale-Varianz verhindern noch robuste Markt-Outperformance; CLV +0.01% bei n=40 stuetzt keinen klaren Preis-Edge.
- [Aktion] `weights_suggestion` data-driven/n=47 nur notieren: 0.168/0.163/0.169/0.343/0.157 fuer Polymarkt/Buchmacher/Kalshi/Modell/Whale; keine Auto-Uebernahme bis Ensemble-vs.-Markt mehrtaegig positiv ist.

## 2026-06-27

- [Beobachtung] Rollierend fuehrt Kalshi bei n=58 mit Brier/RPS/LogLoss 0.455/0.144/0.779; Polymarkt liegt praktisch gleichauf bei 0.456/0.145/0.782, Ensemble bleibt bei 0.462/0.148/0.792 dahinter.
- [Beobachtung] Seit 25.06. kamen 11 Aufloesungen hinzu; Tages-Brier ca. Buchmacher 0.419, Polymarkt 0.424, Kalshi 0.426, Ensemble 0.437, Modell 0.494, Whale 0.612.
- [Hypothese] Die ROI-Verbesserung auf +11.0% kommt eher aus Favoriten-/Ergebnisclustern als aus robuster Wahrscheinlichkeitskalibrierung, weil das Ensemble den Markt bei Brier/RPS/LogLoss weiter nicht schlaegt.
- [Aktion] `weights_suggestion` data-driven/n=58 nur notieren: 0.169/0.166/0.170/0.355/0.141 fuer Polymarkt/Buchmacher/Kalshi/Modell/Whale; keine Auto-Uebernahme bis Ensemble-vs.-Markt mehrtaegig positiv ist und Modell-Brier klar unter Marktblock-Niveau faellt.

## 2026-06-28

- [Beobachtung] Kalshi fuehrt rollierend bei n=63 mit Brier/RPS/LogLoss 0.4458/0.1389/0.7672; Polymarkt liegt mit 0.4470/0.1391/0.7696 praktisch gleichauf, Ensemble bleibt bei 0.4518/0.1422/0.7778 dahinter.
- [Beobachtung] Die 5 neuen Aufloesungen liefern Ensemble 4/5 Treffer und Tages-Brier ca. 0.329; Referenz-Policy steigt auf 60 Wetten, 70.0% Trefferquote, ROI +12.55%, CLV +0.69% bei beat-close-rate 47.06%.
- [Hypothese] Die kurzfristige ROI- und Tages-Brier-Verbesserung ist noch kein stabiler Preis-Edge, weil das Ensemble rollierend Markt/Kalshi nicht schlaegt und CLV mit 47.06% beat-close-rate keinen klaren Marktbewegungsbeleg liefert.
- [Aktion] `weights_suggestion` data-driven/n=63 nur notieren: 0.168/0.165/0.168/0.359/0.140 fuer Polymarkt/Buchmacher/Kalshi/Modell/Whale; keine Auto-Uebernahme bis Ensemble-vs.-Markt mehrere Tage positiv bleibt und Modell-Brier klar unter Marktblock-Niveau faellt.

## 2026-06-30

- [Beobachtung] Kalshi fuehrt rollierend bei n=63 mit Brier/RPS/LogLoss 0.446/0.139/0.767; Ensemble liegt bei n=67 mit 0.465/0.152/0.801 hinter Polymarkt 0.462/0.150/0.797.
- [Beobachtung] Die 4 neuen Aufloesungen liefern Tages-Brier Modell 0.578, Ensemble 0.671, Buchmacher 0.688, Polymarkt 0.696, Whale 0.873; ROI faellt von +12.55% auf +10.9%, CLV von +0.69% auf +0.63%.
- [Hypothese] Das erhoehte Modellgewicht wird durch den Mini-Tag gestuetzt, ist aber noch nicht robust, weil das Ensemble rollierend den Marktblock nicht schlaegt und Whale-Upsets weiter grosse Fehler erzeugen.
- [Aktion] `weights_suggestion` data-driven/n=67 nur notieren: 0.165/0.163/0.175/0.370/0.128 fuer Polymarkt/Buchmacher/Kalshi/Modell/Whale; keine Auto-Uebernahme bis Ensemble-vs.-Markt mehrere Tage positiv ist und CLV klar >1% bei n>=60 liegt.

## 2026-07-01

- [Beobachtung] Kalshi fuehrt rollierend bei n=63 mit Brier/RPS/LogLoss 0.446/0.139/0.767; Ensemble liegt bei n=70 mit 0.457/0.150/0.790 nicht vor Polymarkt 0.457/0.149/0.790.
- [Beobachtung] Die 3 neuen Aufloesungen liefern Tages-Brier ca. Whale 0.157, Ensemble 0.281, Modell 0.294, Polymarkt 0.340, Buchmacher 0.346; ROI steigt auf +14.7%, CLV bleibt nur +0.60% bei n=54.
- [Hypothese] Das Modellgewicht 0.370 ist als Richtung plausibel, aber noch nicht uebernahmefaehig, weil Modell rollierend mit Brier 0.497 schlechter als Markt/Kalshi bleibt und Ensemble den Markt probabilistisch nicht schlaegt.
- [Aktion] `weights_suggestion` data-driven/n=70 nur notieren: 0.163/0.161/0.170/0.370/0.137 fuer Polymarkt/Buchmacher/Kalshi/Modell/Whale; keine Auto-Uebernahme bis Ensemble-vs.-Markt mehrtaegig positiv ist und CLV >1.0% bei n>=60 liegt.

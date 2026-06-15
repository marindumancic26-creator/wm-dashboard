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

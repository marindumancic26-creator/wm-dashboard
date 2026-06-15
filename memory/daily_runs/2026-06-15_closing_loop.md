# Closing-Loop-Report — 2026-06-15

Stand: 2026-06-15T08:42:17 · automatisch erzeugt (deterministisch, ohne Claude).
Narrative Hermes-Analyse: auf Anfrage.

## Trefferbilanz (Headline-Prognose)

**✅ 4 richtig · ❌ 4 falsch** — Trefferquote 50% über n=8 Spiele (Ensemble).

## Aufgelöste Spiele (8)

### fifwc-bra-mar-2026-06-13 — Ergebnis 1:1 (draw)
Prognose-Stand: 2026-06-13T21:02:02

| Quelle | Brier |
|---|---|
| Polymarkt | 0.923 |
| Buchmacher | 0.909 ✅ |
| Kalshi | 0.930 |
| Modell | 1.090 ❌ |
| Ensemble | 0.957 |

### fifwc-hai-sco-2026-06-13 — Ergebnis 0:1 (team2_win)
Prognose-Stand: 2026-06-14T01:17:17

| Quelle | Brier |
|---|---|
| Polymarkt | 0.194 |
| Buchmacher | 0.205 |
| Kalshi | 0.205 |
| Modell | 0.251 ❌ |
| Whale | 0.008 ✅ |
| Ensemble | 0.169 |

### fifwc-qat-che-2026-06-13 — Ergebnis 1:1 (draw)
Prognose-Stand: 2026-06-13T20:44:24

| Quelle | Brier |
|---|---|
| Polymarkt | 1.441 ❌ |
| Buchmacher | 1.400 |
| Kalshi | 1.410 |
| Modell | 1.374 ✅ |
| Whale | 1.401 |
| Ensemble | 1.380 |

### fifwc-usa-par-2026-06-12 — Ergebnis 4:1 (team1_win)
Prognose-Stand: 2026-06-13T00:33:36

| Quelle | Brier |
|---|---|
| Polymarkt | 0.427 |
| Buchmacher | 0.444 |
| Kalshi | 0.419 |
| Modell | 0.858 ❌ |
| Whale | 0.001 ✅ |
| Ensemble | 0.400 |

### fifwc-swe-tun-2026-06-14 — Ergebnis 5:1 (team1_win)
Prognose-Stand: 2026-06-14T16:03:57+00:00

| Quelle | Brier |
|---|---|
| Polymarkt | 0.374 |
| Buchmacher | 0.384 ❌ |
| Kalshi | 0.358 |
| Modell | 0.354 ✅ |
| Ensemble | 0.370 |

### fifwc-aus-tur-2026-06-14 — Ergebnis 2:0 (team1_win)
Prognose-Stand: 2026-06-14T01:16:46

| Quelle | Brier |
|---|---|
| Polymarkt | 1.074 |
| Buchmacher | 1.070 |
| Kalshi | 1.053 |
| Modell | 0.980 ✅ |
| Whale | 1.465 ❌ |
| Ensemble | 1.093 |

### fifwc-ger-kor-2026-06-14 — Ergebnis 7:1 (team1_win)
Prognose-Stand: 2026-06-14T16:03:50+00:00

| Quelle | Brier |
|---|---|
| Polymarkt | 0.005 |
| Buchmacher | 0.004 ✅ |
| Kalshi | 0.007 |
| Modell | 0.059 ❌ |
| Ensemble | 0.012 |

### fifwc-nld-jpn-2026-06-14 — Ergebnis 2:2 (draw)
Prognose-Stand: 2026-06-14T16:03:55+00:00

| Quelle | Brier |
|---|---|
| Polymarkt | 0.815 ✅ |
| Buchmacher | 0.821 |
| Kalshi | 0.819 |
| Modell | 0.833 ❌ |
| Ensemble | 0.820 |

## Rollierende Bestenliste (alle aufgelösten Spiele)

| Rang | Quelle | Ø Brier | Ø RPS | Ø LogLoss | Hit-Rate | R/F | n |
|---|---|---|---|---|---|---|---|
| 1 | Kalshi | 0.650 | 0.193 | 1.045 | 50% | 4/4 | 8 |
| 2 | Ensemble | 0.650 | 0.193 | 1.062 | 50% | 4/4 | 8 |
| 3 | Polymarkt | 0.657 | 0.195 | 1.057 | 50% | 4/4 | 8 |
| 4 | Buchmacher | 0.655 | 0.196 | 1.052 | 50% | 4/4 | 8 |
| 5 | Modell | 0.725 | 0.225 | 1.144 | 38% | 3/5 | 8 |
| 6 | Whale | 0.719 | 0.242 | 1.444 | 50% | 2/2 | 4 |

_RPS = Ranked Probability Score (ordinal, Fußball-Standard). Brier 0.667 / RPS 0.333 / LogLoss 1.099 ≈ Zufall. Niedriger ist besser._

## Wett-Kennzahlen (Referenz-Policy)

_1 Einheit flat auf Ensemble-Favorit @ beste 1X2-Quote_

- Wetten: 7 · Trefferquote 43% · **ROI -33.9%**
- CLV: noch nicht messbar (Snapshots zu eng beieinander — aussagekräftig, sobald der Daily-Run Tage im Voraus läuft).

## Gewichts-Empfehlung

_Inverse-LogLoss-Empfehlung, geshrunken (α=0.35). Markt/Bücher/Kalshi korreliert → Block mit Vorsicht. Nicht auto-angewandt._

| Quelle | aktuell | empfohlen |
|---|---|---|
| Polymarkt | 0.3 | 0.276 |
| Buchmacher | 0.25 | 0.244 |
| Kalshi | 0.1 | 0.147 |
| Modell | 0.2 | 0.198 |
| Whale | 0.15 | 0.135 |

## Automatische Flags

- ⚠️ **Whale hochvariant** (Spannweite 0.001–1.465 über 4 Spiele) → defensive Gewichtung beibehalten, NICHT erhöhen.
- ⚠️ **Modell schwach kalibriert** (Ø 0.725 > 0.55) → Elo-/Gastgeber-Annahmen prüfen, sobald n≥5.
- ✅ Ensemble schlägt/erreicht Markt (Ø 0.650 vs. 0.657).

## Hermes-Analyse

Kalibrierung: Kalshi ist aktuell die beste voll besetzte Quelle (Ø Brier 0.6502, RPS 0.1928, LogLoss 1.0446, n=8). Das Ensemble liegt beim Brier gleichauf (0.6502) und beim RPS fast gleichauf (0.1930), verliert aber im LogLoss gegen Kalshi (1.0622 vs. 1.0446). Gegen den reinen Markt ist der Vorsprung real, aber klein: Brier 0.6502 vs. 0.6566 und RPS 0.1930 vs. 0.1953. Das ist ein Signal, aber noch kein Grund für aggressive Gewichtsänderungen.

Auffällig schlecht bleibt das reine Modell (Ø Brier 0.7247, RPS 0.2253, LogLoss 1.1436, Treffer 3/8). Der Grund wirkt nicht wie ein einzelner Datenfehler, sondern wie strukturelle Überzeugung auf Favoriten-/Stärkeannahmen bei dünner Turnierform: StatsBomb ist historisch, FBref-Form steht bei 0 Spielen, und die heutigen Match-Qualitätsgründe nennen regelmäßig "Form 0 Sp.". In den beiden großen Fehlprognosen Qatar-Schweiz 1:1 und Australien-Türkei 2:0 war das Modell zwar jeweils weniger schlecht als Markt/Bücher/Kalshi, aber alle Hauptquellen lagen auf dem falschen Favoriten; das hilft dem Ensemble nur begrenzt, weil die Marktquellen stark korreliert sind.

Positive Treffer: Deutschland-Korea war marktseitig praktisch sauber kalibriert (Bücher Brier 0.0042, Markt 0.0051, Ensemble 0.0124). Haiti-Schottland und USA-Paraguay zeigen, dass Whale-Signale einzelne Favoriten sehr gut treffen können (Whale Brier 0.0078 bzw. 0.0014), aber Australien-Türkei zeigt die Gegenprobe mit Whale Brier 1.4648. Daher bleibt die automatische Flag "Whale hochvariant" maßgeblich; n=4 reicht nicht für mehr Gewicht.

Wetten/CLV: Die Referenz-Policy steht bei 7 Wetten, 43% Trefferquote und ROI -33.9%. CLV ist nur als Tendenz lesbar: beat-close 57.1% über n=7, aber der Report warnt zurecht, dass Snapshots noch zu eng beieinander liegen. Für die heutigen offenen Spiele sind 0 Value-Bets ausgewiesen; mehrere zentrale EVs sind zwar positiv, werden durch konservative p-Abzüge auf negative EVs gedrückt. Das ist im Sinne der Leitplanken richtig und sollte nicht aufgeweicht werden.

Gewichte: `weights_suggestion.status=data-driven` bei n=8 liefert Markt 0.276, Bücher 0.244, Kalshi 0.147, Modell 0.198, Whale 0.135 gegenüber aktuell 0.300/0.250/0.100/0.200/0.150. Weil n=8 nur die Mindestschwelle ist und Markt/Bücher/Kalshi korreliert sind, heute keine Konfigurationsänderung empfehlen. Nächster Prüfpunkt: Stabilität bis mindestens n≥15, insbesondere ob Kalshi den LogLoss-Vorsprung hält und ob das Modell unter 0.70 Brier fällt.

# Closing-Loop-Report — 2026-06-15

Stand: 2026-06-15T07:30:55 · automatisch erzeugt (deterministisch, ohne Claude).
Narrative Hermes-Analyse: auf Anfrage.

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

| Rang | Quelle | Ø Brier | Ø RPS | Ø LogLoss | Hit-Rate | n |
|---|---|---|---|---|---|---|
| 1 | Kalshi | 0.650 | 0.193 | 1.045 | 50% | 8 |
| 2 | Ensemble | 0.650 | 0.193 | 1.062 | 50% | 8 |
| 3 | Polymarkt | 0.657 | 0.195 | 1.057 | 50% | 8 |
| 4 | Buchmacher | 0.655 | 0.196 | 1.052 | 50% | 8 |
| 5 | Modell | 0.725 | 0.225 | 1.144 | 38% | 8 |
| 6 | Whale | 0.719 | 0.242 | 1.444 | 50% | 4 |

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

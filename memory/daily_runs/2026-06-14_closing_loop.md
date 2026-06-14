# Closing-Loop-Report — 2026-06-14

Stand: 2026-06-14T12:46:11 · automatisch erzeugt (deterministisch, ohne Claude).
Narrative Hermes-Analyse: auf Anfrage.

## Aufgelöste Spiele (5)

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

## Rollierende Bestenliste (alle aufgelösten Spiele)

| Rang | Quelle | Ø Brier | Ø RPS | Ø LogLoss | Hit-Rate | n |
|---|---|---|---|---|---|---|
| 1 | Whale | 0.719 | 0.242 | 1.444 | 50% | 4 |
| 2 | Ensemble | 0.800 | 0.250 | 1.281 | 40% | 5 |
| 3 | Kalshi | 0.803 | 0.251 | 1.262 | 40% | 5 |
| 4 | Buchmacher | 0.806 | 0.253 | 1.271 | 40% | 5 |
| 5 | Polymarkt | 0.812 | 0.254 | 1.282 | 40% | 5 |
| 6 | Modell | 0.910 | 0.300 | 1.383 | 20% | 5 |

_RPS = Ranked Probability Score (ordinal, Fußball-Standard). Brier 0.667 / RPS 0.333 / LogLoss 1.099 ≈ Zufall. Niedriger ist besser._

## Wett-Kennzahlen (Referenz-Policy)

_1 Einheit flat auf Ensemble-Favorit @ beste 1X2-Quote_

- Wetten: 4 · Trefferquote 25% · **ROI -61.0%**
- CLV: noch nicht messbar (Snapshots zu eng beieinander — aussagekräftig, sobald der Daily-Run Tage im Voraus läuft).

## Gewichts-Empfehlung

- n=5 < 8: Prior beibehalten (kein Overfitting an Einzelspiele).

## Automatische Flags

- ⚠️ **Whale hochvariant** (Spannweite 0.001–1.465 über 4 Spiele) → defensive Gewichtung beibehalten, NICHT erhöhen.
- ⚠️ **Modell schwach kalibriert** (Ø 0.910 > 0.55) → Elo-/Gastgeber-Annahmen prüfen, sobald n≥5.
- ✅ Ensemble schlägt/erreicht Markt (Ø 0.800 vs. 0.812).

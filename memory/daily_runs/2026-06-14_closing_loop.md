# Closing-Loop-Report — 2026-06-14

Stand: 2026-06-14T01:17:49 · automatisch erzeugt (deterministisch, ohne Claude).
Narrative Hermes-Analyse: auf Anfrage.

## Aufgelöste Spiele (2)

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

## Rollierende Bestenliste (alle aufgelösten Spiele)

| Rang | Quelle | Ø Brier | Ø LogLoss | Hit-Rate | n |
|---|---|---|---|---|---|
| 1 | Whale | 0.701 | 1.705 | 50% | 2 |
| 2 | Ensemble | 0.890 | 1.412 | 50% | 2 |
| 3 | Kalshi | 0.914 | 1.379 | 50% | 2 |
| 4 | Buchmacher | 0.922 | 1.398 | 50% | 2 |
| 5 | Polymarkt | 0.934 | 1.424 | 50% | 2 |
| 6 | Modell | 1.116 | 1.621 | 0% | 2 |

_Brier 0.667 / LogLoss 1.099 = Zufall. Niedriger ist besser._

## Wett-Kennzahlen (Referenz-Policy)

_1 Einheit flat auf Ensemble-Favorit @ beste 1X2-Quote_

- Wetten: 1 · Trefferquote 0% · **ROI -100.0%**
- CLV: noch nicht messbar (Snapshots zu eng beieinander — aussagekräftig, sobald der Daily-Run Tage im Voraus läuft).

## Gewichts-Empfehlung

- n=2 < 8: Prior beibehalten (kein Overfitting an Einzelspiele).

## Automatische Flags

- ⚠️ **Whale hochvariant** (Spannweite 0.001–1.401 über 2 Spiele) → defensive Gewichtung beibehalten, NICHT erhöhen.
- ⚠️ **Modell schwach kalibriert** (Ø 1.116 > 0.55) → Elo-/Gastgeber-Annahmen prüfen, sobald n≥5.
- ✅ Ensemble schlägt/erreicht Markt (Ø 0.890 vs. 0.934).
- ℹ️ Erst 2 Spiele aufgelöst — keine Gewichtsänderungen vor n≥5 (Schutz vor Überanpassung an Einzelspiele).

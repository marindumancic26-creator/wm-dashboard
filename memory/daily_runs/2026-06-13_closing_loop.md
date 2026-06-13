# Closing-Loop-Report — 2026-06-13

Stand: 2026-06-13T21:02:12 · automatisch erzeugt (deterministisch, ohne Claude).
Narrative Hermes-Analyse: auf Anfrage.

## Aufgelöste Spiele (1)

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
| 1 | Whale | 0.001 | 0.028 | 100% | 1 |
| 2 | Ensemble | 0.400 | 0.726 | 100% | 1 |
| 3 | Kalshi | 0.419 | 0.750 | 100% | 1 |
| 4 | Polymarkt | 0.427 | 0.761 | 100% | 1 |
| 5 | Buchmacher | 0.444 | 0.782 | 100% | 1 |
| 6 | Modell | 0.858 | 1.372 | 0% | 1 |

_Brier 0.667 / LogLoss 1.099 = Zufall. Niedriger ist besser._

## Gewichts-Empfehlung

- n=1 < 8: Prior beibehalten (kein Overfitting an Einzelspiele).

## Automatische Flags

- ⚠️ **Modell schwach kalibriert** (Ø 0.858 > 0.55) → Elo-/Gastgeber-Annahmen prüfen, sobald n≥5.
- ✅ Ensemble schlägt/erreicht Markt (Ø 0.400 vs. 0.427).
- ℹ️ Erst 1 Spiele aufgelöst — keine Gewichtsänderungen vor n≥5 (Schutz vor Überanpassung an Einzelspiele).

# Backtest-Report — Angriff/Abwehr-Engine + Dixon-Coles

Datengrundlage: 128 WM-Spiele (StatsBomb 2018+2022), 5-fold-Kreuzvalidierung (out-of-sample).

**Baseline (Basisraten):** Brier 0.6439, LogLoss 1.0629

| rho | Brier | LogLoss | Hit-Rate | n |
|---|---|---|---|---|
| 0.0 | 0.7318 | 1.7018 | 42% | 128 | ⭐
| -0.05 | 0.7334 | 1.7081 | 42% | 128 |
| -0.1 | 0.7352 | 1.7151 | 42% | 128 |
| -0.15 | 0.7372 | 1.7229 | 43% | 128 |
| -0.2 | 0.7394 | 1.7309 | 43% | 128 |

**Bestes rho (Out-of-sample): 0.0** (LogLoss 1.7018).
Engine schlägt Basisraten: NEIN (LogLoss 1.7018 vs. 1.0629).

_Hinweis: ELO_PER_GOAL wird hier NICHT getunt (kein historisches Elo). Validiert sind die getrennte Angriff/Abwehr-Struktur und der rho-Wert._

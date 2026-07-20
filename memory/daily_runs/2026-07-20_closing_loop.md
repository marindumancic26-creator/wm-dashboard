# Closing-Loop-Report — 2026-07-20

Stand: 2026-07-20T09:05:51 · automatisch erzeugt (deterministisch, ohne Claude).
Narrative Hermes-Analyse: auf Anfrage.

> Kalibrierung nicht verfügbar: football-data.org-Fehler: HTTPSConnectionPool(host='api.football-data.org', port=443): Max retries exceeded with url: /v4/competitions/WC/matches?status=FINISHED (Caused by ConnectTimeoutError(<HTTPSConnection(host='api.football-data.org', port=443) at 0x224fea37a40>, 'Connection to api.football-data.org timed out. (connect timeout=25)'))

## Hermes-Analyse

Der heutige Fallback-Hermes nutzt den deterministischen Snapshot 2026-07-20T09:05:51. Der Daily-Lauf verarbeitete 0 Spiele mit 0 Fehlern; Value-Bets stehen bei 0 und Gesamtstake 0.0%. FBref-Form steht auf stale; alle Modell- und Staking-Parameter bleiben unveraendert.

Rollierend sind 0 Spiele aufgeloest. Beste Quelle nach Brier ist ensemble mit Brier/RPS/LogLoss None/None/None. Das Ensemble liegt bei None/None/None und 0.0% Trefferquote. Markt und Kalshi liegen bei Brier None bzw. None.

Das reine Modell bleibt mit Brier None hinter dem Marktblock, Whale bleibt mit LogLoss None hochvariant. Daraus folgt keine automatische Gewichts-, Parameter- oder Staking-Aenderung.

Die Referenz-Policy steht bei 0 Wetten, ROI +0.00% und durchschnittlichem CLV +0.00%. Das ist ein Beobachtungssignal, aber kein Freibrief, solange Ensemble-vs.-Markt nicht stabil positiv ist.

`weights_suggestion` wird nur notiert: market 0.300, books 0.250, kalshi 0.100, model 0.200, whale 0.150. Parameter-Tuning bleibt Report-only (Vorschlag, keine Auto-Uebernahme. Headline ist Walk-forward-RPS; In-sample und Live-rho-Grid sind nur Diagnose.).

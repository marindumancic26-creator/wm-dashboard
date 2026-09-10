# Closing-Loop-Report — 2026-09-10

Stand: 2026-09-10T16:06:03 · automatisch erzeugt (deterministisch, ohne Claude).
Narrative Hermes-Analyse: siehe Abschnitt unten.

> Kalibrierung nicht verfügbar: football-data.org-Fehler: HTTPSConnectionPool(host='api.football-data.org', port=443): Max retries exceeded with url: /v4/competitions/WC/matches?status=FINISHED (Caused by ConnectTimeoutError(<HTTPSConnection(host='api.football-data.org', port=443) at 0x212c9592090>, 'Connection to api.football-data.org timed out. (connect timeout=25)'))
## Hermes-Analyse

Der heutige Fallback-Hermes nutzt den deterministischen Snapshot 2026-09-10T09:00:16. Der Daily-Lauf verarbeitete 0 Spiele mit 0 Fehlern; Value-Bets stehen bei 0 und Gesamtstake 0.0%. FBref-Form steht auf stale; alle Modell- und Staking-Parameter bleiben unveraendert.

Rollierend sind 93 Spiele aufgeloest. Beste Quelle nach Brier ist ensemble mit Brier/RPS/LogLoss 0.4441/0.1563/0.7752. Das Ensemble liegt bei 0.4441/0.1563/0.7752 und 73.1% Trefferquote. Markt und Kalshi liegen bei Brier 0.4501 bzw. 0.4458.

Das reine Modell bleibt mit Brier 0.4724 hinter dem Marktblock, Whale bleibt mit LogLoss 1.2652 hochvariant. Daraus folgt keine automatische Gewichts-, Parameter- oder Staking-Aenderung.

Die Referenz-Policy steht bei 89 Wetten, ROI +0.00% und durchschnittlichem CLV +0.00%. Das ist ein Beobachtungssignal, aber kein Freibrief, solange Ensemble-vs.-Markt nicht stabil positiv ist.

`weights_suggestion` wird nur notiert: market 0.153, books 0.150, kalshi 0.158, model 0.376, whale 0.162. Parameter-Tuning bleibt Report-only (Vorschlag, keine Auto-Uebernahme. Headline ist Walk-forward-RPS; In-sample und Live-rho-Grid sind nur Diagnose.).

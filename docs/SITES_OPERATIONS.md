# Private Fußballanalyse: Betrieb

## Quellen und Stand
- Python-Code: bestehendes wm-dashboard-Repository, Pipeline `python -m src.pipeline.club_sites_run`.
- Sites-Quellcode: eigener Checkout und eigenes privates Sites-Repository; Hosting-ID `appgprj_6aebaddeca5c8191ac55299e3cb06ae6`.
- Site: https://marin-fussballanalyse.sunnymelon11.chatgpt.site (Veröffentlichung gesondert prüfen).
- Oberfläche und Read-API benötigen Sites-Identität; Maschinenendpunkte benötigen zusätzlich das Import-Secret.

## GitHub-Konfiguration
Repository-Secrets: `ODDS_API_KEY`, `FOOTBALL_DATA_API_KEY`, `FOOTBALL_SITE_URL`, `FOOTBALL_SITE_BYPASS`, `FOOTBALL_IMPORT_SECRET`.
Repository-Variable: `FOOTBALL_SITES_ENABLED=true` aktiviert den Workflow erst nach erfolgreichem Cloud-Readback und bestätigter kostenloser Standard-Linux-Ausführung.

09:00, 14:00 und 18:00 Europe/Berlin sind Sollzeiten. UTC-Doppeltrigger berücksichtigen DST; Slot-Claims in D1 verhindern Doppelabrufe. Es gibt keine Pünktlichkeitsgarantie von GitHub. Ein beanspruchter, abgebrochener Slot wird nicht nochmals kostenpflichtig ausgeführt; der nächste Slot kann fortsetzen.

## Budget und Handover
Eine EU-Region, `h2h,totals`, höchstens zwei reservierte Credits je Wettbewerbsabruf. Ein kreditfreier Sports-Request prüft die Providerheader. Fehlende oder widersprüchliche Budgetdaten stoppen weitere kostenpflichtige Abrufe. Die serverseitige Grenze beträgt höchstens 500 Credits einschließlich beobachtetem Verbrauch. Reservierungen werden bei unsicherem Ausgang nicht zurückgebucht. Damit kann das angezeigte Restbudget konservativer als beim Provider ausfallen.

Nach Cloud-Abnahme verhindert `data/processed/club_sites_odds_owner.json` im bisherigen lokalen Checkout weitere WM-Quotenabrufe. Schlüssel bleiben unverändert. Vor einer Rückkehr zum lokalen Betrieb zuerst die GitHub-Variable deaktivieren, dann die Handover-Datei kontrolliert entfernen.

## Daten und Störungen
D1 speichert Runs, Budget und Claims; R2 archiviert die Originalantworten. Das ist keine externe WORM- oder Zeitattestierung. Rohdaten und Secrets gehören nicht ins öffentliche GitHub-Repository. Fehlgeschlagene Quellen erhalten den letzten bekannten Stand mit unverändertem Zeitstempel; die UI markiert ihn veraltet. Ein als gesperrt importiertes Modell kann über die API nicht freigeschaltet werden.

Lokale Pending-Runs werden beim nächsten lokalen Lauf erneut hochgeladen, ohne Provider nochmals abzurufen. In einem vollständig ausgefallenen kurzlebigen Runner kann ein noch nicht hochgeladener Capture verloren gehen; der reservierte Verbrauch bleibt in D1 erhalten.

## Prüfungen
Python: `python -m pytest -q`.
Site: `node --experimental-strip-types --test tests/domain.test.ts`, `npx tsc --noEmit`, offizieller Sites-Build.
Die endgültigen Prüfergebnisse, Deployment- und Actions-IDs stehen im Umsetzungsprotokoll.

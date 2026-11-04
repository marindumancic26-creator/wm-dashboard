# Private Fußballanalyse mit Sites

Vom Nutzer bestätigter Entwurf vom 04.11.2026.

## Ziel
Private, mobile-first Site für Bundesliga, Champions League, Serie A, La Liga und Premier League. Stufenweiser Start mit echten Spielplänen und 1X2-/Über-Unter-Quoten. Modellwahrscheinlichkeiten, faire Quoten und EV bleiben hinter den bestehenden Vereins-Freigaben. Keine automatischen Wetten und keine zusätzliche Echtgeldfreigabe.

## Entscheidungen
- Bestehendes Python-Projekt erweitern; WM-Ausgaben nicht überschreiben.
- GitHub Actions führt die Pipeline unabhängig vom Rechner aus.
- Drei Slots: 09:00, 14:00, 18:00 Europe/Berlin; DST und verspätete/duplizierte Läufe berücksichtigen.
- Eine Buchmacherregion EU, Märkte h2h und totals. Quoten nur für Wettbewerbe mit heute noch nicht angepfiffenen Spielen.
- Datenbudget 0 EUR: verfügbare Credits kontrollieren, vor Abrufen reservieren, bei unbekanntem Budget stoppen. Bei Knappheit Abrufe auf restliche Tage verteilen und nähere Anstöße priorisieren.
- Sites owner-private mit serverseitigem Lesen und geschütztem Maschinenimport; D1 als Index/Zustand, R2 als Archiv.
- Versionierte, idempotente Runs mit stabilen Spiel-IDs, UTC-Datenzeiten, Quellstatus und Marktlinien. Letzter gültiger Stand bleibt bei Fehlern erhalten.
- Keine Provider-Abfrage durch Öffnen/Neuladen im Browser.
- Keine erfundenen Daten, fehlende Abdeckung offen anzeigen. Modell- und Marktwahrscheinlichkeiten trennen; gleiche Torlinie vergleichen.
- Bestehende Modell-/Lockbox-Gates und Mindesttrainingsmengen unverändert. Keine Übertragung von WM-Nationalmannschaftswerten auf Vereine.
- Helle neutrale Oberfläche, Grün als Akzent, mobile Spielkarten mit ausklappbaren Details; Desktop Liste/Detail. Lade-, Fehler-, Leer-, veraltete und gesperrte Zustände.
- Frontend Architect führt Stack-/Komponentenentscheidungen; Design Taste nur für passende allgemeine Gestaltungsregeln.

## Architektur
Provider -> kanonische Club-Fixtures -> budgetierter Quotenabruf -> versionierter Run -> authentifizierter Sites-Import -> R2/D1 -> private Read-API -> Oberfläche.

Sites verwendet den offiziellen Vinext-Starter für serverseitige Funktionen. GitHub-Secrets halten Providerzugänge und Maschinenzugriff. Die App verlangt zusätzlich zum Sites-Zugang ein getrenntes Import-Secret; dieses erscheint nie im Browser. Bestehende Datenprovider und Modellcode werden wiederverwendet.

## Veröffentlichung
Zuerst private Site mit realen Fixtures/Quoten, dann freigegebene Modelle. Vor Aktivierung des Cloud-Zeitplans GitHub-Zugang, enthaltene Ausführung, gültige Providerzugänge und echten Schreib-/Leseablauf nachweisen. Konkurrierende lokale Quotenjobs bei der Umstellung kontrolliert ablösen. Fehlende Voraussetzungen sichtbar melden, keinen kostenpflichtigen Ersatz wählen.

## Abnahme
Bestehende Modelltests; neue Quotenlinien-, UTC/DST-, Budget-, Idempotenz-, Auth- und Datenverlusttests. Build, Handy-/Desktop-/Tastaturprüfung. Echter Cloud-Import mit Readback. Modellüberlegenheit wird nicht vorausgesetzt.

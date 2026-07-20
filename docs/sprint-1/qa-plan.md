# Sprint 1 — Unabhängiger QA-Plan für die Club-Lockbox

Owner: **Ivy (QA)**  
Scope: Prospektive, versionierte Shadow-/Lockbox-Auswertung  
Arbeitsweise: Implementierung durch Sage; anschließender unabhängiger Read-only-QA-Lauf  
Grundsatz: Jeder Integritäts-, Leakage- oder Versionsfehler blockiert die Freigabe.

## P0 — Muss vor jedem Sign-off bestehen

### 1. Artefakt- und Manifestvertrag

- Manifest friert mindestens `schema_version`, `candidate_version`, Modell-/Konfigurationshash,
  Cutoff-Regel, Parameter, Benchmarkdefinitionen und Guardrails ein.
- Forecast-Artefakte enthalten eine kanonische `match_id`, Fixture-Revision beziehungsweise
  Kickoff, `generated_at_utc`, Modellversion, rohe Modellwahrscheinlichkeiten und die final
  eingefrorenen Kandidatenwahrscheinlichkeiten.
- Closing-Artefakte enthalten Quelle, Capture-Zeitpunkt, rohe beziehungsweise entvigte
  Wahrscheinlichkeiten sowie Qualitätsstatus.
- Result-Artefakte sind von Forecast und Closing getrennt. Forecast-Erzeugung darf weder
  Ergebnis noch nachträglich bekannte Ergebnisfelder entgegennehmen.
- Wahrscheinlichkeiten müssen endlich, nicht negativ und auf 1 normiert sein. Fehlende,
  unbekannte oder ungültige Versionen und naive Zeitstempel werden fail-closed abgewiesen.
- `mode=shadow`, `auto_apply=false`, `prediction_allowed=false`, `value_allowed=false` und
  deaktivierte Stakes bleiben unveränderliche Schutzfelder.

### 2. Leakage und feste Cutoff-Regel

- Frühe, letzte zulässige, exakt am Cutoff liegende und verspätete Captures werden in
  zufälliger Reihenfolge geprüft. Ausschließlich `captured_at_utc < cutoff_utc` ist zulässig.
- Dateiname, Verzeichnisreihenfolge und JSON-Einfügereihenfolge dürfen die Auswahl nicht
  beeinflussen; sortiert wird nach geparstem UTC-Zeitpunkt mit dokumentiertem Tie-Break.
- Der primäre Closing-Stand folgt dem prospektiv eingefrorenen Cutoff, standardmäßig T-5
  Minuten. Ein späterer offizieller Close darf nur als separat benannter Sekundärbenchmark
  erscheinen.
- Nach einem verschobenen Kickoff wird die Fixture-Revision berücksichtigt. Ein Capture,
  das relativ zum gültigen Cutoff verspätet ist, bleibt ausgeschlossen.
- Das Ändern aktueller oder zukünftiger Resultate darf weder ein bereits gespeichertes
  Forecast-Artefakt noch seine Parameterauswahl verändern.

### 3. Create-only, Idempotenz und Duplikate

- Derselbe logische Write zweimal erzeugt genau ein Artefakt und identische Nutzdaten.
- Gleiche `match_id`, Version und Capture-ID mit identischem Inhalt sind idempotent.
- Dieselbe Identität mit abweichendem Inhalt ist ein Konflikt: kein Überschreiben, keine
  Last-write-wins-Semantik; der Lauf wird blockiert oder der Konflikt explizit quarantänisiert.
- Doppelte Providerzeilen und providerübergreifende Duplikate werden über die kanonische
  `match_id` deterministisch erkannt. Nicht eindeutig versöhnbare Identitäten bleiben gesperrt.
- Parallele Writer dürfen weder Datensätze verlieren noch beschädigte oder doppelte
  Artefakte erzeugen.

### 4. Atomare Persistenz und Integrität

- Temporäre Dateien entstehen im Zielverzeichnis, werden vollständig geschrieben und
  geflusht und anschließend per atomarem Replace beziehungsweise create-only Commit sichtbar.
- Simulierte Fehler bei Serialisierung, Write, Flush und Commit lassen ein vorhandenes
  gültiges Artefakt unverändert.
- Leser sehen bei einem konkurrierenden Write ausschließlich den alten oder den neuen
  vollständigen Stand, niemals partielles JSON.
- SHA-256 beziehungsweise Manifest-Hash erkennt nachträgliche Manipulation. Manipulierte,
  unlesbare und verwaiste Temp-Artefakte führen nicht zu einer positiven Auswertung.

### 5. Fehlende und verspätete Closing-Quoten

- Jeder zulässige eingefrorene Forecast bleibt im Coverage-Nenner, auch ohne Closing-Quote.
- Fehlendes Closing wird als `unpaired` beziehungsweise `missing_closing` ausgewiesen und
  darf nicht durch Vorfilterung verschwinden.
- Eine verspätet eintreffende, aber vor Cutoff erfasste Quote darf deterministisch gepaart
  werden. Eine nach Cutoff oder Kickoff erfasste Quote darf dies niemals.
- Bei mehreren zulässigen Captures gilt die manifestierte Auswahlregel. Gleichstände besitzen
  einen stabilen Tie-Break; Fallback- und stale-Quellen bleiben getrennt gekennzeichnet.
- Coverage-Grenzwerte werden direkt unter, exakt auf und direkt über dem Schwellwert getestet.

### 6. Versionsisolation

- Jede Änderung an Kandidatenlogik, Parametern, Grid oder Cutoff erzeugt eine neue
  `candidate_version` beziehungsweise einen neuen Manifest-Hash.
- Alte Artefakte werden niemals mit einer neuen Version nachberechnet oder überschrieben.
- Metriken und Gates werden je Kandidaten- und Modellversion getrennt berechnet. Gemischte
  Kohorten dürfen nicht aggregiert freigegeben werden.
- Opening-/Closing-Vergleiche über eine Versionsgrenze werden blockiert oder als eigener,
  nicht freigabefähiger Diagnoseblock ausgewiesen.
- Retuning darf ausschließlich zukünftige, nach dem neuen Manifest erzeugte Forecasts
  beeinflussen.

### 7. Freigabe-Gates

- Prospektiv müssen RPS und LogLoss aggregiert jeweils besser als der rohe Closing-Markt sein.
- Für beide Metriken muss die obere 95-%-Bootstrap-Grenze des Deltas unter null liegen.
- Mindestens vier von fünf verpflichtenden Ligen müssen beide Metriken schlagen.
- Mindest-Coverage, Mindeststichprobe, Mindestbeobachtungsdauer, alle Pflichtligen,
  Manifestintegrität und Versionsreinheit müssen erfüllt sein.
- Der Kandidat muss zusätzlich gegen den separat ausgewiesenen `alpha=0`-Marktkalibrator
  bestehen; Markt-Rekalibrierung allein gilt nicht als Modell-Edge.
- Jeder einzelne falsche Gate-Wert blockiert. Leere Listen oder leere Wettbewerbsblöcke
  dürfen nicht durch `all([])` positiv bewertet werden.
- Auch bei bestandenen Statistik-Gates bleibt die Freigabe `manual_only`; menschliche
  Zustimmung ist verpflichtend. Value, Auto-Apply und Stakes bleiben gesperrt.

## P1 — Robustheit und Betriebsverträglichkeit

### 1. Windows-Pfade

- Relative Pfade, `..`, gemischte Separatoren, abweichende Groß-/Kleinschreibung und der
  Unicode-Projektpfad `Fußball wahrscheinlichkeit` werden korrekt aufgelöst.
- Produktive WM-Ausgaben können weder direkt noch über Pfadalias, Symlink oder Junction als
  Lockbox-Ziel verwendet werden.
- Temp- und Zielartefakt liegen auf demselben Volume. `PermissionError` oder kurzzeitige
  Antivirus-Sperren beschädigen den letzten gültigen Stand nicht.

### 2. Determinismus und Reproduzierbarkeit

- Kanonische Serialisierung erzeugt für semantisch identische Payloads unabhängig von
  Dictionary-Reihenfolge denselben Hash.
- Evaluationsmetriken, Bootstrap und Tie-Breaks sind bei fixiertem Seed reproduzierbar.
- Eine vollständige Auswertung aus unveränderten Artefakten liefert wiederholt identische
  Metriken, Coverage-Zähler, Gate-Ergebnisse und Reports.

### 3. Degradation und Reporting

- Ausfall einer Liga oder Quelle isoliert den Fehler, markiert den Lauf degradiert und kann
  die Gesamtfreigabe nicht positiv machen.
- Unbekannte Clubs und nicht kanonische Fixtures bleiben sichtbar, aber ohne Prognose-,
  Pairing- oder Value-Freigabe.
- Report und maschinenlesbare Ausgabe stimmen bei Nennern, Paarzahlen, Versionen,
  Benchmarks und Gate-Werten überein.
- Fehlermeldungen enthalten genug Kontext für Diagnose, aber keine Schlüssel oder geheimen
  Rohdaten.

## Bestehende Testmuster zur Wiederverwendung

- `test_replay_snapshot_selects_only_last_pre_kickoff`: UTC- und Leakage-Selektion.
- `test_parameter_tuning_selects_last_pre_kickoff_snapshot`: letzter zulässiger Snapshot.
- `test_calibration_separates_model_versions`: getrennte Versionskohorten.
- `test_canonical_match_id_is_provider_and_reschedule_independent`: stabile Match-Identität.
- `test_club_shadow_run_writes_only_shadow_output` und
  `test_club_shadow_run_refuses_productive_wm_outputs`: Shadow-Schutz und Pfadgrenzen.
- `test_multi_competition_shadow_run_isolates_source_failure`: Liga-/Quellenisolation.
- `test_closing_gate_requires_both_rps_and_logloss`,
  `test_closing_gate_requires_four_of_five_leagues` und
  `test_closing_gate_fails_without_coverage`: fail-closed Statistik-Gates.
- `test_club_migration_readiness_*`: menschliche Freigabe, Sperrfelder und Gesamtgate.
- `test_history_csv_parser_averages_bookmaker_closing_consensus`,
  `test_history_csv_parser_excludes_stale_pinnacle_after_warning` und
  `test_history_csv_parser_does_not_fallback_to_opening_average`: Closing-Quellenstatus.
- `tmp_path` plus `monkeypatch` aus den Adapter- und Pipeline-Tests: isolierte Persistenz-
  und Failure-Injection-Tests.

## Read-only-QA-Lauf nach Implementierung

1. Änderungen und Artefaktverträge gegen diesen Plan und `docs/lockbox-design.md` prüfen.
2. P0-Tests einzeln ausführen und bei Fehlern sofort Sign-off blockieren.
3. P1-Tests und gezielte Failure Injection ausführen.
4. Vorgeschriebene Suite aus `AGENTS.md` ausführen:
   `python -m pytest quality/test_functional.py tests/test_model.py -q`.
5. Bei Berührung von Ensemble, Monte Carlo oder Value zusätzlich
   `python -m pytest quality/test_regression.py -q` ausführen.
6. Vollständige Suite ausführen und `git diff --check` prüfen.
7. Arbeitsbaum auditieren: keine unbeabsichtigten produktiven Ausgaben, Parameter-, Weight-
   oder Stakingänderungen und keine erzeugten Geheimnisse.

## Explizite Sign-off-Kriterien

QA erteilt Sign-off nur, wenn alle folgenden Bedingungen erfüllt sind:

- Alle P0-Fälle sind automatisiert und grün; kein P0-Fall ist `xfail`, übersprungen oder nur
  manuell beschrieben.
- Alle relevanten P1-Fälle sind grün oder besitzen einen dokumentierten, nicht sicherheits-
  oder evidenzrelevanten Restpunkt mit Owner und Folgetermin.
- Die vorgeschriebene und die vollständige Testsuite sind grün; `git diff --check` ist sauber.
- Fehlende Closing-Quoten bleiben nachweislich im Nenner, Versionen sind strikt isoliert und
  Cutoff-/Kickoff-Leakage ist durch Negativtests ausgeschlossen.
- Create-only-, Idempotenz-, Konflikt- und Atomicity-Tests beweisen, dass kein bestehendes
  Beweisartefakt still überschrieben oder partiell sichtbar werden kann.
- Rohmarkt und `alpha=0`-Kalibrator werden getrennt berichtet; kein Gate nutzt synthetische,
  unvollständige oder versionsgemischte Evidenz.
- Die Readiness bleibt bis zum prospektiven Bestehen aller Gates und menschlicher Zustimmung
  blockiert. `auto_apply`, Value und Stakes sind weiterhin deaktiviert.
- Der QA-Bericht nennt Testkommandos, Ergebnisse, geprüften Commit beziehungsweise Diff und
  alle verbleibenden Risiken.

Bis diese Kriterien erfüllt sind, lautet der QA-Status **BLOCKED / kein produktiver Einsatz**.

# Lockbox-Protokoll für `closing_residual_v1`

Status: **verbindliches Quant-Governance-Protokoll**  
Geltungsbereich: prospektive Shadow-Validierung des Closing-Residualkandidaten  
Grundsatz: Bis zur definitiven Freigabe bleiben `auto_apply` und reale Stakes ausgeschaltet.

Die Begriffe **MUSS**, **DARF NICHT** und **SOLL** sind normativ. Eine Abweichung ist kein
Interpretationsspielraum, sondern ein dokumentationspflichtiger Integritätsverstoß.

## 1. Zweck und Hypothese

Die Lockbox prüft, ob eine vorab eingefrorene Version des Kandidaten auf neuen Spielen den
Closing-Markt reproduzierbar schlägt. Sie ist keine weitere Tuningfläche. Die primäre Hypothese
lautet, dass der Kandidat auf identischen, gepaarten Spielen sowohl einen niedrigeren Ranked
Probability Score (RPS) als auch einen niedrigeren LogLoss als beide Pflichtbenchmarks erzielt.

Eine Verbesserung gegenüber dem rohen Markt allein belegt keine Modell-Edge. Da der historische
Kandidat überwiegend eine Markt-Rekalibrierung darstellt, MUSS er zusätzlich den reinen
`alpha=0`-Marktkalibrator schlagen.

## 2. Unveränderliches Manifest

Vor dem ersten eingeschlossenen Anstoß MUSS ein Manifest erzeugt, gehasht und eingefroren werden.
Nach dem Freeze DARF es nicht überschrieben werden. Das Manifest enthält mindestens:

- `lockbox_id`, `epoch_id`, `candidate_name` und eindeutige `candidate_version`;
- `frozen_at_utc` mit explizitem `Z` oder `+00:00`;
- Git-Commit, Code-Hash und Schema-Version;
- vollständige Konfiguration einschließlich Residual-Alpha, Markt-Temperatur,
  Remis-Multiplikator, Parametergrids und aller Defaultwerte;
- Modell- und Featuredefinition einschließlich Basismodell-Version;
- Trainingsdaten-Dateien mit SHA256, Datenzeitraum und maximalem Informationszeitpunkt;
- Buchmacher-Whitelist, Quellenpriorität, De-vig-, Konsens- und Missing-Data-Regeln;
- Population, Wettbewerbe, Saison/Epoch, Ein- und Ausschlussregeln;
- Capture-Cutoff, zulässige Staleness und Zeitstempelregeln;
- Benchmarkdefinitionen, Metriken, Bootstrapverfahren, Gates und Guardrail-Grenzen;
- geplante Auswertungszeitpunkte und gegebenenfalls vorab festgelegtes sequenzielles
  Test-/Alpha-Spending-Verfahren;
- SHA256 des kanonisch serialisierten Manifests.

Jeder Lockbox-Record MUSS den Manifest-Hash referenzieren. Die bestehende allgemeine
`MODEL_VERSION` genügt nicht, wenn sie Residual-, Benchmark-, Daten- oder Capture-Regeln nicht
vollständig abbildet.

## 3. Prospektiver T-5-Cutoff und Zeitstempel

Der operative Cutoff ist **T-5:00 Minuten** relativ zum zuletzt vor dem Capture autoritativ
bekannten Anstoßzeitpunkt. Für Kandidat und Benchmarks MUSS derselbe atomare Markt-Capture
verwendet werden.

- Kein Quoten-, Feature- oder Modelleingang DARF nach dem T-5-Cutoff erfasst worden sein.
- Verwendet wird der prospektiv geplante T-5-Capture, nicht nach Spielende der günstigste oder
  schlicht „letzte“ Snapshot. Ein früherer Ersatz ist nur zulässig, wenn die im Manifest
  festgelegte maximale Staleness eingehalten wird.
- `generated_at_utc`, `scheduled_kickoff_utc`, später `actual_kickoff_utc` und jeder
  `source_captured_at_utc` MUSS explizit UTC sein. Naive lokale ISO-Zeitstempel sind ungültig.
- Nach Vorliegen des tatsächlichen Anstoßes MUSS zusätzlich geprüft werden, dass alle Inputs vor
  dem tatsächlichen Anstoß lagen. Ein Capture nach tatsächlichem Anstoß ist ungültig.
- Eine spätere Kickoffkorrektur ändert keine Prognose. Sie wird als Amendment angehängt und kann
  den Record nach den vorab definierten Regeln ungültig machen.
- Ein offizieller späterer Closing-Preis darf als sekundärer Benchmark gespeichert werden, aber
  niemals rückwirkend Input der handelbaren T-5-Prognose sein.

## 4. Population

Die primäre Population umfasst regulär beendete 1X2-Ligaspiele der folgenden fünf Wettbewerbe:

- Premier League;
- La Liga;
- Bundesliga;
- Serie A;
- Ligue 1.

Ein Spiel ist nur einschließbar, wenn vor dem Ergebnis eine kanonische Match-ID, eindeutige
Heim-/Auswärtsidentität, Wettbewerb, Saison, Spieltag und ein gültiger UTC-Anstoßzeitpunkt
vorlagen. Abgebrochene, annullierte oder nicht regulär gewertete Spiele sowie Fixtures mit
ungeklärter Identität werden nach der eingefrorenen Regel ausgeschlossen. Entscheidungen dürfen
nicht vom Ergebnis, den Prognosen oder der späteren Score-Differenz abhängen.

Der Coverage-Nenner umfasst alle grundsätzlich populationsfähigen, später regulär beendeten
Fixtures, auch wenn der Capture fehlt. Fehlende Daten dürfen die Population daher nicht künstlich
verbessern.

## 5. Append-only Lockbox-Artefakte

Pro Match und Capture MUSS ein neues, unveränderliches Artefakt geschrieben werden. Eine laufend
überschriebene Sammeldatei ist kein Lockbox-Beleg. Jeder Forecast-Record enthält mindestens:

- kanonische Match-ID, Capture-/Prediction-ID, Liga, Saison und Spieltag;
- Manifest-Hash, Kandidatenversion und Code-Commit;
- alle Zeitstempel aus Abschnitt 3;
- rohe Quoten je Whitelist-Buch mit Quellenkennung;
- entviggte Konsenswahrscheinlichkeiten des rohen Markts;
- Wahrscheinlichkeiten des `alpha=0`-Marktkalibrators;
- eingefrorene Basismodell- und Kandidatenwahrscheinlichkeiten;
- verwendete Parameter, Datenqualitätsstatus und Ausschlussgrund, falls nicht eligible;
- SHA256 des kanonisch serialisierten Records.

Ergebnisse werden erst nach Spielende in separaten append-only Resultat-Records erfasst. Forecasts
werden niemals ergänzt oder überschrieben. Korrekturen erfolgen ausschließlich als versionierte,
verkettete Amendment-Records; Original und Änderung bleiben prüfbar. Ein Hash-Manifest oder eine
Hash-Chain MUSS fehlende, ersetzte oder veränderte Artefakte erkennbar machen.

## 6. Pflichtbenchmarks

Alle primären Vergleiche sind gepaart und verwenden exakt dieselben eligible Spiele.

1. **Raw market:** Konsens der eingefrorenen Buchmacher-Whitelist, mit der eingefrorenen
   De-vig- und Aggregationsregel aus demselben T-5-Capture.
2. **Alpha-0:** dieselbe eingefrorene Markt-Temperatur- und Remis-Rekalibrierung wie beim
   Kandidaten, aber `alpha=0`, also ohne Beitrag des Basismodells.

Der Kandidat MUSS beide Benchmarks schlagen. Ein Fallback auf eine andere Buchmachermenge,
`AvgC*` oder eine andere Aggregationsregel ist in der primären Population verboten. Fehlt die
erforderliche Whitelist-Abdeckung, wird der Record vor Kenntnis des Ergebnisses als `ineligible`
markiert und zählt weiterhin gegen die Coverage. Ein vorab benannter Sharp-Book- oder offizieller
Closing-Benchmark darf nur sekundär berichtet werden.

## 7. Retuning und Epoch-Trennung

Eine aktive Lockbox-Epoch ist für Entwicklung gesperrt. Ihre Ergebnisse dürfen weder Auswahl
noch Änderung von Parametern, Features, Grids, Buchmachern, De-vig-Regeln, Cutoff, Filtern,
Ausnahmen oder Gates beeinflussen.

- Forschung und Retuning laufen ausschließlich in einer getrennten Development-Population.
- Jede materielle Änderung erzeugt eine neue Kandidatenversion und eine neue zukünftige Epoch mit
  neuem Manifest. Sie darf niemals rückwirkend auf die alte Epoch gerechnet werden.
- Die alte Version wird bis zum vorab festgelegten Abschluss unverändert weitergeführt und
  separat berichtet.
- Erst nach formellem Abschluss darf eine Lockbox-Epoch zu Developmentdaten herabgestuft werden.
  Die danach entwickelte Version benötigt wiederum eine vollständig neue zukünftige Lockbox.
- Mehrere Varianten dürfen nicht gegeneinander auf derselben aktiven Lockbox ausgewählt werden.

## 8. Metriken und Inferenz

RPS und LogLoss sind ko-primäre Metriken. Für jedes Spiel und jede Benchmark werden die
ungerundeten Scores sowie die ungerundeten gepaarten Differenzen
`Kandidat minus Benchmark` gespeichert. Rundung ist ausschließlich für die Darstellung erlaubt.

Für jede ko-primäre Metrik MUSS eine einseitige 95-%-Obergrenze der mittleren Differenz mit einem
Cluster-Bootstrap berechnet werden:

- mindestens 10.000 Replikate;
- fester, im Manifest gespeicherter Seed;
- Cluster `Liga × Saison × Spieltag`; falls der Spieltag fehlt, wird der vorab definierte
  UTC-Datumsblock verwendet;
- vollständige Cluster werden mit Zurücklegen gezogen;
- Auswertung gegen beide Pflichtbenchmarks und zusätzlich je Liga/Guardrail-Gruppe.

Zwischenergebnisse dürfen deskriptiv angezeigt werden, lösen aber kein Release aus. Es darf nur zu
den im Manifest festgelegten Zeitpunkten formal getestet werden. Häufigeres Freigabe-Peeking ist
nur mit einem vorab festgelegten anytime-validen oder Alpha-Spending-Verfahren erlaubt.

## 9. Gates

### 9.1 Datenintegrität und Coverage

- 100 % der eingeschlossenen Records bestehen Schema-, Hash-, Manifest-, UTC- und
  Pre-Kickoff-Prüfung.
- Es gibt keine unbekannte Modellversion oder Benchmarkquelle.
- Primäre Closing-Coverage beträgt mindestens 98 %.

### 9.2 Stichprobe und Freigabesemantik

- **Diagnostic:** frühestens ab 3.000 gepaarten Spielen insgesamt und mindestens 500 je Liga.
  Dieser Status erlaubt Berichte und Ursachenanalyse, aber keine produktive Übernahme, keine
  Stakes und kein `auto_apply`.
- **Definitive release:** frühestens ab 15.000 gepaarten Spielen insgesamt und mindestens 1.500
  je Liga. Eine frühere definitive Entscheidung ist nur mit dem im Manifest eingefrorenen,
  anytime-validen Verfahren zulässig. Stichprobengröße allein bewirkt keine Freigabe.

Die definitive Schwelle reflektiert die sehr kleine historische Effektgröße; ein kleineres Sample
kann einen deutlich größeren neuen Effekt diagnostisch sichtbar machen, ersetzt aber ohne
vorab festgelegte sequenzielle Inferenz nicht das definitive Gate.

### 9.3 Aggregat- und Liga-Gates

Gegen **jede** der beiden Pflichtbenchmarks müssen gleichzeitig gelten:

- mittlere Differenz RPS kleiner als null;
- mittlere Differenz LogLoss kleiner als null;
- 95-%-Bootstrap-Obergrenze der RPS-Differenz kleiner als null;
- 95-%-Bootstrap-Obergrenze der LogLoss-Differenz kleiner als null.

Mindestens vier der fünf Ligen müssen in der Punktschätzung beide Benchmarks in beiden Metriken
schlagen. In keiner Liga darf die 95-%-Bootstrap-Untergrenze einer RPS- oder
LogLoss-Differenz größer als null sein; eine statistisch klare Verschlechterung blockiert somit die
Freigabe.

### 9.4 Guardrails

Für Remis-Spiele, Spiele mit mindestens einem Aufsteiger und die ersten sechs Spieltage jeder Liga
gelten gegen beide Pflichtbenchmarks:

- 95-%-Obergrenze Delta RPS höchstens `+0,002`;
- 95-%-Obergrenze Delta LogLoss höchstens `+0,01`.

Zu kleine Gruppen werden als `insufficient_data` ausgewiesen und können ein definitives Release
nicht positiv bestätigen. Insbesondere die Remisgruppe ist ein Pflichtguardrail und darf nicht in
einer Gesamtaggregation verborgen werden.

## 10. Integritätsverstöße und Releaseentscheidung

Ein einzelner ungültiger Record wird nicht still repariert oder gelöscht, sondern unveränderlich
als Verstoß markiert. Manifestmutation, Überschreiben eines Forecasts, Hashbruch, Ergebniszugriff
vor Forecast-Freeze, Retuning mit aktiven Lockbox-Ergebnissen, rückwirkende Variantenwahl oder
systematische Zeitstempelverletzungen blockieren die gesamte Epoch für ein definitives Release.

Reine, vorab definierte Record-Ausfälle beeinflussen Coverage und werden transparent berichtet.
Eine Ausnahme nach Kenntnis des Outcomes ist unzulässig. Die Releaseentscheidung ist nur
`definitive_release`, wenn **alle** Integritäts-, Stichproben-, Aggregat-, Benchmark-, Liga- und
Guardrail-Gates gleichzeitig erfüllt sind. Andernfalls bleibt der Status `diagnostic`, `blocked`
oder `insufficient_data`; `auto_apply=false` und Stakes bleiben gesperrt.

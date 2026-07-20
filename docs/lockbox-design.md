# Team-Consilium — Prospektive Club-Lockbox

## Positionen

**Sage (Backend):** Separate append-only Forecast-, Closing- und Result-Artefakte mit
kanonischer Match-ID, UTC-Zeitstempeln, SHA-256 und create-only Semantik. Der bestehende
überschreibbare Shadow-Export ist nur Discovery, kein Beweisartefakt.

**Vega (Quant):** Der Kandidat braucht ein vollständiges eigenes Manifest. Der primäre
Vergleich muss zusätzlich gegen einen `alpha=0`-Marktkalibrator erfolgen, weil nur 306 von
7.082 historischen Zeilen einen echten Modellanteil besitzen. Retuning erzeugt immer eine
neue zukünftige Lockbox-Version.

**Ivy (QA):** Fehlende Closing-Quoten müssen im Coverage-Nenner bleiben. Zufällige
Dateireihenfolge, Exact-Kickoff-Captures, Duplikatkonflikte, Versionswechsel und partielle
Writes müssen fail-closed getestet werden.

## Echte Meinungsverschiedenheiten

1. Sage schlug zunächst den „letzten vollständigen Capture vor Kickoff“ vor; Vega und Ivy
   lehnen die nachträgliche Auswahl als potenzielles Cherry-Picking ab. Entscheidung:
   prospektiv fester Cutoff, standardmäßig T-5 Minuten; ein offizieller späterer Close ist
   nur sekundärer Benchmark.
2. Ein direkt integrierter Live-Lauf wäre schneller sichtbar. Remy begrenzt Sprint 1 auf
   Core, Manifest, Persistenz und Evaluation, weil eine belastbare Club-Modell-/Odds-
   Anbindung noch fehlt. Keine synthetische Live-Edge wird vorgetäuscht.

## Beschluss

Sprint 1 liefert eine eigenständig testbare Lockbox mit unveränderlichen Artefakten,
Versionstrennung, ehrlicher Coverage und blockierenden Prospektiv-Gates. Die Anbindung an
liga-spezifische Odds- und Resultquellen wird vorbereitet, aber nicht mit erfundenen Daten
als live markiert.


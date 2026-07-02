# wm-dashboard — Design-Refresh Diff (Option 1)

## Was ändert sich zum aktuellen `templates/dashboard.html`

Aktueller Style ist bereits solide (Dark-Mode, 12-Spalten-Grid, Fira Code für Zahlen, ARIA-Labels, `prefers-reduced-motion`). Der Refresh ersetzt **nur** die Token-Ebene und trennt Chart-Semantik von Status-Semantik.

| Aspekt | Vorher | Nachher | Warum |
|---|---|---|---|
| Basis-Palette | selbst-gemischtes Grau (`--bg:#0b0c0e`, `--panel:#15171a`) | Financial-Dashboard-Palette (`--bg:#020617`, `--panel:#0E1223`) | tiefere Blau-Grautöne = professioneller Finanz-/Wett-Feel, höherer Kontrast zu Karten |
| Body-Font | Inter | **Fira Sans** | Kohärent zur bereits genutzten Fira-Code-Familie, gleicher Designer, gleiche Metriken |
| Chart-Farben vs. Status-Farben | vermischt (`--m2 = --good = #34d399`) | getrennt (`--m2 = #8B5CF6` Modell, `--good = #22C55E` Trefferbilanz) | vermeidet visuelle Verwechslung „grüne Linie = richtig" |
| Modell-Linien | solid | `stroke-dasharray: 5 5` via `.chart-model` | Konvention aus Predictive Analytics: Prognosen gestrichelt, Ist-Daten solid |
| Confidence-Band | ad-hoc pro Chart | Token `--confidence` + `--confidence-opacity: 0.2` | Ein globales Band-Design für alle MC/Unsicherheits-Plots |
| Table-Header | rollt beim Scrollen | `position: sticky; top: 0` | Bei der langen Cockpit-Tabelle bleibt der Spaltenkopf sichtbar |
| Row-Hover | grau (`rgba(255,255,255,.035)`) | blau-tinted (`rgba(59,130,246,.06)`) + `cursor:pointer` | signalisiert „klickbar, öffnet Detail" |
| Section-Titel | letter-spacing 0 | letter-spacing 0.04em, uppercase | dichte Karten → klare visuelle Trennung Titel/Inhalt |
| KPI-Zahl (`.big`) | Sans | **Mono** | vertikale Ausrichtung im Grid, kein Springen der Ziffernbreite |

## Einbindung (2 Schritte)

**Schritt 1 —** Datei kopieren:
```
deliverables\style.css  →  wm-dashboard\docs\style.css
```

**Schritt 2 —** In `templates/dashboard.html` den Inline-`<style>...</style>`-Block (Zeile 10-102) ersetzen durch:
```html
<link rel="stylesheet" href="style.css">
```

Wenn du das `<style>`-Block-Layout in der Live-Datei `docs/index.html` behalten willst (self-contained), kannst du den Inhalt von `style.css` direkt zwischen die `<style>`-Tags kopieren. Aber besser: separates File + der `export_static`-Runner inlined es beim Build.

## Optionale Chart-Farb-Umstellung (`static/app.js` o.ä.)

Wenn du direkt HEX-Werte in JS für Chart-Farben hast, ersetze:

```js
// alt
const COLORS = { market:'#2f81f7', model:'#34d399', whale:'#fb7185' };

// neu — semantisch klar
const COLORS = {
  market:  getComputedStyle(document.body).getPropertyValue('--m1').trim(),
  model:   getComputedStyle(document.body).getPropertyValue('--m2').trim(),
  whale:   getComputedStyle(document.body).getPropertyValue('--m3').trim(),
  band:    getComputedStyle(document.body).getPropertyValue('--confidence').trim(),
  anomaly: getComputedStyle(document.body).getPropertyValue('--anomaly').trim(),
};

// Modell-Kurve gestrichelt zeichnen
ctx.setLineDash([5, 5]);
```

## Was NICHT geändert wurde

- Kein Umbau der HTML-Struktur (`templates/dashboard.html` bleibt inhaltlich unverändert).
- Kein Umbau von `app.py` / Pipeline / Model-Code — Option 1 ist reine UI-Ebene.
- Kein Neubau der Karten-Anordnung — Tabs (Cockpit / Turnier / Detail / Value / Kalibrierung) bleiben identisch.
- Kein Ersatz der `.tag.live/.historical/.estimated/.unavailable/.cached`-Semantik (die ist schon gut).
- Kein Test-Impact — `pytest quality/test_functional.py tests/test_model.py` bleibt unberührt.

## Preview

Aktuelles `dashboard.html` mit dem neuen CSS-Overlay: bevor du merged, öffne lokal
```
python -m http.server 8080 --directory deliverables
```
und dann `http://localhost:8080/preview-dashboard.html` (falls du eine Preview-Kopie willst — sag Bescheid, dann bau ich die).

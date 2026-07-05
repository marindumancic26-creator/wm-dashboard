# GitHub + Handy-Dashboard - Schritt fuer Schritt

Das Repo ist lokal commit-fertig vorbereitet. `api_keys.json` und `data/`
sind gitignored; das Handy-Dashboard liegt als self-contained HTML in
`docs/index.html`.

## Wichtig: kostenlose GitHub Pages = oeffentliches Repo

Bei einem oeffentlichen Repo kann jeder den Code und die Doku sehen. Nicht
enthalten sind API-Keys und lokale Rohdaten. Optionen:

- Oeffentlich: Code + Analyse-Notizen sichtbar, Pages gratis.
- Privat: GitHub Pages fuer private Repos braucht GitHub Pro.
- Nur Dashboard veroeffentlichen: separates Repo nur mit `docs/`.

## A) Repo auf GitHub anlegen + pushen

1. Auf github.com einloggen -> New repository -> Name z.B. `wm-dashboard`.
2. Ohne README/gitignore anlegen.
3. Im Projektordner:

```powershell
cd "C:\Users\marin\OneDrive\Dokumente\Fußball wahrscheinlichkeit"
git branch -M main
git remote add origin https://github.com/<DEIN-USER>/wm-dashboard.git
git push -u origin main
```

## B) GitHub Pages aktivieren

Repo -> Settings -> Pages -> Build and deployment -> Source: **GitHub Actions**.

Der Workflow `.github/workflows/pages.yml` veroeffentlicht ausschliesslich
`docs/`, laeuft nur bei `docs/**`-Aenderungen und versucht den Pages-Deploy bei
transienten GitHub-Fehlern intern bis zu dreimal, bevor ein Run rot wird.

Nach etwa einer Minute ist das Dashboard erreichbar:

`https://<DEIN-USER>.github.io/wm-dashboard`

## C) Taeglich aktualisieren

Der automatische Runner erzeugt `docs/index.html`, committed und pushed. Der
lokale Pages-Watchdog prueft danach, ob die oeffentliche Seite denselben
`generated_at`-Stand wie `docs/index.html` zeigt.

## Variante: nur das Dashboard veroeffentlichen

Separates Mini-Repo, das ausschliesslich die fertige HTML enthaelt:

```powershell
mkdir "$env:USERPROFILE\wm-dashboard-public"
cd "$env:USERPROFILE\wm-dashboard-public"
copy "C:\Users\marin\OneDrive\Dokumente\Fußball wahrscheinlichkeit\docs\index.html" index.html
git init
git add index.html
git commit -m "dashboard"
git branch -M main
git remote add origin https://github.com/<DEIN-USER>/wm-dashboard-public.git
git push -u origin main
```

Dann Pages-Source = Branch `main`, Ordner `/`.

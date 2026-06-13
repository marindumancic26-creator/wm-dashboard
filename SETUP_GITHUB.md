# GitHub + Handy-Dashboard — Schritt für Schritt

Das Repo ist lokal **commit-fertig** vorbereitet (erster Commit ist gesetzt,
`api_keys.json` ist sicher ausgeschlossen). Du musst nur noch auf GitHub pushen.

## ⚠️ Wichtig: Kostenlose GitHub Pages = ÖFFENTLICHES Repo
Bei einem **öffentlichen** Repo kann jeder den Code + die Doku (`memory/`) sehen.
**Nicht** enthalten sind deine API-Keys (`api_keys.json` ist gitignored) und alle
lokalen Daten (`data/` ist gitignored). Optionen:
- **Öffentlich (gratis):** Code + Analyse-Notizen sind sichtbar. Pages gratis.
- **Privat:** Repo privat lassen — GitHub Pages auf privaten Repos braucht **GitHub Pro**.
- **Nur Dashboard veröffentlichen:** separates Repo nur mit `docs/` (Anleitung unten).

## A) Repo auf GitHub anlegen + pushen
1. Auf github.com einloggen → **New repository** → Name z.B. `wm-dashboard` →
   **ohne** README/gitignore anlegen (haben wir schon) → Create.
2. Im Projektordner (PowerShell):
   ```powershell
   cd "C:\Users\marin\OneDrive\Dokumente\Fußball wahrscheinlichkeit"
   git branch -M main
   git remote add origin https://github.com/<DEIN-USER>/wm-dashboard.git
   git push -u origin main
   ```
   (GitHub fragt beim ersten Push nach Login/Token.)

## B) GitHub Pages aktivieren
Repo → **Settings → Pages → Build and deployment → Source: Deploy from a branch**
→ Branch **main**, Ordner **/docs** → Save.
Nach ~1 Min ist das Dashboard erreichbar unter
`https://<DEIN-USER>.github.io/wm-dashboard` — am Handy öffnen, zum Homescreen.

## C) Täglich aktualisieren
Nach jedem Daily-Run (`run_daily.bat`) wird `docs/index.html` neu erzeugt. Dann:
```powershell
git add docs/index.html
git commit -m "Update dashboard"
git push
```
Optional automatisieren: diese drei Zeilen ans Ende von `run_daily.bat` hängen.

## Variante: nur das Dashboard veröffentlichen (keine Code/Notizen öffentlich)
Separates Mini-Repo, das ausschließlich die fertige HTML enthält:
```powershell
mkdir "$env:USERPROFILE\wm-dashboard-public"; cd "$env:USERPROFILE\wm-dashboard-public"
copy "C:\Users\marin\OneDrive\Dokumente\Fußball wahrscheinlichkeit\docs\index.html" index.html
git init; git add index.html; git commit -m "dashboard"
git branch -M main
git remote add origin https://github.com/<DEIN-USER>/wm-dashboard-public.git
git push -u origin main
```
Dann Pages-Source = Branch main, Ordner **/ (root)**.

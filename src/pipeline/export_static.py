"""Static-Export des Dashboards: self-contained HTML mit inline-Daten.

Erzeugt `docs/index.html` — eine einzige Datei ohne Server, die auf jedem Gerät
(Handy-Browser, GitHub Pages, OneDrive) läuft. Daten + Quotenverlauf werden inline
gebacken; der „Aktualisieren"-Button wird im statischen Modus ausgeblendet.

GitHub Pages (kostenlos, Handy-tauglich):
  1. GitHub-Repo anlegen, `docs/index.html` committen+pushen.
  2. Repo → Settings → Pages → Source: Branch main, Ordner /docs.
  3. URL https://<user>.github.io/<repo> im Handy öffnen (Lesezeichen/Homescreen).
Der lokale Daily-Run regeneriert `docs/index.html`; ein `git push` aktualisiert das Handy.
"""
from __future__ import annotations

import json

from src import config


def _load_dashboard_data() -> dict:
    f = config.DATA_PROCESSED / "dashboard_data.json"
    data = json.loads(f.read_text(encoding="utf-8"))
    extra_f = config.DATA_PROCESSED / "extra_markets.json"
    if extra_f.exists():
        try:
            extra = json.loads(extra_f.read_text(encoding="utf-8"))
            for m in data.get("matches", []):
                if m.get("slug") in extra:
                    m["extra_research"] = extra[m["slug"]]
        except Exception:
            pass
    return data


def _build_odds_history(slugs: set[str]) -> dict:
    hist: dict[str, list] = {s: [] for s in slugs}
    for f in sorted(config.DATA_SNAPSHOTS.glob("*.json")):
        try:
            snap = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        for m in snap.get("matches", []):
            slug = m.get("slug")
            if slug not in hist:
                continue
            ts = (m.get("market") or {}).get("fetched_at") or snap.get("generated_at") or f.stem
            hist[slug].append({"t": ts, "odds": m.get("odds_1x2"),
                               "market": (m.get("market") or {}).get("probs"),
                               "ensemble": (m.get("ensemble") or {}).get("probs")})
    for s in hist:
        hist[s].sort(key=lambda x: x["t"])
    return hist


def _inline_json(obj) -> str:
    """JSON sicher in ein <script>-Tag einbetten: verhindert </script>-Breakout/XSS,
    falls externe Daten (Buchmacher-/Teamnamen, Notizen) HTML-/JS-Sequenzen enthalten.
    \\u003c ist gültiges JSON für '<', bricht das Skript-Tag aber nicht; U+2028/2029
    würden JS-Stringliterale beenden und werden ebenfalls escaped."""
    return (json.dumps(obj, ensure_ascii=False)
            .replace("<", "\\u003c")
            .replace(" ", "\\u2028")
            .replace(" ", "\\u2029"))


def export(out_path=None):
    out_path = out_path or (config.PROJECT_ROOT / "docs" / "index.html")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    template = (config.PROJECT_ROOT / "templates" / "dashboard.html").read_text(encoding="utf-8")
    data = _load_dashboard_data()
    slugs = {m["slug"] for m in data.get("matches", []) if m.get("slug")}
    odds = _build_odds_history(slugs)

    inject = ("<script>window.__STATIC_DATA__=" + _inline_json(data)
              + ";window.__STATIC_ODDS__=" + _inline_json(odds) + ";</script>")
    html = template.replace("<body>", "<body>\n" + inject, 1)
    out_path.write_text(html, encoding="utf-8")
    return out_path


if __name__ == "__main__":
    p = export()
    print(f"Static-Dashboard exportiert: {p} ({p.stat().st_size // 1024} KB)")

"""Lokales Dashboard fuer WM-Prognosen.

Start:  python app.py   ->  http://127.0.0.1:5050
Daten:  data/processed/dashboard_data.json (erzeugt vom Daily Run).
/api/refresh stoesst einen neuen Pipeline-Lauf an (synchron, dauert ~1-2 min).
"""
import json
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from src import config

app = Flask(__name__)
# Template-Aenderungen sofort ausliefern (kein Server-Neustart noetig fuer dashboard.html)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.jinja_env.auto_reload = True


def _load_data():
    f = config.DATA_PROCESSED / "dashboard_data.json"
    if not f.exists():
        return None
    data = json.loads(f.read_text(encoding="utf-8"))
    # On-Demand recherchierte Zusatzmarkt-Quoten (BTTS/Handicap/DC/DNB) einblenden.
    # Wird von Claude bei Web-Recherche/Screenshot-Eingabe gepflegt; bewusst getrennt
    # vom automatischen Pipeline-Output, da Quellen ungeprueft/manuell sein koennen.
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


@app.route("/")
def index():
    return render_template("dashboard.html")


@app.route("/api/dashboard-data")
def dashboard_data():
    data = _load_data()
    if data is None:
        return jsonify({"error": "Noch kein Daily Run. Bitte ausfuehren: python -m src.pipeline.daily_matchday_run"}), 404
    return jsonify(data)


@app.route("/api/odds-history")
def odds_history():
    """Zeitreihe der besten 1X2-Quoten + Markt-/Ensemble-Wahrscheinlichkeiten je Spiel
    über alle Snapshots (für Quotenverlauf/Line-Movement-Charts)."""
    slug = request.args.get("slug", "")
    series = []
    for f in sorted(config.DATA_SNAPSHOTS.glob("*.json")):
        try:
            snap = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        for m in snap.get("matches", []):
            if m.get("slug") != slug:
                continue
            ts = (m.get("market") or {}).get("fetched_at") or snap.get("generated_at") or f.stem
            series.append({
                "t": ts,
                "odds": m.get("odds_1x2"),
                "market": (m.get("market") or {}).get("probs"),
                "ensemble": (m.get("ensemble") or {}).get("probs"),
            })
    series.sort(key=lambda x: x["t"])
    return jsonify({"slug": slug, "series": series, "n": len(series)})


@app.route("/api/refresh", methods=["POST"])
def refresh():
    from src.pipeline import daily_matchday_run
    skip_whales = request.args.get("skip_whales") == "1"
    payload = daily_matchday_run.run(skip_whales=skip_whales)
    return jsonify({"ok": True, "matches": len(payload["matches"])})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, debug=False)

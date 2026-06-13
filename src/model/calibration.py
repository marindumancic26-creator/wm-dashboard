"""Kalibrierungs- & Wett-Tracking: eigene Prognosen gegen offizielle Ergebnisse.

Pro aufgeloestem Spiel und je Quelle:
  - Brier   = sum_i (p_i - o_i)^2            (0=perfekt, 0.667=Gleichvert., 2=max falsch)
  - LogLoss = -ln(p_actual)                  (0=perfekt, 1.099=Gleichvert.; bestraft Sicherheit)
  - Hit     = 1 wenn argmax(p) == Ergebnis   (Trefferquote)

Wett-Kennzahlen (Referenz-Policy: 1 Einheit flat auf den Ensemble-Favoriten zur
besten verfuegbaren 1X2-Quote):
  - ROI     = (Summe Auszahlung - Summe Einsatz) / Summe Einsatz
  - CLV     = Closing Line Value: bewegte sich der Markt zwischen Opening- und
              Closing-Snapshot in Richtung unserer Modell-Lehne (Prozessguete VOR
              Ergebnis), und schlug die Opening-Quote die Closing-Quote?

Leakage-Schutz: nur Snapshots VOR Anpfiff. Opening = frueheste, Closing = letzte
gueltige Prognose. CLV wird aussagekraeftig, sobald der Daily-Run Tage im Voraus laeuft.
"""
from __future__ import annotations

import datetime as dt
import json
import math

from src import config

OUTCOMES = ("team1_win", "draw", "team2_win")
SOURCES = ("market", "books", "kalshi", "model", "whale", "ensemble")


def _team_eq(a: str, b: str) -> bool:
    ca = config.canonical_team(a).lower()
    cb = config.canonical_team(b).lower()
    return ca == cb or ca in cb or cb in ca


def _date_close(d1: str, d2: str, days: int = 1) -> bool:
    try:
        a = dt.date.fromisoformat(d1[:10])
        b = dt.date.fromisoformat(d2[:10])
        return abs((a - b).days) <= days
    except Exception:
        return d1 == d2


def brier(probs: dict, outcome: str) -> float:
    return sum((probs.get(o, 0.0) - (1.0 if o == outcome else 0.0)) ** 2 for o in OUTCOMES)


def log_loss(probs: dict, outcome: str) -> float:
    p = max(min(probs.get(outcome, 0.0), 1.0), 1e-9)
    return -math.log(p)


def argmax_outcome(probs: dict) -> str:
    return max(OUTCOMES, key=lambda o: probs.get(o, 0.0))


def _all_forecasts() -> dict:
    """Pro Spiel-Slug ALLE Prognose-Staende (chronologisch), inkl. 1X2-Bestquoten."""
    forecasts: dict[str, list] = {}
    for f in sorted(config.DATA_SNAPSHOTS.glob("*.json")):
        try:
            snap = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        for m in snap.get("matches", []):
            entry = {"snapshot_date": f.stem,
                     "generated_at": snap.get("generated_at", f.stem),
                     "model_version": snap.get("config", {}).get("model_version"),
                     "team1": m["team1"], "team2": m["team2"],
                     "date": m["date"], "sources": {}, "odds_1x2": m.get("odds_1x2")}
            if m.get("market"):
                entry["sources"]["market"] = m["market"]["probs"]
                entry["generated_at"] = m["market"].get("fetched_at", entry["generated_at"])
            if m.get("books") and m["books"].get("probs"):
                entry["sources"]["books"] = m["books"]["probs"]
            if m.get("kalshi") and m["kalshi"].get("probs"):
                entry["sources"]["kalshi"] = m["kalshi"]["probs"]
            if m.get("model"):
                entry["sources"]["model"] = m["model"]["probs"]
            if m.get("whale") and m["whale"].get("probs"):
                entry["sources"]["whale"] = m["whale"]["probs"]
            if m.get("ensemble") and m["ensemble"].get("probs"):
                entry["sources"]["ensemble"] = m["ensemble"]["probs"]
            forecasts.setdefault(m["slug"], []).append(entry)
    return forecasts


def _to_utc(local_iso: str):
    try:
        return dt.datetime.fromisoformat(local_iso).astimezone(dt.timezone.utc)
    except Exception:
        return None


def _parse_kickoff(utc_iso: str):
    try:
        return dt.datetime.fromisoformat(utc_iso.replace("Z", "+00:00"))
    except Exception:
        return None


def _clv(fc_open: dict, fc_close: dict, pick: str) -> dict:
    """Closing Line Value fuer die gewettete Auswahl (Ensemble-Favorit).
    model_beat_close: bewegte sich der Markt in Richtung unserer Opening-Modell-Lehne?
    clv_odds: Opening-Bestquote / Closing-Bestquote - 1 (positiv = wir haetten besser gekauft)."""
    out = {"model_beat_close": None, "clv_odds": None}
    mo = fc_open["sources"].get("market") or fc_open["sources"].get("books")
    mc = fc_close["sources"].get("market") or fc_close["sources"].get("books")
    md = fc_open["sources"].get("model")
    if mo and mc and md:
        lean = md.get(pick, 0) - mo.get(pick, 0)   # unsere Edge-Richtung beim Opening
        move = mc.get(pick, 0) - mo.get(pick, 0)   # tatsaechliche Marktbewegung
        if abs(move) > 1e-6 and abs(lean) > 1e-6:
            out["model_beat_close"] = (lean * move > 0)
    oo, co = fc_open.get("odds_1x2"), fc_close.get("odds_1x2")
    if oo and co and oo.get(pick) and co.get(pick):
        out["clv_odds"] = round(oo[pick] / co[pick] - 1.0, 4)
    return out


def evaluate(results: dict) -> dict:
    if results.get("status") != "live":
        return {"status": "unavailable", "note": results.get("note", ""), "matches": [],
                "summary": {}, "betting": {}}

    forecasts = _all_forecasts()
    rows = []
    for slug, entries in forecasts.items():
        fc0 = entries[0]
        res = next((r for r in results["results"]
                    if _date_close(r["date"], fc0["date"])
                    and ((_team_eq(fc0["team1"], r["home"]) and _team_eq(fc0["team2"], r["away"])) or
                         (_team_eq(fc0["team1"], r["away"]) and _team_eq(fc0["team2"], r["home"])))), None)
        if not res:
            continue

        kickoff = _parse_kickoff(res.get("kickoff_utc") or "")
        valid = entries
        if kickoff:
            valid = [e for e in entries if (_to_utc(e["generated_at"]) or kickoff) < kickoff]
        if not valid:
            continue
        fc_open, fc = valid[0], valid[-1]  # Opening + Closing (letzter Pre-Kickoff)

        flipped = _team_eq(fc["team1"], res["away"])
        hg, ag = res["home_goals"], res["away_goals"]
        g1, g2 = (ag, hg) if flipped else (hg, ag)
        outcome = "team1_win" if g1 > g2 else ("team2_win" if g2 > g1 else "draw")

        row = {"slug": slug, "result": f"{g1}:{g2}", "outcome": outcome,
               "snapshot_date": fc["snapshot_date"], "forecast_at": fc["generated_at"],
               "model_version": fc.get("model_version"),
               "brier": {}, "log_loss": {}, "hit": {}}
        for src, probs in fc["sources"].items():
            row["brier"][src] = round(brier(probs, outcome), 4)
            row["log_loss"][src] = round(log_loss(probs, outcome), 4)
            row["hit"][src] = int(argmax_outcome(probs) == outcome)

        # Referenz-Wett-Policy: 1 Einheit flat auf Ensemble-Favorit zur besten Quote
        ens = fc["sources"].get("ensemble")
        if ens:
            pick = argmax_outcome(ens)
            row["pick"] = pick
            odds = (fc.get("odds_1x2") or {}).get(pick)
            if odds:
                won = (pick == outcome)
                row["bet"] = {"pick": pick, "odds": odds, "won": won,
                              "profit": round((odds - 1.0) if won else -1.0, 4)}
            row["clv"] = _clv(fc_open, fc, pick)
        rows.append(row)

    # --- Quellen-Summary: Brier, LogLoss, Hit-Rate ---
    summary = {}
    for src in SOURCES:
        b = [r["brier"][src] for r in rows if src in r["brier"]]
        if b:
            ll = [r["log_loss"][src] for r in rows if src in r["log_loss"]]
            h = [r["hit"][src] for r in rows if src in r["hit"]]
            summary[src] = {"mean_brier": round(sum(b) / len(b), 4),
                            "mean_log_loss": round(sum(ll) / len(ll), 4),
                            "hit_rate": round(sum(h) / len(h), 4), "n": len(b)}

    # --- Wett-Summary: ROI + CLV ---
    bets = [r["bet"] for r in rows if r.get("bet")]
    clvs = [r["clv"]["clv_odds"] for r in rows if r.get("clv") and r["clv"]["clv_odds"] is not None]
    beats = [r["clv"]["model_beat_close"] for r in rows
             if r.get("clv") and r["clv"]["model_beat_close"] is not None]
    betting = {"policy": "1 Einheit flat auf Ensemble-Favorit @ beste 1X2-Quote",
               "n_bets": len(bets)}
    if bets:
        profit = sum(b["profit"] for b in bets)
        betting["roi"] = round(profit / len(bets), 4)
        betting["hit_rate"] = round(sum(1 for b in bets if b["won"]) / len(bets), 4)
    if clvs:
        betting["avg_clv_odds"] = round(sum(clvs) / len(clvs), 4)
    if beats:
        betting["beat_close_rate"] = round(sum(1 for x in beats if x) / len(beats), 4)
        betting["n_clv"] = len(beats)

    return {"status": "live", "n_resolved": len(rows), "matches": rows,
            "summary": summary, "betting": betting,
            "note": "Brier 0=perfekt/0.667=Zufall; LogLoss 0=perfekt/1.099=Zufall. "
                    "ROI/CLV: Referenz-Policy auf Ensemble-Favorit, letzter Pre-Kickoff-Snapshot."}

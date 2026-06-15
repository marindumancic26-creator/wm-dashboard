"""Transparentes Ensemble: Polymarket-Preis + Elo/StatsBomb-Modell + Whale-Signal.

Gewichte sind konfigurierbar (config.ENSEMBLE_WEIGHTS) und werden im Dashboard
pro Quelle offengelegt. Faellt eine Quelle aus, werden die Gewichte renormalisiert.
Whale-Signal wird zusaetzlich mit seiner eigenen Daten-Konfidenz gedaempft.
"""
from __future__ import annotations

from src import config
from src.model import features


def blend_probs(market: dict | None, model: dict | None, whale: dict | None,
                weights: dict | None = None, books: dict | None = None,
                kalshi: dict | None = None) -> dict:
    weights = dict(weights or config.ENSEMBLE_WEIGHTS)
    sources = {}
    if market and market.get("probs"):
        sources["market"] = market["probs"]
    if books and books.get("probs"):
        sources["books"] = books["probs"]
    if kalshi and kalshi.get("probs"):
        sources["kalshi"] = kalshi["probs"]
    if model and model.get("probs"):
        sources["model"] = model["probs"]
    if whale and whale.get("probs"):
        # Whale-Gewicht zusaetzlich nach Stichprobe daempfen
        n = whale.get("n_wallets_scored", 0)
        damp = min(1.0, n / 8)
        avg_conf = 0.0
        if whale.get("wallets"):
            avg_conf = sum(w["confidence"] for w in whale["wallets"]) / len(whale["wallets"])
        weights["whale"] = weights.get("whale", config.ENSEMBLE_WEIGHTS["whale"]) * damp * (0.5 + 0.5 * avg_conf)
        sources["whale"] = whale["probs"]

    active = {k: weights[k] for k in sources if weights.get(k, 0) > 0}
    wsum = sum(active.values())
    if not active or wsum == 0:
        return {"probs": None, "weights_used": {}, "note": "keine Quelle verfuegbar"}
    active = {k: v / wsum for k, v in active.items()}

    OUTCOMES = ("team1_win", "draw", "team2_win")
    blended = {o: sum(active[s] * sources[s][o] for s in active) for o in OUTCOMES}
    s = sum(blended.values())
    blended = {k: v / s for k, v in blended.items()}

    # Whale-Gate: ein einzelnes Extremsignal (hochvariant, unvalidiert) darf den Blend
    # um max. WHALE_SHIFT_CAP gegenueber dem Blend OHNE Whale verschieben. Begrenzt die
    # Whale-getriebenen Schein-Edges, ohne die Basisgewichte zu retunen.
    WHALE_SHIFT_CAP = 0.08
    if "whale" in active and len(active) > 1:
        nw = {k: v for k, v in active.items() if k != "whale"}
        z = sum(nw.values()) or 1.0
        nw = {k: v / z for k, v in nw.items()}
        base = {o: sum(nw[k] * sources[k][o] for k in nw) for o in OUTCOMES}
        bs = sum(base.values()) or 1.0
        base = {k: v / bs for k, v in base.items()}
        # Delta (Whale-Effekt) summiert zu 0 -> skaliertes base+alpha*delta bleibt normiert
        delta = {o: blended[o] - base[o] for o in OUTCOMES}
        maxabs = max(abs(d) for d in delta.values())
        if maxabs > WHALE_SHIFT_CAP:
            alpha = WHALE_SHIFT_CAP / maxabs
            blended = {o: base[o] + alpha * delta[o] for o in OUTCOMES}

    blended = {k: round(v, 4) for k, v in blended.items()}
    return {"probs": blended, "weights_used": {k: round(v, 3) for k, v in active.items()},
            "sources": {k: {o: round(p, 4) for o, p in v.items()} for k, v in sources.items()}}


def blend_lambdas(market: dict | None, model: dict | None, weights_used: dict,
                  books: dict | None = None, kalshi: dict | None = None) -> dict:
    """Tor-Erwartungswerte des Ensembles: gewichtetes Mittel aus markt-impliziten
    und modellbasierten lambdas (Whale liefert keine eigene Torstruktur —
    sein Gewicht fliesst anteilig dem Markt zu, da beide preisbasiert sind).

    Die preis-implizite Torstruktur stammt aus der besten verfuegbaren Preisquelle:
    Polymarket-Markt > Buchmacher > Kalshi. Damit folgt die MC-Torverteilung denselben
    Quellen, die auch blend_probs treiben — auch wenn Polymarket fuer ein Spiel fehlt."""
    cands = {}
    price_src = None
    if market and market.get("probs"):
        price_src = market["probs"]
    elif books and books.get("probs"):
        price_src = books["probs"]
    elif kalshi and kalshi.get("probs"):
        price_src = kalshi["probs"]
    if price_src:
        mi = features.market_implied_lambdas(price_src["team1_win"],
                                             price_src["draw"],
                                             price_src["team2_win"])
        cands["market"] = (mi["lambda1"], mi["lambda2"], mi)
    if model:
        cands["model"] = (model["lambda1"], model["lambda2"], None)

    if not cands:
        return {"lambda1": 1.3, "lambda2": 1.3, "note": "Fallback-Baseline"}

    # books/kalshi/whale liefern keine eigene Torstruktur — preisbasiert, daher dem Markt-λ zugeschlagen
    w_market = (weights_used.get("market", 0) + weights_used.get("whale", 0)
                + weights_used.get("books", 0) + weights_used.get("kalshi", 0))
    w_model = weights_used.get("model", 0)
    parts = []
    if "market" in cands:
        parts.append((w_market, cands["market"]))
    if "model" in cands:
        parts.append((w_model, cands["model"]))
    wsum = sum(p[0] for p in parts) or 1.0

    lam1 = sum(w * c[0] for w, c in parts) / wsum
    lam2 = sum(w * c[1] for w, c in parts) / wsum
    out = {"lambda1": round(lam1, 3), "lambda2": round(lam2, 3)}
    if "market" in cands and cands["market"][2]:
        out["market_implied"] = cands["market"][2]
    return out

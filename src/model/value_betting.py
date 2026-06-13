"""Expected-Value- und Value-Bet-Engine auf Basis ECHTER Buchmacher-Quoten.

Quellen-Trennung (bewusst sauber gehalten):
  - "best_odds": beste real angebotene Quote ueber alle Buecher (Line-Shopping)
  - "consensus_prob": scharfer entvigter Marktkonsens (Pinnacle bevorzugt) — KEINE Quote,
    sondern die faire Markt-Wahrscheinlichkeit ohne Marge
  - "p_model": unsere Modell-/Ensemble-/Monte-Carlo-Wahrscheinlichkeit
  - "p_cons": konservative Untergrenze (bewusst vorsichtig, s.u.)

EV = p_cons * best_odds - 1   |   Break-even = 1 / best_odds
Value nur wenn p_cons > Break-even (also EV > 0).

Konservative Untergrenze: Anker ist das MINIMUM aus Modell- und scharfer
Marktwahrscheinlichkeit (Maerkte sind effizient — wir trauen uns nicht ueber den
scharfen Konsens hinaus), minus ein Sicherheitsabschlag nach Unsicherheitsstufe:
  low -3pp, medium -6pp, high -10pp. Das deckt kleine Datenbasis, Rotation,
Verletzungen, Motivation, Wetter, Marktbewegungen und Modellfehler defensiv ab.

Nur Maerkte mit echten Live-Quoten werden bewertet: 1X2 und Over/Under (Totals).
Fuer Maerkte ohne abgerufene Quote (BTTS, Handicap, DNB, Doppelte Chance) liefern
wir hoechstens eine modell-faire Referenzquote, aber KEINE Value-Empfehlung.
"""
from __future__ import annotations

HAIRCUT = {"low": 0.03, "medium": 0.06, "high": 0.10}
STAKE_CAP = {"low": 0.020, "medium": 0.015, "high": 0.0075}  # max % Bankroll
KELLY_FRACTION = 0.25  # Viertel-Kelly (defensiv)


SIGMA_FLOOR = 0.03   # Grundunsicherheit, selbst bei perfekter Datenlage
Z = 0.8              # Risikoaversion: untere Konfidenzgrenze p_sharp - Z*sigma
MIN_BOOKS = 3        # Liquiditaets-Gate: weniger Buecher -> keine Value-Empfehlung


def estimate_sigma(band_width: float | None, disagreement: float) -> float:
    """Unsicherheit der Wahrscheinlichkeit aus MC-Bandbreite (90%-Intervall -> sigma),
    Markt-Modell-Diskrepanz und Grundunsicherheit. Quadratische Summe."""
    bw = (band_width / 3.29) if band_width is not None else 0.05  # 90%-Intervall = 3.29*sigma
    return (bw ** 2 + (0.4 * disagreement) ** 2 + SIGMA_FLOOR ** 2) ** 0.5


def _tier_from_sigma(sigma: float, n_books: int) -> str:
    if n_books < 5 or sigma > 0.12:
        return "high"
    if sigma < 0.06:
        return "low"
    return "medium"


def conservative_prob(p_model: float, p_market: float | None, sigma: float) -> float:
    """Untere Konfidenzgrenze: Anker (min aus Modell/scharfem Markt) minus Z*sigma.
    Skaliert mit echter Unsicherheit statt fixem pp-Abschlag."""
    anchor = min(p_model, p_market) if p_market is not None else p_model
    return max(0.01, round(anchor - Z * sigma, 4))


def _stake_pct(ev: float, odds: float, p_cons: float, tier: str) -> float:
    """Viertel-Kelly, gekappt nach Unsicherheitsstufe. 0 wenn kein Value."""
    if ev <= 0 or odds <= 1.0:
        return 0.0
    kelly = (p_cons * odds - 1.0) / (odds - 1.0)  # voller Kelly-Anteil
    stake = max(0.0, KELLY_FRACTION * kelly)
    return round(min(stake, STAKE_CAP[tier]) * 100, 2)  # in % Bankroll


def _row(market, selection, odds, book, p_model, p_market, band_width, n_books):
    if not odds or odds <= 1.0:
        return None
    disagreement = abs(p_model - p_market) if p_market is not None else 0.0
    sigma = estimate_sigma(band_width, disagreement)
    tier = _tier_from_sigma(sigma, n_books)
    p_cons = conservative_prob(p_model, p_market, sigma)
    breakeven = 1.0 / odds
    ev = p_cons * odds - 1.0
    liquid = n_books >= MIN_BOOKS    # Liquiditaets-Gate
    return {
        "market": market, "selection": selection,
        "best_odds": round(odds, 3), "book": book,
        "breakeven_prob": round(breakeven, 4),
        "p_model": round(p_model, 4),
        "p_market_consensus": round(p_market, 4) if p_market is not None else None,
        "p_conservative": p_cons,
        "sigma": round(sigma, 4), "n_books": n_books,
        "ev": round(ev, 4),
        "ev_at_model": round(p_model * odds - 1.0, 4),
        "is_value": (p_cons > breakeven) and liquid,
        "risk": tier,
        "stake_pct": _stake_pct(ev, odds, p_cons, tier) if liquid else 0.0,
    }


def evaluate_match(match: dict, best_prices: dict | None) -> dict:
    """match = Pipeline-Match-Dict (mit ensemble, model, monte_carlo, books-Status,
    tournament_form). best_prices = odds_client.best_prices_for_match(...)."""
    t1, t2 = match["team1"], match["team2"]
    out = {"team1": t1, "team2": t2, "rows": [], "value_bets": [],
           "n_bookmakers": best_prices.get("n_bookmakers") if best_prices else 0,
           "books": best_prices.get("books", []) if best_prices else [],
           "has_live_odds": bool(best_prices)}
    if not best_prices:
        out["note"] = "Keine Live-Buchmacherquoten gefunden (Spiel evtl. ausserhalb Markt)."
        return out

    ens = match["ensemble"]["probs"]
    mc = match["monte_carlo"]
    band = match["monte_carlo"]["uncertainty"]
    form = match.get("model", {}).get("tournament_form")
    sb_status = match.get("model", {}).get("statsbomb_status", "unavailable")
    data_thin = (sb_status == "unavailable") and not form

    label = {"team1_win": f"Sieg {t1}", "draw": "Unentschieden", "team2_win": f"Sieg {t2}"}
    rows = []

    # ---- 1X2 ----
    for sel in ("team1_win", "draw", "team2_win"):
        info = best_prices["h2h"].get(sel)
        if not info:
            continue
        p_model = ens[sel]
        p_market = info["consensus_prob"]
        bw = band[sel]["p95"] - band[sel]["p05"]
        r = _row("1X2", label[sel], info["best_odds"], info["book"], p_model, p_market,
                 bw, info.get("n_books", 0))
        if r:
            rows.append(r)

    # ---- Doppelte Chance & Draw-No-Bet (aus 1X2-Bestquoten abgeleitet, faire Referenz) ----
    # Hinweis: KEINE eigenen Live-Quoten -> als Referenz markiert, nicht fuer Value-Liste.
    dc_refs = _derived_refs(best_prices["h2h"], ens, label, t1, t2)
    out["derived_reference"] = dc_refs

    # ---- Over/Under Tore (Totals) ----
    n_form = 0
    if form:
        n_form = max((f.get("matches", 0) for f in form.values()), default=0)
    total_dist = mc["total_goals_dist"]  # 0..8, 9+
    for line, slot in sorted(best_prices.get("totals", {}).items(), key=lambda kv: float(kv[0])):
        try:
            ln = float(line)
        except ValueError:
            continue
        # P(Over ln) aus MC-Gesamttorverteilung
        floor = int(ln)  # z.B. 2.5 -> over = total >= 3 = 1 - P(0..2)
        p_over = round(1.0 - sum(total_dist[: floor + 1]), 4)
        p_under = round(1.0 - p_over, 4)
        for nm, p_model, info in (("Over %.1f" % ln, p_over, slot["over"]),
                                  ("Under %.1f" % ln, p_under, slot["under"])):
            # Totals ohne MC-Band -> band_width None (estimate_sigma nutzt Default)
            r = _row("Über/Unter", nm, info["best_odds"], info["book"], p_model,
                     info["consensus_prob"], None, info.get("n_books", 0))
            if r:
                rows.append(r)

    out["rows"] = rows
    out["value_bets"] = sorted([r for r in rows if r["is_value"]],
                               key=lambda r: -r["ev"])[:4]

    # Modell-Fairquoten fuer Zusatzmaerkte ohne Live-API-Quote (BTTS/DC/DNB).
    # Reine Orientierung — echte EV nur mit recherchierten/gelieferten Quoten.
    btts = mc["events"]["btts"]
    model_markets = [
        {"market": "BTTS", "selection": "Beide treffen: Ja", "p_model": round(btts, 4),
         "fair_odds": round(1.0 / btts, 3) if btts else None},
        {"market": "BTTS", "selection": "Beide treffen: Nein", "p_model": round(1 - btts, 4),
         "fair_odds": round(1.0 / (1 - btts), 3) if btts < 1 else None},
    ]
    for r in dc_refs:
        model_markets.append({"market": "DC/DNB", "selection": r["selection"],
                              "p_model": r["p_model"], "fair_odds": r["fair_odds"]})
    out["model_markets"] = model_markets
    return out


def _derived_refs(h2h: dict, ens: dict, label: dict, t1: str, t2: str) -> list:
    """Modell-faire Referenzquoten fuer Doppelte Chance / DNB — OHNE Live-Marktquote,
    daher nur als Orientierung, nicht fuer EV-Empfehlungen."""
    refs = []
    p1, pd, p2 = ens["team1_win"], ens["draw"], ens["team2_win"]
    combos = [
        (f"Doppelte Chance {t1}/X", p1 + pd),
        (f"Doppelte Chance {t2}/X", p2 + pd),
        (f"Doppelte Chance {t1}/{t2}", p1 + p2),
        (f"DNB {t1}", p1 / (p1 + p2) if (p1 + p2) else None),
        (f"DNB {t2}", p2 / (p1 + p2) if (p1 + p2) else None),
    ]
    for name, p in combos:
        if p:
            refs.append({"selection": name, "p_model": round(p, 4),
                         "fair_odds": round(1.0 / p, 3),
                         "note": "Modell-faire Quote, keine Live-Marktquote abgerufen"})
    return refs


def apply_quality_gate(value: dict, dq: dict) -> dict:
    """Skaliert Einsaetze mit dem Datenqualitaets-Multiplikator und unterdrueckt
    Value-Flags bei roter Ampel (zu duenne Datenlage fuer eine Wette)."""
    mult = dq.get("stake_multiplier", 1.0)
    tier = dq.get("tier", "amber")
    for r in value.get("rows", []):
        r["stake_pct"] = round(r["stake_pct"] * mult, 2)
        if tier == "red":
            r["is_value"] = False  # rote Ampel: keine Empfehlung
    if tier == "red":
        value["value_bets"] = []
        value["gate_note"] = "Value-Flags unterdrückt (Datenqualität rot)."
    else:
        value["value_bets"] = [r for r in value.get("value_bets", []) if r.get("is_value")]
        for r in value["value_bets"]:
            r["stake_pct"] = round(r["stake_pct"] * mult, 2)
    value["data_quality_tier"] = tier
    return value


PER_MATCH_CAP = 2.0   # % Bankroll je Spiel (Ausgänge im selben Spiel sind korreliert)
PORTFOLIO_CAP = 6.0   # % Bankroll gesamt


def portfolio(value_bets_all: list, bankroll_note: bool = True) -> dict:
    """Aggregierte Einsatzverteilung. Korrelations-Cap pro Spiel + Gesamt-Cap.

    Mehrere Value-Wetten im selben Spiel sind stark korreliert (gleiches Resultat
    treibt sie gemeinsam) → pro Spiel wird die Summe auf PER_MATCH_CAP gedeckelt,
    danach die Gesamtexposure auf PORTFOLIO_CAP (Kapitalerhalt, keine Klumpen)."""
    bets = sorted(value_bets_all, key=lambda r: -r["ev"])
    per_match: dict[str, float] = {}
    for b in bets:
        s = b.get("slug", "?")
        used = per_match.get(s, 0.0)
        b["_corr"] = round(max(0.0, min(b["stake_pct"], PER_MATCH_CAP - used)), 2)
        per_match[s] = used + b["_corr"]
    total = sum(b["_corr"] for b in bets)
    scale = min(1.0, PORTFOLIO_CAP / total) if total > PORTFOLIO_CAP else 1.0
    plan = [{**b, "stake_pct_final": round(b["_corr"] * scale, 2)} for b in bets]
    return {"n_value_bets": len(bets), "total_stake_pct": round(total * scale, 2),
            "scaled_down": scale < 1.0, "per_match_capped": any(v >= PER_MATCH_CAP for v in per_match.values()),
            "plan": plan}

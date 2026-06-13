"""Datenqualitaets-Score je Spiel — Composite aus vorhandenen Status-Signalen.

Gibt 0..1 + Ampel (green/amber/red) + nachvollziehbare Faktoren. Wird genutzt, um
Einsaetze zu skalieren und Value-Flags bei duenner Lage zu unterdruecken. Kein neues
Datenholen — nur Aggregation dessen, was die Pipeline ohnehin liefert.
"""
from __future__ import annotations

import statistics

# Gewichte der Teilfaktoren (Summe 1.0)
WEIGHTS = {"elo": 0.10, "statsbomb": 0.20, "form": 0.20,
           "liquidity": 0.25, "market_agreement": 0.25}


def _liquidity_factor(value: dict | None) -> tuple[float, str]:
    if not value or not value.get("has_live_odds"):
        return 0.2, "keine Live-Quoten"
    n = value.get("n_bookmakers", 0)
    f = min(1.0, n / 20.0)  # >=20 Buecher -> volle Punktzahl
    return f, f"{n} Buchmacher"


def _market_agreement(match: dict) -> tuple[float, str]:
    """Niedrige Dispersion zwischen Markt/Buecher/Kalshi = hohe Qualitaet."""
    probs = []
    for src in ("market", "books", "kalshi"):
        s = match.get(src)
        if s and s.get("probs"):
            probs.append(s["probs"]["team1_win"])
    if len(probs) < 2:
        return 0.5, "nur 1 Marktquelle"
    disp = statistics.pstdev(probs)  # 0 = perfekte Einigkeit
    f = max(0.0, 1.0 - disp / 0.10)  # 10pp Streuung -> 0
    return f, f"Dispersion {disp*100:.1f}pp ueber {len(probs)} Quellen"


def score_match(match: dict) -> dict:
    factors, reasons = {}, []

    elo_status = (match.get("model", {}).get("elo", {}) or {}).get("status", "estimated")
    factors["elo"] = 1.0 if elo_status == "live" else 0.6
    reasons.append(f"Elo {elo_status}")

    sb = match.get("model", {}).get("statsbomb_status", "unavailable")
    factors["statsbomb"] = {"live": 1.0, "historical": 0.7}.get(sb, 0.3)
    reasons.append(f"StatsBomb {sb}")

    form = match.get("model", {}).get("tournament_form")
    n_form = max((f.get("matches", 0) for f in form.values()), default=0) if form else 0
    factors["form"] = min(1.0, n_form / 3.0)
    reasons.append(f"Form {n_form} Sp.")

    lf, lr = _liquidity_factor(match.get("value"))
    factors["liquidity"] = lf
    reasons.append(lr)

    mf, mr = _market_agreement(match)
    factors["market_agreement"] = mf
    reasons.append(mr)

    score = round(sum(WEIGHTS[k] * factors[k] for k in WEIGHTS), 4)
    tier = "green" if score >= 0.70 else ("amber" if score >= 0.45 else "red")
    # Einsatz-Multiplikator: red drosselt hart, amber moderat
    stake_mult = {"green": 1.0, "amber": 0.5, "red": 0.0}[tier]
    return {"score": score, "tier": tier, "stake_multiplier": stake_mult,
            "factors": {k: round(v, 3) for k, v in factors.items()},
            "reasons": reasons}

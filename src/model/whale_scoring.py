"""Whale-Scoring auf Basis oeffentlicher Polymarket-Daten.

WICHTIGE EINSCHRAENKUNG (dokumentiert, siehe memory/data_sources.md):
Polymarket stellt KEINE saubere oeffentliche Pro-Nutzer-Erfolgshistorie mit
aufgeloesten Maerkten, Brier Score oder Closing-Line-Value bereit. Oeffentlich
verfuegbar sind: Trades pro Markt, Top-Holder pro Markt und die Activity-Historie
einzelner Wallets (Trades/Redeems). REDEEM-Eintraege entstehen nur bei
gewonnenen Positionen -> daraus laesst sich eine HEURISTISCHE Erfolgsquote
ableiten. Alle Scores hier sind daher heuristisch, nicht audit-fest.

Defensive Gewichtung: Shrinkage n/(n+K) gegen einen neutralen Prior, damit
Wallets mit wenigen Glueckstreffern nicht ueber konsistente Vieltrader steigen.
"""
from __future__ import annotations

import datetime as dt
import time

from src import config
from src.data_sources import polymarket_client as pm

FOOTBALL_KEYWORDS = ("world cup", "fifa", "soccer", "football", "vs.", " fc ",
                     "premier league", "champions league", "la liga", "bundesliga", "serie a")


def _is_football(title: str) -> bool:
    t = (title or "").lower()
    return any(k in t for k in FOOTBALL_KEYWORDS)


def score_wallet(wallet: str, activity: list[dict]) -> dict:
    """Heuristisches Score-Profil einer Wallet aus ihrer oeffentlichen Activity."""
    now = time.time()
    trades = [a for a in activity if a.get("type") == "TRADE"]
    redeems = [a for a in activity if a.get("type") == "REDEEM"]
    fb_trades = [a for a in trades if _is_football(a.get("title", ""))]
    fb_redeems = [a for a in redeems if _is_football(a.get("title", ""))]

    n_trades = len(trades)
    vol = sum(float(a.get("usdcSize") or 0) for a in trades)
    fb_vol = sum(float(a.get("usdcSize") or 0) for a in fb_trades)
    redeem_usd = sum(float(a.get("usdcSize") or 0) for a in redeems)

    # Heuristik "Trefferquote": Anteil distinct gewonnener Maerkte an distinct gehandelten.
    # Verzerrt (Redeem != jeder Gewinn, offene Maerkte zaehlen mit) -> nur als Signal.
    traded_markets = {a.get("conditionId") for a in trades if a.get("conditionId")}
    won_markets = {a.get("conditionId") for a in redeems if a.get("conditionId")}
    resolved_hit_rate = (len(won_markets & traded_markets) / len(traded_markets)) if traded_markets else None

    last_ts = max((int(a.get("timestamp") or 0) for a in activity), default=0)
    recency_days = (now - last_ts) / 86400 if last_ts else None
    recency_factor = max(0.2, min(1.0, 1.0 - (recency_days or 999) / 90))  # <90 Tage aktiv

    avg_stake = vol / n_trades if n_trades else 0.0

    # Shrinkage: Vertrauen waechst mit Stichprobe der FUSSBALL-Trades
    n_fb = len(fb_trades)
    confidence = n_fb / (n_fb + config.WHALE_SHRINKAGE_K)

    # Gesamtscore in [0,1]: Treffer-Heuristik (geshrunken Richtung 0.5) x Recency,
    # skaliert mit log-Volumen (Kappung verhindert reine Geld-Dominanz)
    import math
    hit = resolved_hit_rate if resolved_hit_rate is not None else 0.5
    hit_shrunk = confidence * hit + (1 - confidence) * 0.5
    vol_factor = min(1.0, math.log10(max(fb_vol, 1) + 1) / 6)  # 1.0 ab ~1M$ Fussball-Volumen
    score = round(hit_shrunk * recency_factor * (0.5 + 0.5 * vol_factor), 4)

    return {
        "wallet": wallet,
        "n_trades_total": n_trades,
        "n_trades_football": n_fb,
        "volume_usd_total": round(vol, 0),
        "volume_usd_football": round(fb_vol, 0),
        "avg_stake_usd": round(avg_stake, 0),
        "redeem_usd": round(redeem_usd, 0),
        "resolved_hit_rate_heuristic": round(resolved_hit_rate, 3) if resolved_hit_rate is not None else None,
        "recency_days": round(recency_days, 1) if recency_days is not None else None,
        "confidence": round(confidence, 3),
        "score": score,
        "score_basis": "heuristic",  # nie "audited" — keine oeffentliche P&L-Historie pro Markt
        "football_specialist": n_fb >= 10 and (fb_vol / vol > 0.3 if vol else False),
    }


def whale_signal(snapshot: dict, max_wallets: int = 10) -> dict:
    """Aggregiertes Whale-Signal fuer ein Match-Event.

    Kandidaten = Top-Holder beider Sieg-Maerkte + groesste Einzeltrades.
    Signal = score-gewichtete Netto-Exposure je Ausgang -> Wahrscheinlichkeitsvektor.
    """
    market = snapshot["market"]
    holders = snapshot.get("holders", {})
    trades = snapshot.get("trades", {})

    # Exposure je Wallet und Ausgang aus Top-Holdern (Yes-Token-Bestaende)
    exposure: dict[str, dict[str, float]] = {}
    for outcome_key, hl in holders.items():
        for h in hl[:config.WHALE_TOP_HOLDERS]:
            w = h.get("proxyWallet")
            amt = float(h.get("amount") or 0)
            if w and amt > 0:
                exposure.setdefault(w, {}).setdefault(outcome_key, 0.0)
                exposure[w][outcome_key] += amt

    # Grosse aktuelle Trades ergaenzen (BUY auf Yes zaehlt als Exposure)
    for outcome_key, tl in trades.items():
        for t in tl:
            if t.get("side") == "BUY" and (t.get("outcome") or "").lower() == "yes":
                w = t.get("proxyWallet")
                usd = float(t.get("size") or 0) * float(t.get("price") or 0)
                if w and usd > 500:
                    exposure.setdefault(w, {}).setdefault(outcome_key, 0.0)
                    exposure[w][outcome_key] += usd

    # Wallets nach Gesamt-Exposure sortieren, Top-N scoren (Activity-Calls sind teuer)
    ranked = sorted(exposure.items(), key=lambda kv: -sum(kv[1].values()))[:max_wallets]
    profiles = []
    weighted = {"team1_win": 0.0, "draw": 0.0, "team2_win": 0.0}
    for wallet, expo in ranked:
        act = pm.get_user_activity(wallet, limit=500)
        prof = score_wallet(wallet, act)
        prof["exposure"] = {k: round(v, 0) for k, v in expo.items()}
        profiles.append(prof)
        for k, v in expo.items():
            if k in weighted:
                weighted[k] += prof["score"] * v
        time.sleep(0.12)

    tot = sum(weighted.values())
    probs = {k: (v / tot) for k, v in weighted.items()} if tot > 0 else None

    return {
        "probs": probs,
        "n_wallets_scored": len(profiles),
        "wallets": sorted(profiles, key=lambda p: -p["score"]),
        "method": ("Score-gewichtete Yes-Exposure der Top-Holder/Top-Trades. "
                   "Heuristisch — keine verifizierte Pro-Nutzer-Historie oeffentlich."),
        "status": "estimated",
        "fetched_at": dt.datetime.now().isoformat(timespec="seconds"),
    }

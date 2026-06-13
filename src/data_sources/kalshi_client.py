"""Kalshi (regulierter US-Prognosemarkt) — zweiter Marktpreis neben Polymarket.

Oeffentliche Market-Data-API ohne Key: Serie KXWCGAME = WM-Spiele, pro Event
drei Maerkte (Team1/Team2/TIE), Preise in Cents. Wahrscheinlichkeit aus
Bid/Ask-Mitte (falls quotiert), sonst last_price; danach normalisiert.
Divergenz Polymarket vs. Kalshi ist selbst ein Signal (Illiquiditaet/Manipulation).
"""
from __future__ import annotations

import datetime as dt
import json
import time

import requests

from src import config

API = "https://api.elections.kalshi.com/trade-api/v2"
SERIES = "KXWCGAME"
_CACHE = config.DATA_RAW / "kalshi_events.json"
_CACHE_TTL = 2 * 3600


def fetch_events(force: bool = False) -> dict:
    if not force and _CACHE.exists() and (time.time() - _CACHE.stat().st_mtime) < _CACHE_TTL:
        try:
            return json.loads(_CACHE.read_text(encoding="utf-8"))
        except Exception:
            pass
    events, cursor = [], None
    try:
        for _ in range(10):
            # KEIN status-Filter: spielnahe Events verlassen den Status "open",
            # bleiben aber handelbar/quotiert — sonst fehlen genau die Spiele von heute
            params = {"series_ticker": SERIES, "with_nested_markets": "true", "limit": 200}
            if cursor:
                params["cursor"] = cursor
            r = requests.get(f"{API}/events", params=params, timeout=25)
            r.raise_for_status()
            data = r.json()
            events.extend(data.get("events", []))
            cursor = data.get("cursor")
            if not cursor:
                break
        payload = {"status": "live", "events": events,
                   "as_of": dt.datetime.now().isoformat(timespec="seconds")}
        _CACHE.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return payload
    except Exception as exc:
        return {"status": "unavailable", "events": [], "note": f"Kalshi-API-Fehler: {exc}"}


def _num(m: dict, dollars_key: str, cents_key: str) -> float | None:
    """Kalshi liefert je nach API-Version '*_dollars' (String, 0..1) oder
    Integer-Cents. Beides nach Wahrscheinlichkeit 0..1 normalisieren."""
    v = m.get(dollars_key)
    if v not in (None, ""):
        try:
            return float(v)
        except (TypeError, ValueError):
            pass
    v = m.get(cents_key)
    if v not in (None, "", 0):
        try:
            return float(v) / 100.0
        except (TypeError, ValueError):
            pass
    return None


def _market_prob(m: dict) -> float | None:
    """Bid/Ask-Mitte bevorzugt, sonst letzter Preis."""
    bid = _num(m, "yes_bid_dollars", "yes_bid")
    ask = _num(m, "yes_ask_dollars", "yes_ask")
    if bid is not None and ask is not None and 0 < bid <= ask < 1:
        return (bid + ask) / 2.0
    last = _num(m, "last_price_dollars", "last_price")
    if last is not None and 0 < last < 1:
        return last
    return None


def probs_for_match(team1: str, team2: str, all_events: dict) -> dict | None:
    if all_events.get("status") != "live":
        return None
    for ev in all_events.get("events", []):
        title = (ev.get("title") or "").replace(" vs. ", " vs ")
        parts = [s.strip() for s in title.split(" vs ")]
        if len(parts) != 2:
            continue
        k1, k2 = config.canonical_team(parts[0]), config.canonical_team(parts[1])
        c1, c2 = config.canonical_team(team1), config.canonical_team(team2)
        direct = k1.lower() == c1.lower() and k2.lower() == c2.lower()
        flipped = k1.lower() == c2.lower() and k2.lower() == c1.lower()
        if not (direct or flipped):
            continue

        out = {}
        vol = 0
        for m in ev.get("markets", []):
            sub = (m.get("yes_sub_title") or "").strip()
            p = _market_prob(m)
            try:
                vol += int(float(m.get("volume_fp") or m.get("volume") or 0))
            except (TypeError, ValueError):
                pass
            if p is None:
                continue
            if sub.lower() in ("tie", "draw"):
                out["draw"] = p
            elif config.canonical_team(sub).lower() == k1.lower():
                out["team1_win" if direct else "team2_win"] = p
            elif config.canonical_team(sub).lower() == k2.lower():
                out["team2_win" if direct else "team1_win"] = p
        if len(out) != 3:
            return None  # unvollstaendig quotiert -> nicht verwenden
        s = sum(out.values())
        if s <= 0:
            return None
        return {
            "probs": {k: round(v / s, 4) for k, v in out.items()},
            "raw_sum": round(s, 4), "volume_contracts": vol,
            "event_ticker": ev.get("event_ticker"),
            "url": f"https://kalshi.com/markets/{SERIES}",
            "status": "live", "source": "kalshi",
        }
    return None

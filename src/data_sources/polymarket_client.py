"""Polymarket-Integration (nur oeffentliche, unauthentifizierte Endpunkte).

  - Gamma API  (gamma-api.polymarket.com): Events, Maerkte, Preise
  - Data API   (data-api.polymarket.com) : Trades, Holder, User-Activity

WM-Spiel-Events folgen dem Slug-Muster: fifwc-<code1>-<code2>-<YYYY-MM-DD>.
Pro Spiel existieren drei Ja/Nein-Maerkte (Heimsieg, Auswaertssieg, Remis),
die zusammen den 1X2-Markt bilden. Preise werden normalisiert (Summe -> 1).
"""
from __future__ import annotations

import datetime as dt
import json
import time
from typing import Optional

import requests

from src import config

_session = requests.Session()
_session.headers["User-Agent"] = "wm-dashboard/0.1 (research)"


def _get(url: str, params: dict | None = None, timeout: int = 25):
    r = _session.get(url, params=params, timeout=timeout)
    r.raise_for_status()
    return r.json()


# ---------------------------------------------------------------- Discovery

def discover_match_events(dates: list[str], max_pages: int = 12) -> list[dict]:
    """Findet offene fifwc-Match-Events fuer die angegebenen Daten (YYYY-MM-DD)."""
    found: dict[str, dict] = {}
    for offset in range(0, max_pages * 100, 100):
        try:
            batch = _get(f"{config.GAMMA_API}/events", {
                "tag_slug": "fifa-world-cup", "closed": "false",
                "limit": 100, "offset": offset,
            })
        except Exception:
            break
        if not batch:
            break
        for ev in batch:
            slug = ev.get("slug", "")
            if slug.startswith(config.MATCH_SLUG_PREFIX) and slug[-10:] in dates:
                found[slug] = ev
        if len(batch) < 100:
            break
    return sorted(found.values(), key=lambda e: e.get("slug", ""))


def parse_slug(slug: str) -> Optional[dict]:
    """fifwc-can-bih-2026-06-12 -> Teams + Datum."""
    body = slug[len(config.MATCH_SLUG_PREFIX):]
    parts = body.split("-")
    if len(parts) < 5:
        return None
    code1, code2 = parts[0], parts[1]
    date = "-".join(parts[2:5])
    return {
        "team1_code": code1, "team2_code": code2, "date": date,
        "team1": config.TEAM_CODES.get(code1, code1.upper()),
        "team2": config.TEAM_CODES.get(code2, code2.upper()),
    }


# ---------------------------------------------------------------- Maerkte

def get_event(slug: str) -> Optional[dict]:
    res = _get(f"{config.GAMMA_API}/events", {"slug": slug})
    return res[0] if res else None


def extract_1x2(event: dict) -> Optional[dict]:
    """Extrahiert Heim/Remis/Auswaerts-Preise aus den drei Ja/Nein-Maerkten.

    Rueckgabe enthaelt rohe und normalisierte Wahrscheinlichkeiten sowie
    Liquiditaets-/Volumenkennzahlen und die conditionIds fuer die Data API.
    """
    meta = parse_slug(event.get("slug", "")) or {}
    # Teamnamen primaer aus dem Event-Titel ("Australia vs. Türkiye") — robuster
    # als Slug-Codes, weil die Markt-Fragen dieselbe Schreibweise nutzen.
    title = (event.get("title") or "").replace(" vs. ", " vs ")
    tparts = [s.strip() for s in title.split(" vs ")]
    if len(tparts) == 2 and all(tparts):
        raw1, raw2 = tparts
    else:
        raw1, raw2 = meta.get("team1", ""), meta.get("team2", "")
    t1, t2 = config.canonical_team(raw1), config.canonical_team(raw2)

    out = {"team1_win": None, "draw": None, "team2_win": None}
    cond = {}
    vol = liq = 0.0

    for m in event.get("markets", []):
        q = (m.get("question") or "").lower()
        try:
            prices = json.loads(m.get("outcomePrices", "[]"))
            outs = json.loads(m.get("outcomes", "[]")) if m.get("outcomes") else []
            # Yes-Preis ueber das Label finden (robust gegen [No, Yes]-Reihenfolge);
            # ohne Labels Fallback auf Index 0 (bisherige Annahme [Yes, No]).
            yi = next((i for i, o in enumerate(outs) if str(o).strip().lower() == "yes"), 0)
            yes_price = float(prices[yi])
        except Exception:
            continue
        vol += float(m.get("volumeNum") or 0)
        liq += float(m.get("liquidityNum") or 0)
        if "draw" in q:
            key = "draw"
        elif raw1.lower() in q or t1.lower() in q:
            key = "team1_win"
        elif raw2.lower() in q or t2.lower() in q:
            key = "team2_win"
        else:
            continue
        out[key] = yes_price
        cond[key] = m.get("conditionId")

    if any(v is None for v in out.values()):
        # Fallback: Zuordnung ueber Fragenreihenfolge unsicher -> None melden
        return None

    raw_sum = sum(out.values())
    norm = {k: (v / raw_sum if raw_sum > 0 else None) for k, v in out.items()}
    return {
        "slug": event.get("slug"), "title": event.get("title"),
        "team1": t1, "team2": t2, "date": meta.get("date"),
        "raw": out, "raw_sum": round(raw_sum, 4),
        "probs": norm,
        "condition_ids": cond,
        "volume_usd": round(vol, 0), "liquidity_usd": round(liq, 0),
        # UTC-aware: maßgeblich für den Pre-Kickoff-/Leakage-Filter der Kalibrierung,
        # damit die Abgrenzung unabhängig von Systemzeitzone/DST robust ist.
        "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "source": "polymarket-gamma", "status": "live",
        "url": f"https://polymarket.com/event/{event.get('slug')}",
    }


# ---------------------------------------------------------------- Data API

def get_trades(condition_id: str, limit: int = 200) -> list[dict]:
    try:
        return _get(f"{config.DATA_API}/trades", {"market": condition_id, "limit": limit}) or []
    except Exception:
        return []


def get_holders(condition_id: str, limit: int = 20) -> list[dict]:
    try:
        res = _get(f"{config.DATA_API}/holders", {"market": condition_id, "limit": limit})
    except Exception:
        return []
    if isinstance(res, dict):
        return res.get("holders", [])
    # API liefert teils Liste von {token, holders}
    holders = []
    for tok in res or []:
        holders.extend(tok.get("holders", []))
    return holders


def get_user_activity(wallet: str, limit: int = 500) -> list[dict]:
    """Oeffentliche Aktivitaet einer Wallet (Trades, Redeems, ...)."""
    try:
        return _get(f"{config.DATA_API}/activity", {"user": wallet, "limit": limit}) or []
    except Exception:
        return []


def snapshot_market(event_slug: str) -> Optional[dict]:
    """Komplett-Snapshot eines Match-Events inkl. Trades/Holdern, gecacht nach data/raw."""
    ev = get_event(event_slug)
    if not ev:
        return None
    market = extract_1x2(ev)
    if not market:
        return None
    trades, holders = {}, {}
    for key, cid in market["condition_ids"].items():
        if not cid:
            continue
        trades[key] = get_trades(cid, config.WHALE_RECENT_TRADES)
        holders[key] = get_holders(cid, config.WHALE_TOP_HOLDERS)
        time.sleep(0.15)  # hoeflich bleiben
    snap = {"market": market, "trades": trades, "holders": holders}
    out = config.DATA_RAW / f"polymarket_{event_slug}.json"
    out.write_text(json.dumps(snap, ensure_ascii=False), encoding="utf-8")
    return snap

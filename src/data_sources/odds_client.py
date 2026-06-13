"""Buchmacher-Quoten via The Odds API (the-odds-api.com, Free Tier ~500 Req/Monat).

Liefert 3-Weg-H2H-Quoten (Sieg/Remis/Sieg) fuer WM-Spiele. Pinnacle wird
bevorzugt (schaerfster Buchmacher); fehlt Pinnacle, Median ueber alle Buecher.
Quoten werden proportional entvigt (Overround entfernt) -> Wahrscheinlichkeiten.

Ohne ODDS_API_KEY: Status "unavailable", Ensemble laesst die Quelle weg.
Sparsame API-Nutzung: 1 Request pro Daily Run (alle Spiele in einer Antwort).
"""
from __future__ import annotations

import datetime as dt
import json
import statistics
import time

import requests

from src import config

SPORT_KEY = "soccer_fifa_world_cup"
_CACHE = config.DATA_RAW / "bookmaker_odds.json"
_CACHE_TTL = 6 * 3600  # Quoten bewegen sich — aber Free-Tier-Budget schonen


def available() -> bool:
    return bool(config.ODDS_API_KEY)


def fetch_all_odds(force: bool = False) -> dict:
    """Alle offenen WM-H2H-Quoten. {"status", "events": [...], "as_of"}"""
    if not available():
        return {"status": "unavailable", "events": [],
                "note": "Kein ODDS_API_KEY gesetzt (kostenlos: the-odds-api.com)."}

    if not force and _CACHE.exists() and (time.time() - _CACHE.stat().st_mtime) < _CACHE_TTL:
        try:
            return json.loads(_CACHE.read_text(encoding="utf-8"))
        except Exception:
            pass

    try:
        r = requests.get(f"{config.ODDS_API_BASE}/sports/{SPORT_KEY}/odds",
                         params={"apiKey": config.ODDS_API_KEY, "regions": "eu,uk",
                                 "markets": "h2h,totals", "oddsFormat": "decimal"},
                         timeout=25)
        r.raise_for_status()
        remaining = r.headers.get("x-requests-remaining")
        payload = {"status": "live", "events": r.json(),
                   "as_of": dt.datetime.now().isoformat(timespec="seconds"),
                   "requests_remaining": remaining}
        _CACHE.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return payload
    except Exception as exc:
        return {"status": "unavailable", "events": [], "note": f"Odds-API-Fehler: {exc}"}


def _devig(odds: dict[str, float]) -> dict[str, float]:
    """Proportionales Entviggen: p_i = (1/quote_i) / sum(1/quote_j)."""
    inv = {k: 1.0 / v for k, v in odds.items() if v and v > 1.0}
    s = sum(inv.values())
    return {k: v / s for k, v in inv.items()} if s > 0 else {}


def _team_match(a: str, b: str) -> bool:
    ca = config.canonical_team(a).lower()
    cb = config.canonical_team(b).lower()
    return ca == cb or ca in cb or cb in ca


def _find_event(team1: str, team2: str, all_odds: dict):
    for ev in all_odds.get("events", []):
        home, away = ev.get("home_team", ""), ev.get("away_team", "")
        if ((_team_match(team1, home) and _team_match(team2, away)) or
                (_team_match(team1, away) and _team_match(team2, home))):
            return ev, _team_match(team1, away)  # (event, flipped)
    return None, False


def best_prices_for_match(team1: str, team2: str, all_odds: dict) -> dict | None:
    """Beste verfuegbare Quote je Auswahl (Line-Shopping ueber alle Buecher) plus
    scharfer entvigter Konsens (Pinnacle bevorzugt, sonst Median).

    Rueckgabe: {
      "h2h": {sel: {"best_odds", "book", "n_books", "consensus_prob", "all_odds":[...]}},
      "totals": {line: {"over": {...}, "under": {...}, "consensus": {...}}},
      "n_bookmakers", "books": [...] }
    fuer sel in team1_win/draw/team2_win.
    """
    if all_odds.get("status") != "live":
        return None
    ev, flipped = _find_event(team1, team2, all_odds)
    if not ev:
        return None
    home, away = ev.get("home_team", ""), ev.get("away_team", "")

    # ---- 1X2 (h2h): beste Quote je Auswahl + scharfer Konsens ----
    best_h2h = {"team1_win": (0.0, None, []), "draw": (0.0, None, []), "team2_win": (0.0, None, [])}
    per_book_h2h, pinnacle_h2h = [], None
    book_titles = set()
    for bm in ev.get("bookmakers", []):
        title = bm.get("title")
        book_titles.add(title)
        for mk in bm.get("markets", []):
            if mk.get("key") != "h2h":
                continue
            prices = {}
            for o in mk.get("outcomes", []):
                nm, pr = o.get("name", ""), o.get("price")
                if not pr:
                    continue
                if nm.lower() == "draw":
                    sel = "draw"
                elif _team_match(home, nm):
                    sel = "team1_win" if not flipped else "team2_win"
                elif _team_match(away, nm):
                    sel = "team2_win" if not flipped else "team1_win"
                else:
                    continue
                prices[sel] = pr
                cur = best_h2h[sel]
                best_h2h[sel][2].append(pr)
                if pr > cur[0]:
                    best_h2h[sel] = (pr, title, cur[2])
            if len(prices) == 3:
                per_book_h2h.append(prices)
                if bm.get("key") == "pinnacle":
                    pinnacle_h2h = prices
    if not per_book_h2h:
        return None
    sharp = pinnacle_h2h or {
        s: statistics.median(b[s] for b in per_book_h2h) for s in ("team1_win", "draw", "team2_win")}
    consensus = _devig(sharp)

    h2h = {}
    for sel in ("team1_win", "draw", "team2_win"):
        odds, book, allo = best_h2h[sel]
        h2h[sel] = {"best_odds": round(odds, 3), "book": book, "n_books": len(allo),
                    "consensus_prob": round(consensus.get(sel, 0.0), 4),
                    "max_implied": round(1.0 / max(allo), 4) if allo else None,
                    "min_implied": round(1.0 / min(allo), 4) if allo else None}

    # ---- Totals (Over/Under): beste Quote je Linie + Konsens ----
    lines: dict[str, dict] = {}
    for bm in ev.get("bookmakers", []):
        title = bm.get("title")
        for mk in bm.get("markets", []):
            if mk.get("key") != "totals":
                continue
            for o in mk.get("outcomes", []):
                pt, nm, pr = o.get("point"), (o.get("name") or "").lower(), o.get("price")
                if pt is None or pr is None or nm not in ("over", "under"):
                    continue
                key = str(pt)
                slot = lines.setdefault(key, {"over": [], "under": []})
                slot[nm].append((pr, title))
    totals = {}
    for line, slot in lines.items():
        if not slot["over"] or not slot["under"]:
            continue
        bo = max(slot["over"], key=lambda x: x[0])
        bu = max(slot["under"], key=lambda x: x[0])
        # scharfer Konsens je Linie: Median der Quoten -> entviggen
        mo, mu = statistics.median(p for p, _ in slot["over"]), statistics.median(p for p, _ in slot["under"])
        cons = _devig({"over": mo, "under": mu})
        totals[line] = {
            "over": {"best_odds": round(bo[0], 3), "book": bo[1], "n_books": len(slot["over"]),
                     "consensus_prob": round(cons.get("over", 0.0), 4)},
            "under": {"best_odds": round(bu[0], 3), "book": bu[1], "n_books": len(slot["under"]),
                      "consensus_prob": round(cons.get("under", 0.0), 4)},
        }

    return {"h2h": h2h, "totals": totals, "n_bookmakers": len(book_titles),
            "books": sorted(book_titles), "team1": team1, "team2": team2}


def probs_for_match(team1: str, team2: str, date: str, all_odds: dict) -> dict | None:
    """Entvigte 1X2-Wahrscheinlichkeiten fuer ein Spiel; None wenn nicht gefunden.

    team1/team2: unsere Namen; date: YYYY-MM-DD (kickoff kann wegen Zeitzonen
    +/- 1 Tag abweichen — wir matchen primaer ueber Teamnamen).
    """
    if all_odds.get("status") != "live":
        return None
    for ev in all_odds.get("events", []):
        home, away = ev.get("home_team", ""), ev.get("away_team", "")
        if not ((_team_match(team1, home) and _team_match(team2, away)) or
                (_team_match(team1, away) and _team_match(team2, home))):
            continue
        flipped = _team_match(team1, away)

        # Pinnacle bevorzugt, sonst Median ueber alle Buchmacher
        per_book = []
        pinnacle = None
        for bm in ev.get("bookmakers", []):
            for mk in bm.get("markets", []):
                if mk.get("key") != "h2h":
                    continue
                prices = {}
                for o in mk.get("outcomes", []):
                    nm = o.get("name", "")
                    if nm.lower() == "draw":
                        prices["draw"] = o.get("price")
                    elif _team_match(home, nm):
                        prices["home"] = o.get("price")
                    elif _team_match(away, nm):
                        prices["away"] = o.get("price")
                if len(prices) == 3:
                    per_book.append(prices)
                    if bm.get("key") == "pinnacle":
                        pinnacle = prices
        if not per_book:
            return None

        if pinnacle:
            chosen, basis = pinnacle, "pinnacle"
        else:
            chosen = {k: statistics.median(b[k] for b in per_book) for k in ("home", "draw", "away")}
            basis = f"median({len(per_book)} books)"

        p = _devig(chosen)
        if len(p) != 3:
            return None
        overround = sum(1.0 / v for v in chosen.values())
        h, d, a = p["home"], p["draw"], p["away"]
        if flipped:
            h, a = a, h
        return {
            "probs": {"team1_win": round(h, 4), "draw": round(d, 4), "team2_win": round(a, 4)},
            "basis": basis, "n_bookmakers": len(per_book),
            "overround": round(overround, 4),
            "commence_time": ev.get("commence_time"),
            "status": "live", "source": "the-odds-api",
        }
    return None

"""ESPN-Scoreboard (inoffizielle, aber stabile oeffentliche API, kein Key).

Liefert pro WM-Spiel: Status (Scheduled/In Progress/Full Time), Anstoss (UTC),
Zwischenstand und — kurz vor Anpfiff — Aufstellungen (Rosters via Summary-API).
Inoffiziell => defensiv behandeln, Label "live (unofficial)".
"""
from __future__ import annotations

import datetime as dt
import json
import time

import requests

from src import config

BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world"
_CACHE = config.DATA_RAW / "espn_scoreboard.json"
_CACHE_TTL = 1 * 3600  # Status aendert sich schnell


def fetch_scoreboard(date_from: str, date_to: str, force: bool = False) -> dict:
    """Spiele im Datumsbereich (YYYY-MM-DD)."""
    if not force and _CACHE.exists() and (time.time() - _CACHE.stat().st_mtime) < _CACHE_TTL:
        try:
            cached = json.loads(_CACHE.read_text(encoding="utf-8"))
            if cached.get("range") == [date_from, date_to]:
                return cached
        except Exception:
            pass
    try:
        rng = f"{date_from.replace('-', '')}-{date_to.replace('-', '')}"
        r = requests.get(f"{BASE}/scoreboard", params={"dates": rng}, timeout=25,
                         headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        games = []
        for ev in r.json().get("events", []):
            comp = (ev.get("competitions") or [{}])[0]
            teams = {}
            for c in comp.get("competitors", []):
                side = c.get("homeAway")
                teams[side] = {"name": c.get("team", {}).get("displayName", ""),
                               "score": c.get("score")}
            venue = comp.get("venue", {})
            games.append({
                "espn_id": ev.get("id"),
                "kickoff_utc": ev.get("date"),
                "status": ev.get("status", {}).get("type", {}).get("description", "?"),
                "state": ev.get("status", {}).get("type", {}).get("state", "?"),  # pre/in/post
                "clock": ev.get("status", {}).get("displayClock"),
                "venue": venue.get("fullName"),
                "city": venue.get("address", {}).get("city"),
                "home": teams.get("home", {}), "away": teams.get("away", {}),
            })
        payload = {"status": "live", "source_note": "ESPN (inoffizielle API)",
                   "range": [date_from, date_to], "games": games,
                   "as_of": dt.datetime.now().isoformat(timespec="seconds")}
        _CACHE.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return payload
    except Exception as exc:
        return {"status": "unavailable", "games": [], "note": f"ESPN-Fehler: {exc}"}


def info_for_match(team1: str, team2: str, scoreboard: dict) -> dict | None:
    if scoreboard.get("status") != "live":
        return None
    c1 = config.canonical_team(team1).lower()
    c2 = config.canonical_team(team2).lower()
    for g in scoreboard.get("games", []):
        h = config.canonical_team(g["home"].get("name", "")).lower()
        a = config.canonical_team(g["away"].get("name", "")).lower()
        if {c1, c2} == {h, a}:
            flipped = c1 == a
            info = dict(g)
            info["team1_is_home"] = not flipped
            if flipped:
                info["home"], info["away"] = g["away"], g["home"]  # team1-Sicht
            return info
    return None


def lineups(espn_id: str) -> dict | None:
    """Aufstellungen aus der Summary-API (erst ~1h vor Anpfiff gefuellt)."""
    try:
        r = requests.get(f"{BASE}/summary", params={"event": espn_id}, timeout=25,
                         headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        rosters = r.json().get("rosters", [])
        out = {}
        for side in rosters:
            team = side.get("team", {}).get("displayName", "?")
            starters = [p.get("athlete", {}).get("displayName", "?")
                        for p in side.get("roster", []) if p.get("starter")]
            if starters:
                out[team] = {"formation": side.get("formation"), "starting_xi": starters}
        return out or None
    except Exception:
        return None

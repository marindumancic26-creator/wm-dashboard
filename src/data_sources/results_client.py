"""Offizielle WM-Ergebnisse via football-data.org (v4, Free Tier, X-Auth-Token).

Zweck: Auflösung unserer Prognosen -> Kalibrierungs-Tracking (Brier Score).
Ohne FOOTBALL_DATA_API_KEY: Status "unavailable" (Kalibrierung pausiert dann).
"""
from __future__ import annotations

import datetime as dt
import json
import time

import requests

from src import config

_CACHE = config.DATA_RAW / "wc_results.json"
_FIXTURES_CACHE = config.DATA_RAW / "wc_fixtures.json"
_CACHE_TTL = 6 * 3600
_FIXTURES_TTL = 12 * 3600
WC_2026_MATCH_COUNT = 104


def available() -> bool:
    return bool(config.FOOTBALL_DATA_KEY)


def fetch_fixtures(force: bool = False) -> dict:
    """ALLE WM-Spiele inkl. Stage (GROUP_STAGE/LAST_16/…) für die K.o.-Erkennung."""
    if not available():
        return {"status": "unavailable", "fixtures": []}
    if not force and _FIXTURES_CACHE.exists() and (time.time() - _FIXTURES_CACHE.stat().st_mtime) < _FIXTURES_TTL:
        try:
            return json.loads(_FIXTURES_CACHE.read_text(encoding="utf-8"))
        except Exception:
            pass
    try:
        r = requests.get(f"{config.FOOTBALL_DATA_BASE}/competitions/WC/matches",
                         headers={"X-Auth-Token": config.FOOTBALL_DATA_KEY}, timeout=25)
        r.raise_for_status()
        fixtures = []
        for m in r.json().get("matches", []):
            ft = m.get("score", {}).get("fullTime", {})
            fixtures.append({"date": (m.get("utcDate") or "")[:10],
                             "home": m.get("homeTeam", {}).get("name", ""),
                             "away": m.get("awayTeam", {}).get("name", ""),
                             "stage": m.get("stage", ""), "group": m.get("group"),
                             "matchday": m.get("matchday"), "status": m.get("status"),
                             "home_goals": ft.get("home"), "away_goals": ft.get("away")})
        payload = {"status": "live", "fixtures": fixtures,
                   "as_of": dt.datetime.now().isoformat(timespec="seconds")}
        _FIXTURES_CACHE.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return payload
    except Exception as exc:
        return {"status": "unavailable", "fixtures": [], "note": f"football-data.org-Fehler: {exc}"}


def stage_for(team1: str, team2: str, fixtures: dict) -> str | None:
    """Stage eines Spiels (über Teamnamen, zeitzonen-/datumsunabhängig)."""
    from src.model.calibration import _team_eq
    for f in fixtures.get("fixtures", []):
        if ((_team_eq(team1, f["home"]) and _team_eq(team2, f["away"])) or
                (_team_eq(team1, f["away"]) and _team_eq(team2, f["home"]))):
            return f.get("stage")
    return None


def is_knockout(stage: str | None) -> bool:
    return bool(stage) and stage.upper() not in ("GROUP_STAGE", "GROUP", "")


def fetch_results(force: bool = False) -> dict:
    """Beendete WM-2026-Spiele. {"status", "results": [{date, home, away, hg, ag}]}"""
    if not available():
        return {"status": "unavailable", "results": [],
                "note": "Kein FOOTBALL_DATA_API_KEY gesetzt (kostenlos: football-data.org)."}

    if not force and _CACHE.exists() and (time.time() - _CACHE.stat().st_mtime) < _CACHE_TTL:
        try:
            return json.loads(_CACHE.read_text(encoding="utf-8"))
        except Exception:
            pass

    try:
        r = requests.get(f"{config.FOOTBALL_DATA_BASE}/competitions/WC/matches",
                         params={"status": "FINISHED"},
                         headers={"X-Auth-Token": config.FOOTBALL_DATA_KEY},
                         timeout=25)
        r.raise_for_status()
        results = []
        for m in r.json().get("matches", []):
            ft = m.get("score", {}).get("fullTime", {})
            if ft.get("home") is None:
                continue
            results.append({
                "date": (m.get("utcDate") or "")[:10],
                "kickoff_utc": m.get("utcDate"),
                "home": m.get("homeTeam", {}).get("name", ""),
                "away": m.get("awayTeam", {}).get("name", ""),
                "home_goals": ft["home"], "away_goals": ft["away"],
            })
        payload = {"status": "live", "results": results,
                   "as_of": dt.datetime.now().isoformat(timespec="seconds")}
        _CACHE.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
        return payload
    except Exception as exc:
        return {"status": "unavailable", "results": [], "note": f"football-data.org-Fehler: {exc}"}


def world_cup_completion_status(fixtures: dict) -> dict:
    """Objektiver WM-Ende-Check: erst alle 104 Spiele offiziell beendet."""
    rows = fixtures.get("fixtures") or []
    if fixtures.get("status") != "live" or not rows:
        return {"complete": False, "status": fixtures.get("status", "unavailable"),
                "n_fixtures": len(rows), "n_finished": 0,
                "note": "WM-Ende nicht pruefbar: Fixture-Quelle nicht live."}
    finished = [row for row in rows if (row.get("status") or "").upper() == "FINISHED"]
    final_rows = [row for row in rows if (row.get("stage") or "").upper() == "FINAL"]
    final_finished = bool(final_rows and all((row.get("status") or "").upper() == "FINISHED"
                                             for row in final_rows))
    complete = len(rows) >= WC_2026_MATCH_COUNT and len(finished) == len(rows) and final_finished
    return {"complete": complete, "status": "live", "n_fixtures": len(rows),
            "n_finished": len(finished), "final_finished": final_finished,
            "required_fixtures": WC_2026_MATCH_COUNT,
            "note": ("WM abgeschlossen." if complete else
                     "WM laeuft noch oder Finale ist nicht offiziell beendet.")}

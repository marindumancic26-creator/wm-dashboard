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
_CACHE_TTL = 6 * 3600


def available() -> bool:
    return bool(config.FOOTBALL_DATA_KEY)


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

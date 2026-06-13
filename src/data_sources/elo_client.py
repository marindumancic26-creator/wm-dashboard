"""Live-Elo-Ratings von eloratings.net (World Football Elo Ratings).

Ersetzt den statischen Snapshot in config.ELO_RATINGS. Faellt der Abruf aus,
wird der statische Snapshot mit Status "estimated" genutzt. Cache: 20 h.

Endpunkte (oeffentlich, TSV):
  https://www.eloratings.net/World.tsv     — Spalte 3 = Laendercode, Spalte 4 = Rating
  https://www.eloratings.net/en.teams.tsv  — Code -> Klarname
"""
from __future__ import annotations

import json
import time

import requests

from src import config

_CACHE = config.DATA_RAW / "elo_ratings.json"
_CACHE_TTL = 20 * 3600

# eloratings.net-Namen -> unsere Teamnamen (nur Abweichungen)
_ALIASES = {
    "United States": "United States",
    "South Korea": "South Korea",
    "Bosnia/Herzegovina": "Bosnia and Herzegovina",
    "Bosnia and Herzegovina": "Bosnia and Herzegovina",
    "Ivory Coast": "Ivory Coast",
    "Côte d'Ivoire": "Ivory Coast",
    "Czechia": "Czech Republic",
    "Türkiye": "Turkey",
    "Curaçao": "Curacao",
}


def get_ratings(force: bool = False) -> dict:
    """{"ratings": {name: elo}, "status": "live"|"estimated", "as_of", "source"}"""
    if not force and _CACHE.exists() and (time.time() - _CACHE.stat().st_mtime) < _CACHE_TTL:
        try:
            return json.loads(_CACHE.read_text(encoding="utf-8"))
        except Exception:
            pass

    try:
        names_raw = requests.get("https://www.eloratings.net/en.teams.tsv", timeout=20)
        world_raw = requests.get("https://www.eloratings.net/World.tsv", timeout=20)
        names_raw.raise_for_status()
        world_raw.raise_for_status()

        code_to_name = {}
        for line in names_raw.text.splitlines():
            parts = line.split("\t")
            if len(parts) >= 2 and parts[0].strip():
                code_to_name[parts[0].strip()] = parts[1].strip()

        ratings = {}
        for line in world_raw.text.splitlines():
            parts = line.split("\t")
            if len(parts) >= 4:
                code, rating = parts[2].strip(), parts[3].strip()
                name = code_to_name.get(code)
                if name and rating.isdigit():
                    ratings[_ALIASES.get(name, name)] = int(rating)

        if len(ratings) < 50:
            raise ValueError(f"nur {len(ratings)} Ratings geparst — Format geaendert?")

        payload = {"ratings": ratings, "status": "live",
                   "as_of": time.strftime("%Y-%m-%dT%H:%M:%S"),
                   "source": "eloratings.net", "n_teams": len(ratings)}
        _CACHE.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
        return payload
    except Exception as exc:
        return {"ratings": dict(config.ELO_RATINGS), "status": "estimated",
                "as_of": config.ELO_SNAPSHOT_DATE,
                "source": f"statischer Fallback (eloratings.net nicht erreichbar: {exc})",
                "n_teams": len(config.ELO_RATINGS)}


def rating_for(team: str, elo_data: dict) -> float:
    r = elo_data.get("ratings", {})
    aliases = {"USA": "United States", "Türkiye": "Turkey",
               "Bosnia-Herzegovina": "Bosnia and Herzegovina"}
    name = aliases.get(team, team)
    if name in r:
        return r[name]
    for k in r:
        if k.lower() == name.lower():
            return r[k]
    # Fallback: statische Tabelle, dann Default
    return config.ELO_RATINGS.get(name, config.ELO_DEFAULT)

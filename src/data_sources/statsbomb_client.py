"""StatsBomb-Integration.

Zwei sauber getrennte Modi:
  1. API-Modus  : nur wenn SB_USERNAME/SB_PASSWORD als Umgebungsvariablen gesetzt sind
                  (kostenpflichtiger Zugang). Status-Label: "live".
  2. Open-Data  : oeffentliche StatsBomb Open Data via statsbombpy. Neueste Herren-WM
                  dort ist 2022 -> fuer die WM 2026 sind das HISTORISCHE Prior-Daten.
                  Status-Label: "historical" bzw. "unavailable" fuer Teams ohne Daten.

Ergebnis: Team-Profile (Tore erzielt/kassiert pro Spiel auf WM-Niveau), die als
Prior in das Feature-Modell einfliessen. Caching nach data/raw.
"""
from __future__ import annotations

import json
import time
from typing import Optional

from src import config

WC_COMPETITION_ID = 43
WC_SEASONS = {106: "2022", 3: "2018"}  # neueste zuerst genutzt

_CACHE_TTL = 20 * 3600  # einmal taeglich neu laden


def _cache_path(name: str):
    return config.DATA_RAW / f"statsbomb_{name}.json"


def _load_cache(name: str) -> Optional[dict]:
    p = _cache_path(name)
    if p.exists() and (time.time() - p.stat().st_mtime) < _CACHE_TTL:
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def _save_cache(name: str, payload: dict) -> None:
    _cache_path(name).write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")


def data_mode() -> str:
    return "api" if config.STATSBOMB_API_AVAILABLE else "open-data"


def _fetch_wc_matches() -> list[dict]:
    """Laedt WM-Spiele (Ergebnisse) ueber statsbombpy."""
    from statsbombpy import sb  # lazy import

    creds = None
    if config.STATSBOMB_API_AVAILABLE:
        creds = {"user": config.STATSBOMB_USER, "passwd": config.STATSBOMB_PASS}

    rows: list[dict] = []
    for season_id, season_name in WC_SEASONS.items():
        try:
            if creds:
                df = sb.matches(competition_id=WC_COMPETITION_ID, season_id=season_id, creds=creds)
            else:
                df = sb.matches(competition_id=WC_COMPETITION_ID, season_id=season_id)
        except Exception:
            continue
        for _, m in df.iterrows():
            rows.append({
                "season": season_name,
                "home_team": str(m["home_team"]),
                "away_team": str(m["away_team"]),
                "home_score": int(m["home_score"]),
                "away_score": int(m["away_score"]),
            })
    return rows


def local_open_data_available() -> bool:
    return (config.OPEN_DATA_DIR / "competitions.json").exists()


def _local_xg_profiles() -> dict:
    """Aggregiert Event-Level-xG pro Team aus dem lokalen open-data-Klon
    (WM 2018+2022). Teuer (~130 Event-Dateien) -> permanenter Cache, da
    historische Daten unveraenderlich sind."""
    cache = _cache_path("local_xg")
    if cache.exists():
        try:
            return json.loads(cache.read_text(encoding="utf-8"))
        except Exception:
            pass

    agg: dict[str, dict] = {}
    n_events_files = 0
    for season_id in WC_SEASONS:
        mfile = config.OPEN_DATA_DIR / "matches" / str(WC_COMPETITION_ID) / f"{season_id}.json"
        if not mfile.exists():
            continue
        matches = json.loads(mfile.read_text(encoding="utf-8"))
        for m in matches:
            home, away = m["home_team"]["home_team_name"], m["away_team"]["away_team_name"]
            efile = config.OPEN_DATA_DIR / "events" / f"{m['match_id']}.json"
            if not efile.exists():
                continue
            events = json.loads(efile.read_text(encoding="utf-8"))
            n_events_files += 1
            xg = {home: 0.0, away: 0.0}
            for ev in events:
                shot = ev.get("shot")
                if shot and shot.get("statsbomb_xg") is not None:
                    t = ev.get("team", {}).get("name")
                    if t in xg:
                        xg[t] += float(shot["statsbomb_xg"])
            for me, opp in ((home, away), (away, home)):
                a = agg.setdefault(me, {"matches": 0, "xg_for": 0.0, "xg_against": 0.0})
                a["matches"] += 1
                a["xg_for"] += xg[me]
                a["xg_against"] += xg[opp]

    out = {t: {"xg_matches": a["matches"],
               "xg_for_pm": round(a["xg_for"] / a["matches"], 3),
               "xg_against_pm": round(a["xg_against"] / a["matches"], 3)}
           for t, a in agg.items() if a["matches"]}
    payload = {"teams": out, "n_event_files": n_events_files,
               "computed_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
    if out:
        cache.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    return payload


def get_team_profiles(force: bool = False) -> dict:
    """Team-Profile aus StatsBomb-WM-Daten (Tore pro Spiel, Gegentore pro Spiel).

    Rueckgabe: {"mode", "status", "source_note", "teams": {name: {...}}}
    """
    if not force:
        cached = _load_cache("team_profiles")
        if cached:
            cached["cache"] = "cached"
            return cached

    mode = data_mode()
    teams: dict[str, dict] = {}
    status = "historical"
    note = ("StatsBomb Open Data, FIFA World Cup 2018+2022 (neueste oeffentliche Herren-WM). "
            "KEINE tagesaktuellen 2026er-Daten oeffentlich verfuegbar.")
    if mode == "api":
        note = "StatsBomb API (credential-basiert)."
        status = "live"

    try:
        matches = _fetch_wc_matches()
    except Exception as exc:  # statsbombpy/Netz nicht verfuegbar
        return {"mode": mode, "status": "unavailable", "source_note": f"StatsBomb nicht erreichbar: {exc}",
                "teams": {}, "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S")}

    agg: dict[str, dict] = {}
    for m in matches:
        for side, opp in (("home", "away"), ("away", "home")):
            t = m[f"{side}_team"]
            a = agg.setdefault(t, {"matches": 0, "goals_for": 0, "goals_against": 0, "seasons": set()})
            a["matches"] += 1
            a["goals_for"] += m[f"{side}_score"]
            a["goals_against"] += m[f"{opp}_score"]
            a["seasons"].add(m["season"])

    for t, a in agg.items():
        n = a["matches"]
        teams[t] = {
            "matches": n,
            "goals_for_pm": round(a["goals_for"] / n, 3),
            "goals_against_pm": round(a["goals_against"] / n, 3),
            "seasons": sorted(a["seasons"]),
        }

    # Event-Level-xG aus lokalem open-data-Klon ergaenzen (falls vorhanden)
    xg_source = "none"
    if local_open_data_available():
        try:
            xg = _local_xg_profiles()
            for t, vals in xg.get("teams", {}).items():
                if t in teams:
                    teams[t].update(vals)
            if xg.get("teams"):
                xg_source = "local-clone"
                note += " Event-Level-xG aus lokalem open-data-Klon ergaenzt."
        except Exception as exc:
            note += f" (xG-Aggregation fehlgeschlagen: {exc})"

    payload = {
        "mode": mode, "status": status, "source_note": note, "teams": teams,
        "xg_source": xg_source,
        "n_matches_loaded": len(matches),
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "cache": "fresh",
    }
    if teams:
        _save_cache("team_profiles", payload)
    return payload


def profile_for(team: str, profiles: dict) -> dict:
    """Profil eines Teams; Status 'unavailable', wenn das Team in den Open Data fehlt
    (viele 2026er-Teilnehmer waren 2018/2022 nicht dabei)."""
    aliases = {
        "USA": "United States", "Türkiye": "Turkey",
        "Bosnia-Herzegovina": "Bosnia and Herzegovina",
        "South Korea": "South Korea", "Korea Republic": "South Korea",
    }
    teams = profiles.get("teams", {})
    name = aliases.get(team, team)
    for cand in (team, name):
        if cand in teams:
            return {"team": team, "status": profiles.get("status", "historical"), **teams[cand]}
    # statsbomb nennt z.T. andere Schreibweisen
    for k in teams:
        if k.lower() == name.lower():
            return {"team": team, "status": profiles.get("status", "historical"), **teams[k]}
    return {"team": team, "status": "unavailable", "matches": 0,
            "goals_for_pm": None, "goals_against_pm": None, "seasons": []}

"""Kostenlose historische Ligaresultate von football-data.co.uk.

Der Import nutzt ausschliesslich abgeschlossene saisonale CSV-Dateien. Quoten
werden optional als Diagnose-Benchmark eingelesen, niemals als Trainingsziel.
"""
from __future__ import annotations

import csv
import datetime as dt
import io
from pathlib import Path

import requests

from src import config


BASE_URL = "https://www.football-data.co.uk/mmz4281"
COMPETITION_DIVISIONS = {
    "premier_league": "E0",
    "la_liga": "SP1",
    "bundesliga": "D1",
    "serie_a": "I1",
    "ligue_1": "F1",
}
DEFAULT_SEASONS = (2021, 2022, 2023, 2024, 2025)


def _season_code(start_year: int) -> str:
    return f"{start_year % 100:02d}{(start_year + 1) % 100:02d}"


def _parse_date(value: str) -> str | None:
    for fmt in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            return dt.datetime.strptime(value.strip(), fmt).date().isoformat()
        except (AttributeError, ValueError):
            continue
    return None


def _market_probs(row: dict) -> dict | None:
    """Durchschnittsquoten proportional entviggen; nur Diagnose, kein Target."""
    try:
        odds = {"team1_win": float(row["AvgH"]), "draw": float(row["AvgD"]),
                "team2_win": float(row["AvgA"])}
        inverse = {key: 1.0 / value for key, value in odds.items() if value > 1.0}
        total = sum(inverse.values())
        if len(inverse) != 3 or total <= 0:
            return None
        return {key: value / total for key, value in inverse.items()}
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return None


def parse_csv(content: bytes, season_start: int,
              competition_key: str | None = None) -> list[dict]:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = content.decode("cp1252")
    matches = []
    for row in csv.DictReader(io.StringIO(text)):
        date = _parse_date(row.get("Date", ""))
        home, away = (row.get("HomeTeam") or "").strip(), (row.get("AwayTeam") or "").strip()
        try:
            home_score, away_score = int(row["FTHG"]), int(row["FTAG"])
        except (KeyError, TypeError, ValueError):
            continue
        if not (date and home and away):
            continue
        matches.append({"date": date, "season": f"{season_start}-{str(season_start + 1)[-2:]}",
                        "season_start": season_start, "home_team": home, "away_team": away,
                        "competition": competition_key,
                        "home_score": home_score, "away_score": away_score,
                        "market_probs": _market_probs(row)})
    return matches


def fetch_history(competition_key: str = "premier_league",
                  seasons: tuple[int, ...] = DEFAULT_SEASONS,
                  force: bool = False, http=requests,
                  cache_dir: Path | None = None) -> dict:
    division = COMPETITION_DIVISIONS.get(competition_key)
    if not division:
        return {"status": "unavailable", "matches": [],
                "note": "Kein football-data.co.uk-Divisionscode hinterlegt."}
    cache = cache_dir or (config.DATA_RAW / "football_data_uk")
    cache.mkdir(parents=True, exist_ok=True)
    all_matches, loaded, errors = [], [], []
    for season in seasons:
        code = _season_code(season)
        path = cache / f"{division}_{code}.csv"
        try:
            if force or not path.exists():
                response = http.get(f"{BASE_URL}/{code}/{division}.csv", timeout=25)
                response.raise_for_status()
                content = response.content
                path.write_bytes(content)
            else:
                content = path.read_bytes()
            rows = parse_csv(content, season, competition_key)
            if not rows:
                raise ValueError("keine gueltigen Ergebniszeilen")
            all_matches.extend(rows)
            loaded.append({"season_start": season, "n": len(rows), "cache": str(path)})
        except Exception as exc:
            errors.append({"season_start": season, "error": str(exc)})
    all_matches.sort(key=lambda row: (row["date"], row["home_team"], row["away_team"]))
    status = ("historical" if len(loaded) == len(seasons)
              else ("degraded" if loaded else "unavailable"))
    return {"status": status, "source": "football-data.co.uk", "competition": competition_key,
            "matches": all_matches, "seasons": loaded, "errors": errors,
            "n_matches": len(all_matches),
            "note": "Resultate fuer Walk-forward; Quoten nur Diagnose-Benchmark."}


def fetch_histories(competition_keys: tuple[str, ...] | None = None,
                    seasons: tuple[int, ...] = DEFAULT_SEASONS,
                    force: bool = False, http=requests,
                    cache_dir: Path | None = None) -> dict:
    keys = competition_keys or tuple(COMPETITION_DIVISIONS)
    competitions = {key: fetch_history(key, seasons, force, http, cache_dir)
                    for key in keys}
    loaded = [row for row in competitions.values() if row.get("status") != "unavailable"]
    matches = [match for row in competitions.values() for match in row.get("matches", [])]
    status = ("historical" if loaded and len(loaded) == len(keys)
              else ("degraded" if loaded else "unavailable"))
    return {"status": status, "source": "football-data.co.uk",
            "competitions": competitions, "matches": matches,
            "n_matches": len(matches),
            "note": "Top-5-Resultate fuer getrennte Walk-forward-Diagnosen."}

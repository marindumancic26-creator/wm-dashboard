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
PINNACLE_STALE_FROM = dt.date(2025, 7, 23)
OUTCOMES = ("team1_win", "draw", "team2_win")
BOOKMAKER_CLOSING_COLUMNS = {
    "bet365": ("B365CH", "B365CD", "B365CA"),
    "betway": ("BWCH", "BWCD", "BWCA"),
    "interwetten": ("IWCH", "IWCD", "IWCA"),
    "pinnacle": ("PSCH", "PSCD", "PSCA"),
    "william_hill": ("WHCH", "WHCD", "WHCA"),
    "vcbet": ("VCCH", "VCCD", "VCCA"),
}
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


def _parse_iso_date(value: str | None) -> dt.date | None:
    try:
        return dt.date.fromisoformat((value or "")[:10])
    except ValueError:
        return None


def _devig_odds(row: dict, columns: tuple[str, str, str]) -> dict | None:
    try:
        odds = {outcome: float(row[column])
                for outcome, column in zip(OUTCOMES, columns)}
        inverse = {key: 1.0 / value for key, value in odds.items()
                   if value and value > 1.0}
        total = sum(inverse.values())
        if len(inverse) != 3 or total <= 0:
            return None
        return {key: value / total for key, value in inverse.items()}
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return None


def _normalize_probs(probs: dict) -> dict | None:
    total = sum(probs.get(key, 0.0) for key in OUTCOMES)
    if total <= 0:
        return None
    return {key: probs.get(key, 0.0) / total for key in OUTCOMES}


def _market_probs(row: dict, match_date: str | None = None) -> tuple[dict | None, dict]:
    """Closing-Quoten proportional entviggen; nur Benchmark, niemals Target."""
    parsed_date = _parse_iso_date(match_date)
    books, excluded = [], []
    for book, columns in BOOKMAKER_CLOSING_COLUMNS.items():
        if book == "pinnacle" and parsed_date and parsed_date >= PINNACLE_STALE_FROM:
            excluded.append({"book": book, "reason": "football_data_stale_after_2025_07_23"})
            continue
        probs = _devig_odds(row, columns)
        if probs:
            books.append({"book": book, "probs": probs})

    meta = {"closing": True, "source": None, "n_books": len(books),
            "fallback": False, "excluded": excluded}
    if books:
        avg = {key: sum(book["probs"][key] for book in books) / len(books)
               for key in OUTCOMES}
        meta["source"] = "bookmaker_closing_consensus"
        meta["books"] = [book["book"] for book in books]
        return _normalize_probs(avg), meta

    fallback = _devig_odds(row, ("AvgCH", "AvgCD", "AvgCA"))
    if fallback:
        meta["source"] = "avg_closing_fallback"
        meta["fallback"] = True
        return fallback, meta

    meta["source"] = "missing_closing"
    return None, meta


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
        market_probs, market_meta = _market_probs(row, date)
        matches.append({"date": date, "season": f"{season_start}-{str(season_start + 1)[-2:]}",
                        "season_start": season_start, "home_team": home, "away_team": away,
                        "competition": competition_key,
                        "home_score": home_score, "away_score": away_score,
                        "block_key": date,
                        "market_probs": market_probs,
                        "market_meta": market_meta})
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
            covered = sum(1 for row in rows if row.get("market_probs"))
            loaded.append({"season_start": season, "n": len(rows), "cache": str(path),
                           "closing_coverage": round(covered / len(rows), 4)})
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

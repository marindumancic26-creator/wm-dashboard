"""Explizite Club-Quoten, keine WM-Namensheuristik und keine stillen Abruf-Retries."""
from __future__ import annotations

import math
import statistics
import unicodedata

import requests

from src.club_registry import load_club_registry
from src.pipeline.club_sites_policy import parse_time

BASE = "https://api.the-odds-api.com/v4"


def quota_headers(headers) -> dict | None:
    try:
        remaining = int(headers["x-requests-remaining"])
        used = int(headers["x-requests-used"])
        if min(remaining, used) < 0:
            return None
        return {"remaining": remaining, "used": used}
    except (KeyError, ValueError, TypeError):
        return None


class ClubOddsClient:
    def __init__(self, api_key: str, http=requests):
        self.api_key, self.http = api_key, http

    def probe(self) -> dict | None:
        """Sports-Liste ist laut API-Vertrag kreditfrei; Header prüfen das Budget."""
        if not self.api_key:
            return None
        try:
            response = self.http.get(f"{BASE}/sports", params={"apiKey": self.api_key}, timeout=25)
            response.raise_for_status()
            return quota_headers(response.headers)
        except (requests.RequestException, ValueError):
            return None

    def fetch(self, sport_key: str) -> dict:
        try:
            response = self.http.get(f"{BASE}/sports/{sport_key}/odds", params={
                "apiKey": self.api_key, "regions": "eu", "markets": "h2h,totals",
                "oddsFormat": "decimal", "dateFormat": "iso",
            }, timeout=30)
            response.raise_for_status()
            events = response.json()
            if not isinstance(events, list):
                raise ValueError("Ungueltiges Quotenformat")
            return {"status": "live", "events": events,
                    "quota": quota_headers(response.headers)}
        except (requests.RequestException, ValueError):
            # Exceptions enthalten möglicherweise die URL samt API-Key: nie weiterreichen.
            return {"status": "unavailable", "events": [], "quota": None,
                    "note": "Quotenquelle nicht erreichbar oder Antwort ungueltig."}


def _name(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def find_event(fixture: dict, events: list[dict]) -> dict | None:
    clubs = load_club_registry()

    def same(side, name):
        resolved = clubs.resolve(name)
        if side.get("club_id") and resolved.club_id:
            return side["club_id"] == resolved.club_id
        return _name(side.get("name", "")) == _name(name) and bool(name)

    found = []
    for event in events:
        try:
            seconds = abs((parse_time(event["commence_time"]) -
                           parse_time(fixture["kickoff_utc"])).total_seconds())
            if (seconds <= 900 and same(fixture["home"], event.get("home_team", ""))
                    and same(fixture["away"], event.get("away_team", ""))):
                found.append(event)
        except (ValueError, KeyError, TypeError):
            continue
    return found[0] if len(found) == 1 else None


def normalize_event(event: dict, fetched_at: str) -> dict:
    quotes, probabilities = [], []
    for book in event.get("bookmakers", []):
        if not book.get("key"):
            continue
        for market in book.get("markets", []):
            kind = market.get("key")
            if kind not in ("h2h", "totals"):
                continue
            per_book = {}
            for outcome in market.get("outcomes", []):
                name, price = outcome.get("name"), outcome.get("price")
                if (isinstance(price, bool) or not isinstance(price, (int, float))
                        or not math.isfinite(price) or price <= 1):
                    continue
                if kind == "h2h":
                    selection = {event.get("home_team"): "home", "Draw": "draw",
                                 event.get("away_team"): "away"}.get(name)
                    point = None
                else:
                    selection = {"Over": "over", "Under": "under"}.get(name)
                    point = outcome.get("point")
                    if (isinstance(point, bool) or not isinstance(point, (int, float))
                            or not math.isfinite(point) or point < 0):
                        continue
                if not selection:
                    continue
                quotes.append({"market": kind, "selection": selection, "point": point,
                               "odds": price, "bookmaker": book["key"],
                               "bookmaker_name": book.get("title") or book["key"],
                               "fetched_at": fetched_at,
                               "updated_at": market.get("last_update") or book.get("last_update"),
                               "source": "the-odds-api"})
                per_book[selection] = 1 / price
            if kind == "h2h" and set(per_book) == {"home", "draw", "away"}:
                total = sum(per_book.values())
                probabilities.append({key: value / total for key, value in per_book.items()})
    market_probs = None
    if probabilities:
        median = {key: statistics.median(p[key] for p in probabilities)
                  for key in ("home", "draw", "away")}
        total = sum(median.values())
        market_probs = {key: value / total for key, value in median.items()}
    return {"quotes": quotes, "market_probs": market_probs}

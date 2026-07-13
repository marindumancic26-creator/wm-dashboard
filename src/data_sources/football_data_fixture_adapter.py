"""Fixture-first-Adapter fuer football-data.org; derzeit Premier-League-Pilot.

Der Adapter entdeckt Spiele unabhaengig von Prognosemaerkten. Nicht aufgeloeste
Clubs bleiben in der Ausgabe sichtbar, erhalten aber keine kanonische Match-ID
und duerfen weder Prognosen noch Value freischalten.
"""
from __future__ import annotations

import datetime as dt
import json
from dataclasses import asdict
from pathlib import Path

import requests

from src import config
from src.competition_registry import Competition
from src.domain import CanonicalFixture, ClubRegistry, ProviderRef, canonical_match_id


class FootballDataFixtureAdapter:
    provider_name = "football_data"

    def __init__(self, api_key: str | None = None, http=requests) -> None:
        self.api_key = api_key if api_key is not None else config.FOOTBALL_DATA_KEY
        self.http = http

    def _competition_id(self, competition: Competition) -> str | None:
        for ref in competition.provider_ids:
            if ref.provider == self.provider_name:
                return ref.provider_id
        return None

    @staticmethod
    def _cache_path(competition: Competition, date_from: dt.date,
                    date_to: dt.date) -> Path:
        safe_range = f"{date_from.isoformat()}_{date_to.isoformat()}"
        return config.DATA_RAW / "football_data_fixtures" / f"{competition.key}_{safe_range}.json"

    @staticmethod
    def _season_key(match: dict) -> str | None:
        season = match.get("season") or {}
        start = str(season.get("startDate") or "")[:4]
        end = str(season.get("endDate") or "")[:4]
        if not (start.isdigit() and end.isdigit()):
            return None
        return f"{start}-{end[-2:]}"

    @staticmethod
    def _round_key(match: dict) -> str | None:
        matchday = match.get("matchday")
        if matchday is not None:
            return f"md-{matchday}"
        stage = str(match.get("stage") or "").strip().lower()
        return stage.replace("_", "-") or None

    def _convert(self, match: dict, competition: Competition,
                 clubs: ClubRegistry) -> dict:
        home = match.get("homeTeam") or {}
        away = match.get("awayTeam") or {}
        provider_match_id = str(match.get("id") or "")
        home_ref = str(home.get("id") or "")
        away_ref = str(away.get("id") or "")
        home_resolution = clubs.resolve(str(home.get("name") or ""),
                                        self.provider_name, home_ref)
        away_resolution = clubs.resolve(str(away.get("name") or ""),
                                        self.provider_name, away_ref)
        season = self._season_key(match)
        round_key = self._round_key(match)
        kickoff = str(match.get("utcDate") or "")
        blockers = []
        if home_resolution.status != "known":
            blockers.append("Heimclub nicht kanonisiert")
        if away_resolution.status != "known":
            blockers.append("Auswaertsclub nicht kanonisiert")
        if not season:
            blockers.append("Saison fehlt")
        if not round_key:
            blockers.append("Runde fehlt")
        if not kickoff:
            blockers.append("Anstosszeit fehlt")
        else:
            try:
                parsed_kickoff = dt.datetime.fromisoformat(kickoff.replace("Z", "+00:00"))
                if (parsed_kickoff.tzinfo is None or
                        parsed_kickoff.utcoffset() != dt.timedelta(0)):
                    blockers.append("Anstosszeit ist nicht UTC")
            except ValueError:
                blockers.append("Anstosszeit ist ungueltig")
        if not provider_match_id:
            blockers.append("Provider-Match-ID fehlt")

        fixture = None
        if not blockers:
            match_id = canonical_match_id(competition.key, season, round_key,
                                          home_resolution.club_id,
                                          away_resolution.club_id)
            fixture = CanonicalFixture(
                match_id, competition.key, season, round_key, kickoff,
                home_resolution.club_id, away_resolution.club_id,
                neutral=bool(match.get("neutralVenue", False)),
                provider_ids=(ProviderRef(self.provider_name, provider_match_id),),
            )

        return {
            "match_id": fixture.match_id if fixture else None,
            "identity_status": "canonical" if fixture else "pending",
            "identity_ready": bool(fixture),
            "model_status": "not_validated",
            "prediction_allowed": False,
            "value_allowed": False,
            "blockers": blockers,
            "provider": self.provider_name,
            "provider_match_id": provider_match_id,
            "competition": competition.key,
            "season": season,
            "round": round_key,
            "kickoff_utc": kickoff,
            "status": match.get("status"),
            "home": {"name": home.get("name"), "club_id": home_resolution.club_id,
                     "provider_id": home_ref},
            "away": {"name": away.get("name"), "club_id": away_resolution.club_id,
                     "provider_id": away_ref},
            "canonical_fixture": asdict(fixture) if fixture else None,
        }

    def fetch(self, competition: Competition, date_from: dt.date,
              date_to: dt.date, clubs: ClubRegistry) -> dict:
        if date_to < date_from:
            raise ValueError("date_to darf nicht vor date_from liegen")
        competition_id = self._competition_id(competition)
        if not competition_id:
            return {"status": "unavailable", "fixtures": [],
                    "source": self.provider_name,
                    "note": "Wettbewerb hat keine football-data-ID."}
        if not self.api_key:
            return {"status": "unavailable", "fixtures": [],
                    "source": self.provider_name,
                    "note": "Kein FOOTBALL_DATA_API_KEY gesetzt."}
        cache_path = self._cache_path(competition, date_from, date_to)
        try:
            response = self.http.get(
                f"{config.FOOTBALL_DATA_BASE}/competitions/{competition_id}/matches",
                params={"dateFrom": date_from.isoformat(), "dateTo": date_to.isoformat()},
                headers={"X-Auth-Token": self.api_key}, timeout=25)
            response.raise_for_status()
            payload = response.json()
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            fixtures = [self._convert(match, competition, clubs)
                        for match in payload.get("matches", [])]
            pending = sum(row["identity_status"] == "pending" for row in fixtures)
            return {"status": "live", "fixtures": fixtures,
                    "source": self.provider_name,
                    "source_captured_at": dt.datetime.now(dt.timezone.utc).isoformat(
                        timespec="seconds"),
                    "competition": competition.key,
                    "date_from": date_from.isoformat(), "date_to": date_to.isoformat(),
                    "n_fixtures": len(fixtures), "n_identity_pending": pending,
                    "note": "Shadow-Pilot; Value bleibt deaktiviert."}
        except Exception as exc:
            if cache_path.exists():
                try:
                    cached = json.loads(cache_path.read_text(encoding="utf-8"))
                    fixtures = [self._convert(match, competition, clubs)
                                for match in cached.get("matches", [])]
                    pending = sum(row["identity_status"] == "pending" for row in fixtures)
                    return {"status": "cached", "fixtures": fixtures,
                            "source": self.provider_name,
                            "competition": competition.key,
                            "date_from": date_from.isoformat(),
                            "date_to": date_to.isoformat(),
                            "n_fixtures": len(fixtures),
                            "n_identity_pending": pending,
                            "note": f"football-data.org-Fixture-Fehler: {exc}; Cache verwendet."}
                except Exception as cache_exc:
                    return {"status": "unavailable", "fixtures": [],
                            "source": self.provider_name,
                            "competition": competition.key,
                            "note": (f"football-data.org-Fixture-Fehler: {exc}; "
                                     f"Cache unlesbar: {cache_exc}")}
            return {"status": "unavailable", "fixtures": [],
                    "source": self.provider_name,
                    "competition": competition.key,
                    "note": f"football-data.org-Fixture-Fehler: {exc}"}

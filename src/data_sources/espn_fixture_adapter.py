"""Fixture-first-Adapter fuer ESPN-Scoreboards ohne API-Key.

ESPN ist eine inoffizielle kostenlose Quelle. Deshalb ist dieser Adapter nur
Shadow-Infrastruktur: Spiele duerfen sichtbar werden, aber Prognosen und Value
bleiben bis zur separaten Modellfreigabe gesperrt.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import asdict

import requests

from src.competition_registry import Competition
from src.domain import CanonicalFixture, ClubRegistry, ProviderRef, canonical_match_id


ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer"


class EspnFixtureAdapter:
    provider_name = "espn"

    def __init__(self, http=requests) -> None:
        self.http = http

    def _league_slug(self, competition: Competition) -> str | None:
        for ref in competition.provider_ids:
            if ref.provider == self.provider_name:
                return ref.provider_id
        return None

    @staticmethod
    def _date_range(date_from: dt.date, date_to: dt.date) -> str:
        return f"{date_from:%Y%m%d}-{date_to:%Y%m%d}"

    @staticmethod
    def _season_key(event: dict, league: dict | None = None) -> str | None:
        start = ((league or {}).get("season") or {}).get("startDate")
        end = ((league or {}).get("season") or {}).get("endDate")
        if start and end and str(start)[:4].isdigit() and str(end)[:4].isdigit():
            return f"{str(start)[:4]}-{str(end)[:4][-2:]}"
        year = str((event.get("season") or {}).get("year") or "")
        if year.isdigit():
            return f"{year}-{int(year[-2:]) + 1:02d}"
        return None

    @staticmethod
    def _round_key(event: dict) -> str | None:
        season = event.get("season") or {}
        slug = str(season.get("slug") or "").strip().lower()
        if slug:
            return slug.replace("_", "-")
        detail = str((((event.get("status") or {}).get("type") or {}).get("shortDetail")
                     or "")).strip().lower()
        if detail and detail != "scheduled":
            return "-".join(detail.split())
        return "scheduled"

    @staticmethod
    def _side(competition: dict, home_away: str) -> dict:
        for row in competition.get("competitors", []):
            if row.get("homeAway") == home_away:
                return row.get("team") or {}
        return {}

    def _convert(self, event: dict, competition: Competition, league: dict | None,
                 clubs: ClubRegistry) -> dict:
        comp = (event.get("competitions") or [{}])[0]
        home = self._side(comp, "home")
        away = self._side(comp, "away")
        provider_match_id = str(event.get("id") or comp.get("id") or "")
        kickoff = str(event.get("date") or comp.get("date") or comp.get("startDate") or "")
        home_ref = str(home.get("id") or "")
        away_ref = str(away.get("id") or "")
        home_name = str(home.get("displayName") or home.get("name") or "")
        away_name = str(away.get("displayName") or away.get("name") or "")
        home_resolution = clubs.resolve(home_name, self.provider_name, home_ref)
        away_resolution = clubs.resolve(away_name, self.provider_name, away_ref)
        season = self._season_key(event, league)
        round_key = self._round_key(event)
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
                neutral=bool(comp.get("neutralSite", False)),
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
            "status": ((event.get("status") or {}).get("type") or {}).get("description"),
            "home": {"name": home_name, "club_id": home_resolution.club_id,
                     "provider_id": home_ref},
            "away": {"name": away_name, "club_id": away_resolution.club_id,
                     "provider_id": away_ref},
            "canonical_fixture": asdict(fixture) if fixture else None,
        }

    def fetch(self, competition: Competition, date_from: dt.date,
              date_to: dt.date, clubs: ClubRegistry) -> dict:
        if date_to < date_from:
            raise ValueError("date_to darf nicht vor date_from liegen")
        league_slug = self._league_slug(competition)
        if not league_slug:
            return {"status": "unavailable", "fixtures": [],
                    "source": self.provider_name,
                    "note": "Wettbewerb hat keinen ESPN-Slug."}
        try:
            response = self.http.get(
                f"{ESPN_BASE}/{league_slug}/scoreboard",
                params={"dates": self._date_range(date_from, date_to)},
                headers={"User-Agent": "Mozilla/5.0"}, timeout=25)
            response.raise_for_status()
            payload = response.json()
            league = (payload.get("leagues") or [{}])[0]
            fixtures = [self._convert(event, competition, league, clubs)
                        for event in payload.get("events", [])]
            pending = sum(row["identity_status"] == "pending" for row in fixtures)
            return {"status": "live", "fixtures": fixtures,
                    "source": self.provider_name,
                    "source_captured_at": dt.datetime.now(dt.timezone.utc).isoformat(
                        timespec="seconds"),
                    "competition": competition.key,
                    "date_from": date_from.isoformat(), "date_to": date_to.isoformat(),
                    "n_fixtures": len(fixtures), "n_identity_pending": pending,
                    "note": "ESPN-Shadowquelle; Value bleibt deaktiviert."}
        except Exception as exc:
            return {"status": "unavailable", "fixtures": [],
                    "source": self.provider_name,
                    "competition": competition.key,
                    "note": f"ESPN-Fixture-Fehler: {exc}"}

"""Zentrale Wettbewerbs-Registry fuer den spaeteren Vereinsfussball-Shadowbetrieb."""
from __future__ import annotations

from dataclasses import dataclass
from zoneinfo import ZoneInfo

from src.domain import ProviderRef


_VALID_KEYS = set("abcdefghijklmnopqrstuvwxyz0123456789_")


@dataclass(frozen=True)
class Competition:
    key: str
    name: str
    country: str | None
    format: str
    timezone: str
    provider_ids: tuple[ProviderRef, ...]
    odds_keys: tuple[str, ...]
    fixture_sources: tuple[str, ...]
    home_advantage_policy: str = "model_default"
    knockout_rules: str = "none"
    include_qualifying: bool = False
    operation_mode: str = "shadow"

    def __post_init__(self) -> None:
        if not self.key or any(char not in _VALID_KEYS for char in self.key):
            raise ValueError("Wettbewerbsschluessel muss lowercase ASCII sein")
        if self.format not in ("league", "knockout", "hybrid"):
            raise ValueError(f"Unbekanntes Wettbewerbsformat: {self.format}")
        ZoneInfo(self.timezone)
        if self.operation_mode != "shadow":
            raise ValueError("Neue Wettbewerbe duerfen vor Freigabe nur shadow sein")
        if self.home_advantage_policy not in ("model_default", "neutral_zero"):
            raise ValueError("Unbekannte Heimvorteil-Policy")
        if not self.fixture_sources:
            raise ValueError("Mindestens eine Fixture-Quellenstrategie ist erforderlich")


class CompetitionRegistry:
    def __init__(self, competitions: tuple[Competition, ...]) -> None:
        self._by_key: dict[str, Competition] = {}
        self._by_provider: dict[tuple[str, str], Competition] = {}
        for competition in competitions:
            if competition.key in self._by_key:
                raise ValueError(f"Doppelter Wettbewerb: {competition.key}")
            self._by_key[competition.key] = competition
            for ref in competition.provider_ids:
                provider_key = (ref.provider.lower(), ref.provider_id)
                if provider_key in self._by_provider:
                    raise ValueError(f"Doppelte Provider-Wettbewerbs-ID: {provider_key}")
                self._by_provider[provider_key] = competition

    def get(self, key: str) -> Competition:
        return self._by_key[key]

    def by_provider(self, provider: str, provider_id: str) -> Competition | None:
        return self._by_provider.get((provider.strip().lower(), provider_id.strip()))

    def all(self) -> tuple[Competition, ...]:
        return tuple(self._by_key.values())


def _league(key: str, name: str, country: str, football_data_id: str,
            odds_key: str, timezone: str) -> Competition:
    return Competition(key, name, country, "league", timezone,
                       (ProviderRef("football_data", football_data_id),),
                       (odds_key,), ("football_data",))


COMPETITIONS = CompetitionRegistry((
    _league("premier_league", "Premier League", "England", "PL",
            "soccer_epl", "Europe/London"),
    _league("la_liga", "La Liga", "Spain", "PD",
            "soccer_spain_la_liga", "Europe/Madrid"),
    _league("bundesliga", "Bundesliga", "Germany", "BL1",
            "soccer_germany_bundesliga", "Europe/Berlin"),
    _league("serie_a", "Serie A", "Italy", "SA",
            "soccer_italy_serie_a", "Europe/Rome"),
    _league("ligue_1", "Ligue 1", "France", "FL1",
            "soccer_france_ligue_one", "Europe/Paris"),
    Competition("champions_league", "UEFA Champions League", None, "hybrid",
                "Europe/Zurich", (ProviderRef("football_data", "CL"),),
                ("soccer_uefa_champs_league",
                 "soccer_uefa_champs_league_qualification"),
                ("football_data",), knockout_rules="90m_and_advancement",
                include_qualifying=True),
    Competition("europa_league", "UEFA Europa League", None, "hybrid",
                "Europe/Zurich", (ProviderRef("espn", "uefa.europa"),),
                ("soccer_uefa_europa_league",), ("espn",),
                knockout_rules="90m_and_advancement",
                include_qualifying=True),
    Competition("conference_league", "UEFA Conference League", None, "hybrid",
                "Europe/Zurich", (ProviderRef("espn", "uefa.europa.conf"),),
                ("soccer_uefa_europa_conference_league",), ("espn",),
                knockout_rules="90m_and_advancement",
                include_qualifying=True),
))

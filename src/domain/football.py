"""Kanonische Club- und Spielidentitaeten ohne Provider-Kopplung."""
from __future__ import annotations

import datetime as dt
import hashlib
import re
import unicodedata
from dataclasses import dataclass


_KEY_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def _required_key(value: str, field: str) -> str:
    clean = (value or "").strip().lower()
    if not _KEY_RE.fullmatch(clean):
        raise ValueError(f"{field} muss ein stabiler ASCII-Schluessel sein")
    return clean


def _normalise_name(value: str) -> str:
    """Nur Unicode/Whitespace normieren; niemals Teilzeichenketten matchen."""
    clean = unicodedata.normalize("NFKC", value or "").strip().casefold()
    return " ".join(clean.split())


@dataclass(frozen=True)
class ProviderRef:
    provider: str
    provider_id: str

    def __post_init__(self) -> None:
        _required_key(self.provider, "provider")
        if not (self.provider_id or "").strip():
            raise ValueError("provider_id darf nicht leer sein")


@dataclass(frozen=True)
class Club:
    club_id: str
    canonical_name: str
    aliases: tuple[str, ...] = ()
    provider_ids: tuple[ProviderRef, ...] = ()

    def __post_init__(self) -> None:
        _required_key(self.club_id, "club_id")
        if not (self.canonical_name or "").strip():
            raise ValueError("canonical_name darf nicht leer sein")


@dataclass(frozen=True)
class ClubResolution:
    status: str
    club_id: str | None
    canonical_name: str
    prediction_allowed: bool


class ClubRegistry:
    """Exakte Alias-/Provider-ID-Aufloesung mit Kollisionsschutz."""

    def __init__(self, clubs: tuple[Club, ...] | list[Club]) -> None:
        self._clubs: dict[str, Club] = {}
        self._names: dict[str, Club] = {}
        self._provider_ids: dict[tuple[str, str], Club] = {}
        for club in clubs:
            if club.club_id in self._clubs:
                raise ValueError(f"Doppelte club_id: {club.club_id}")
            self._clubs[club.club_id] = club
            for raw_name in (club.canonical_name, *club.aliases):
                name_key = _normalise_name(raw_name)
                existing = self._names.get(name_key)
                if existing and existing.club_id != club.club_id:
                    raise ValueError(f"Club-Alias kollidiert: {raw_name}")
                self._names[name_key] = club
            for ref in club.provider_ids:
                provider_key = (ref.provider.strip().lower(), ref.provider_id.strip())
                existing = self._provider_ids.get(provider_key)
                if existing and existing.club_id != club.club_id:
                    raise ValueError(f"Provider-ID kollidiert: {provider_key}")
                self._provider_ids[provider_key] = club

    @staticmethod
    def _resolved(club: Club) -> ClubResolution:
        return ClubResolution("known", club.club_id, club.canonical_name, True)

    def resolve(self, name: str, provider: str | None = None,
                provider_id: str | None = None) -> ClubResolution:
        if provider and provider_id:
            club = self._provider_ids.get((provider.strip().lower(), provider_id.strip()))
            if club:
                return self._resolved(club)
        club = self._names.get(_normalise_name(name))
        if club:
            return self._resolved(club)
        # Unbekannte Clubs bleiben sichtbar, aber Prognose und Value sind gesperrt.
        return ClubResolution("unknown", None, (name or "").strip(), False)


def canonical_match_id(competition_key: str, season: str, round_key: str,
                       home_club_id: str, away_club_id: str, leg: int = 1) -> str:
    """Providerunabhaengige ID; ein verschobener Anstoss aendert sie nicht."""
    competition = _required_key(competition_key, "competition_key")
    home = _required_key(home_club_id, "home_club_id")
    away = _required_key(away_club_id, "away_club_id")
    if home == away:
        raise ValueError("Heim- und Auswaertsclub muessen verschieden sein")
    if not (season or "").strip() or not (round_key or "").strip():
        raise ValueError("season und round_key duerfen nicht leer sein")
    if leg < 1:
        raise ValueError("leg muss mindestens 1 sein")
    identity = "|".join((competition, season.strip(), round_key.strip().casefold(),
                         home, away, str(leg)))
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]
    return f"fx-{competition}-{digest}"


@dataclass(frozen=True)
class CanonicalFixture:
    match_id: str
    competition_key: str
    season: str
    round_key: str
    kickoff_utc: str
    home_club_id: str
    away_club_id: str
    neutral: bool = False
    leg: int = 1
    provider_ids: tuple[ProviderRef, ...] = ()

    def __post_init__(self) -> None:
        expected = canonical_match_id(self.competition_key, self.season,
                                      self.round_key, self.home_club_id,
                                      self.away_club_id, self.leg)
        if self.match_id != expected:
            raise ValueError("match_id passt nicht zur kanonischen Fixture-Identitaet")
        try:
            parsed = dt.datetime.fromisoformat(self.kickoff_utc.replace("Z", "+00:00"))
        except (AttributeError, ValueError) as exc:
            raise ValueError("kickoff_utc ist kein gueltiger ISO-Zeitpunkt") from exc
        if parsed.tzinfo is None or parsed.utcoffset() != dt.timedelta(0):
            raise ValueError("kickoff_utc muss explizit UTC sein")


def _utc_datetime(value: str, field: str) -> dt.datetime:
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise ValueError(f"{field} ist kein gueltiger ISO-Zeitpunkt") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != dt.timedelta(0):
        raise ValueError(f"{field} muss explizit UTC sein")
    return parsed


@dataclass(frozen=True)
class SourceTimestamp:
    source: str
    captured_at_utc: str

    def __post_init__(self) -> None:
        _required_key(self.source, "source")
        _utc_datetime(self.captured_at_utc, "captured_at_utc")


@dataclass(frozen=True)
class ReplaySnapshot:
    """Kompakter, offline wiederabspielbarer Stand eines kanonischen Spiels."""

    fixture: CanonicalFixture
    generated_at_utc: str
    model_version: str
    source_timestamps: tuple[SourceTimestamp, ...]
    replay_inputs: dict

    def __post_init__(self) -> None:
        _utc_datetime(self.generated_at_utc, "generated_at_utc")
        if not (self.model_version or "").strip():
            raise ValueError("model_version darf nicht leer sein")
        if not isinstance(self.replay_inputs, dict):
            raise ValueError("replay_inputs muss ein Dictionary sein")

    @property
    def eligible_for_learning(self) -> bool:
        generated = _utc_datetime(self.generated_at_utc, "generated_at_utc")
        kickoff = _utc_datetime(self.fixture.kickoff_utc, "kickoff_utc")
        return generated < kickoff


def select_last_pre_kickoff(snapshots: list[ReplaySnapshot]) -> ReplaySnapshot | None:
    """Leakage-Schutz: exakt den letzten Stand vor Anstoss auswaehlen."""
    if not snapshots:
        return None
    match_ids = {snapshot.fixture.match_id for snapshot in snapshots}
    if len(match_ids) != 1:
        raise ValueError("Snapshots verschiedener Spiele duerfen nicht gemischt werden")
    eligible = [snapshot for snapshot in snapshots if snapshot.eligible_for_learning]
    if not eligible:
        return None
    return max(eligible, key=lambda snapshot: _utc_datetime(
        snapshot.generated_at_utc, "generated_at_utc"))

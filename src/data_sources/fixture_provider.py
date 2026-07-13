"""Gemeinsamer Vertrag fuer Fixture-first-Datenquellen."""
from __future__ import annotations

import datetime as dt
from typing import Protocol

from src.competition_registry import Competition
from src.domain import ClubRegistry


class FixtureProvider(Protocol):
    provider_name: str

    def fetch(self, competition: Competition, date_from: dt.date,
              date_to: dt.date, clubs: ClubRegistry) -> dict:
        """Status-getaggte Fixtures liefern; Fehler duerfen nicht nach aussen werfen."""
        ...

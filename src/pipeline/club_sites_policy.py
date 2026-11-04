"""Reine Zeit- und Budgetregeln der privaten Club-Site."""
from __future__ import annotations

import calendar
import datetime as dt
from zoneinfo import ZoneInfo

BERLIN = ZoneInfo("Europe/Berlin")
UTC = dt.timezone.utc
HOURS = (9, 14, 18)
COMPETITIONS = ("bundesliga", "champions_league", "serie_a", "la_liga", "premier_league")


def parse_time(value: str) -> dt.datetime:
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Zeitpunkt braucht eine Zeitzone")
    return parsed.astimezone(UTC)


def scheduled_slot(now: dt.datetime) -> str | None:
    """Verspätungen bis zwei Stunden zulassen; Sommer-/Wintertrigger deduplizieren."""
    local = now.astimezone(BERLIN)
    for hour in reversed(HOURS):
        slot = local.replace(hour=hour, minute=0, second=0, microsecond=0)
        if dt.timedelta(0) <= local - slot < dt.timedelta(hours=2):
            return f"{local.date().isoformat()}@{hour:02d}"
    return None


def next_update(now: dt.datetime) -> str:
    local = now.astimezone(BERLIN)
    for offset in (0, 1):
        day = local.date() + dt.timedelta(days=offset)
        for hour in HOURS:
            candidate = dt.datetime.combine(day, dt.time(hour), BERLIN)
            if candidate > local:
                return candidate.astimezone(UTC).isoformat(timespec="seconds")
    raise AssertionError("Folgetag enthält immer einen Slot")


def eligible_competitions(fixtures: list[dict], now: dt.datetime) -> list[str]:
    nearest: dict[str, dt.datetime] = {}
    for fixture in fixtures:
        try:
            kickoff = parse_time(fixture["kickoff_utc"])
        except (ValueError, KeyError, TypeError):
            continue
        key = fixture.get("competition")
        if (key in COMPETITIONS and is_pre_match(fixture, now) and
                kickoff.astimezone(BERLIN).date() == now.astimezone(BERLIN).date()):
            nearest[key] = min(nearest.get(key, kickoff), kickoff)
    return sorted(nearest, key=lambda key: (nearest[key], key))


def is_pre_match(fixture: dict, now: dt.datetime) -> bool:
    status = str(fixture.get("fixture_status") or fixture.get("status") or "SCHEDULED").upper()
    if status not in ("SCHEDULED", "TIMED", "NOT_STARTED", "NOTSTARTED"):
        return False
    try:
        return parse_time(fixture["kickoff_utc"]) > now
    except (ValueError, KeyError, TypeError):
        return False


def budget_capacity(remaining: int | None, now: dt.datetime, cost: int = 2) -> int:
    """Konservativ über restliche Kalendertage/Slots verteilen, ohne Mehrkosten."""
    if type(remaining) is not int or remaining < cost or cost < 1:
        return 0
    local = now.astimezone(BERLIN)
    days_left = calendar.monthrange(local.year, local.month)[1] - local.day
    today_left = sum(hour >= local.hour for hour in HOURS) or 1
    slots_left = days_left * len(HOURS) + today_left
    return max(0, remaining // max(cost * slots_left, cost))

"""Separater Fixture-first-Shadowlauf; veraendert den WM-Daily-Run nicht."""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

from src import config
from src.club_registry import load_club_registry
from src.competition_registry import COMPETITIONS
from src.data_sources.espn_fixture_adapter import EspnFixtureAdapter
from src.data_sources.football_data_fixture_adapter import FootballDataFixtureAdapter


DEFAULT_OUTPUT = config.DATA_PROCESSED / "club_shadow_fixtures.json"
DEFAULT_ALL_OUTPUT = config.DATA_PROCESSED / "club_shadow_competitions.json"


def _validate_output(output_path: Path) -> None:
    protected_outputs = {
        (config.DATA_PROCESSED / "dashboard_data.json").resolve(),
        (config.PROJECT_ROOT / "docs" / "index.html").resolve(),
    }
    if output_path.resolve() in protected_outputs:
        raise ValueError("Shadowlauf darf keine produktive WM-Ausgabe ueberschreiben")


def _write(payload: dict, output_path: Path) -> None:
    _validate_output(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                           encoding="utf-8")


def _default_adapter(competition):
    if competition.fixture_sources and competition.fixture_sources[0] == "espn":
        return EspnFixtureAdapter()
    return FootballDataFixtureAdapter()


def run(competition_key: str = "premier_league", days: int = 7,
        today: dt.date | None = None, output_path: Path = DEFAULT_OUTPUT,
        adapter: FootballDataFixtureAdapter | None = None) -> dict:
    if days < 1:
        raise ValueError("days muss mindestens 1 sein")
    competition = COMPETITIONS.get(competition_key)
    if competition.operation_mode != "shadow":
        raise ValueError("Vereinswettbewerbe duerfen vor Freigabe nur shadow laufen")
    _validate_output(output_path)
    start = today or dt.datetime.now(dt.timezone.utc).date()
    end = start + dt.timedelta(days=days - 1)
    result = (adapter or _default_adapter(competition)).fetch(
        competition, start, end, load_club_registry())
    payload = {**result,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "mode": "shadow", "auto_apply": False,
        "competition": competition_key,
        "window_days": days,
    }
    _write(payload, output_path)
    return payload


def run_all(days: int = 7, today: dt.date | None = None,
            output_path: Path = DEFAULT_ALL_OUTPUT,
            adapter: FootballDataFixtureAdapter | None = None,
            competition_keys: tuple[str, ...] | None = None) -> dict:
    if days < 1:
        raise ValueError("days muss mindestens 1 sein")
    _validate_output(output_path)
    start = today or dt.datetime.now(dt.timezone.utc).date()
    end = start + dt.timedelta(days=days - 1)
    clubs = load_club_registry()
    keys = competition_keys or tuple(competition.key for competition in COMPETITIONS.all())
    results = {}
    for key in keys:
        try:
            competition = COMPETITIONS.get(key)
            if competition.operation_mode != "shadow":
                raise ValueError("Wettbewerb ist nicht im Shadowmodus")
            provider = adapter or _default_adapter(competition)
            source_result = provider.fetch(competition, start, end, clubs)
        except Exception as exc:
            source_result = {"status": "unavailable", "fixtures": [],
                             "note": f"Shadow-Fixture-Fehler: {exc}"}
        results[key] = {**source_result, "competition": key,
                        "mode": "shadow", "auto_apply": False}

    statuses = [result.get("status") for result in results.values()]
    live_count = sum(status == "live" for status in statuses)
    total_fixtures = sum(len(result.get("fixtures", [])) for result in results.values())
    total_pending = sum(result.get("n_identity_pending", 0) or 0
                        for result in results.values())
    overall_status = ("live" if statuses and live_count == len(statuses)
                      else ("degraded" if live_count else "unavailable"))
    payload = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "status": overall_status, "mode": "shadow", "auto_apply": False,
        "date_from": start.isoformat(), "date_to": end.isoformat(),
        "window_days": days, "n_competitions": len(results),
        "n_live_competitions": live_count, "n_fixtures": total_fixtures,
        "n_identity_pending": total_pending, "competitions": results,
    }
    _write(payload, output_path)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Fixture-first Vereinsfussball-Shadowlauf")
    parser.add_argument("--competition", default="premier_league")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--all", action="store_true", help="Alle Registry-Wettbewerbe laden")
    args = parser.parse_args()
    if args.all:
        result = run_all(args.days)
        print(f"Shadowlauf alle: {result['n_fixtures']} Fixtures aus "
              f"{result['n_live_competitions']}/{result['n_competitions']} Quellen, "
              f"Status {result['status']}")
    else:
        result = run(args.competition, args.days)
        print(f"Shadowlauf {result['competition']}: {result.get('n_fixtures', 0)} Fixtures, "
              f"Status {result['status']}")


if __name__ == "__main__":
    main()

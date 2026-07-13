"""Separater Fixture-first-Shadowlauf; veraendert den WM-Daily-Run nicht."""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

from src import config
from src.club_registry import load_club_registry
from src.competition_registry import COMPETITIONS
from src.data_sources.football_data_fixture_adapter import FootballDataFixtureAdapter


DEFAULT_OUTPUT = config.DATA_PROCESSED / "club_shadow_fixtures.json"


def run(competition_key: str = "premier_league", days: int = 7,
        today: dt.date | None = None, output_path: Path = DEFAULT_OUTPUT,
        adapter: FootballDataFixtureAdapter | None = None) -> dict:
    if days < 1:
        raise ValueError("days muss mindestens 1 sein")
    competition = COMPETITIONS.get(competition_key)
    if competition.operation_mode != "shadow":
        raise ValueError("Vereinswettbewerbe duerfen vor Freigabe nur shadow laufen")
    protected_outputs = {
        (config.DATA_PROCESSED / "dashboard_data.json").resolve(),
        (config.PROJECT_ROOT / "docs" / "index.html").resolve(),
    }
    if output_path.resolve() in protected_outputs:
        raise ValueError("Shadowlauf darf keine produktive WM-Ausgabe ueberschreiben")
    start = today or dt.datetime.now(dt.timezone.utc).date()
    end = start + dt.timedelta(days=days - 1)
    result = (adapter or FootballDataFixtureAdapter()).fetch(
        competition, start, end, load_club_registry())
    payload = {**result,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "mode": "shadow", "auto_apply": False,
        "competition": competition_key,
        "window_days": days,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                           encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Fixture-first Vereinsfussball-Shadowlauf")
    parser.add_argument("--competition", default="premier_league")
    parser.add_argument("--days", type=int, default=7)
    args = parser.parse_args()
    result = run(args.competition, args.days)
    print(f"Shadowlauf {result['competition']}: {result.get('n_fixtures', 0)} Fixtures, "
          f"Status {result['status']}")


if __name__ == "__main__":
    main()

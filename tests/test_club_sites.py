"""Verträge für die private Club-Site, ohne externe Datenabrufe."""
import datetime as dt

from src.pipeline.club_sites_policy import (
    budget_capacity, eligible_competitions, next_update, scheduled_slot,
)
from src.data_sources.club_odds_client import normalize_event, find_event


def utc(value):
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def test_slots_follow_berlin_dst_and_ignore_early_runs():
    assert scheduled_slot(utc("2026-01-10T08:17:00Z")) == "2026-01-10@09"
    assert scheduled_slot(utc("2026-07-10T07:17:00Z")) == "2026-07-10@09"
    assert scheduled_slot(utc("2026-07-10T06:17:00Z")) is None
    assert scheduled_slot(utc("2026-07-10T09:17:00Z")) is None
    assert next_update(utc("2026-07-10T12:17:00Z")) == "2026-07-10T16:00:00+00:00"


def test_eligible_only_today_and_before_kickoff_nearest_first():
    now = utc("2026-11-04T13:17:00Z")
    fixtures = [
        {"competition": "bundesliga", "kickoff_utc": "2026-11-04T18:00:00Z"},
        {"competition": "serie_a", "kickoff_utc": "2026-11-04T14:00:00Z"},
        {"competition": "la_liga", "kickoff_utc": "2026-11-04T12:00:00Z"},
        {"competition": "premier_league", "kickoff_utc": "2026-11-05T14:00:00Z"},
    ]
    assert eligible_competitions(fixtures, now) == ["serie_a", "bundesliga"]


def test_budget_is_fail_closed_paced_and_never_exceeds_remaining():
    now = utc("2026-11-01T08:17:00Z")
    assert budget_capacity(None, now) == 0
    assert budget_capacity(-2, now) == 0
    assert budget_capacity(500, now) == 2
    assert budget_capacity(1, now) == 0
    assert budget_capacity(4, utc("2026-11-30T17:17:00Z")) == 2


def event():
    return {"id": "odds-1", "home_team": "Arsenal", "away_team": "Chelsea",
            "commence_time": "2026-11-04T20:00:00Z", "bookmakers": [
        {"key": "book_a", "title": "Book A", "last_update": "2026-11-04T13:00:00Z",
         "markets": [
            {"key": "h2h", "outcomes": [{"name": "Arsenal", "price": 2.0},
              {"name": "Draw", "price": 3.5}, {"name": "Chelsea", "price": 4.0}]},
            {"key": "totals", "outcomes": [{"name": "Over", "point": 2.5, "price": 1.8},
              {"name": "Under", "point": 2.5, "price": 2.1}]},
         ]},
        {"key": "book_b", "title": "Book B", "markets": [
            {"key": "totals", "outcomes": [{"name": "Over", "point": 3.5, "price": 2.2},
              {"name": "Under", "point": 3.5, "price": 1.7}]},
         ]},
    ]}


def test_totals_lines_stay_separate_and_quotes_have_provenance():
    normalized = normalize_event(event(), "2026-11-04T13:17:00+00:00")
    assert len(normalized["quotes"]) == 7
    over = [q for q in normalized["quotes"] if q["selection"] == "over"]
    assert {q["point"] for q in over} == {2.5, 3.5}
    assert all(q["bookmaker"] and q["fetched_at"] for q in over)
    assert abs(sum(normalized["market_probs"].values()) - 1) < 1e-9
    assert "model_probs" not in normalized


def test_odds_matching_is_ordered_unique_and_kickoff_specific():
    fixture = {"home": {"name": "Arsenal", "club_id": "arsenal"},
               "away": {"name": "Chelsea", "club_id": "chelsea"},
               "kickoff_utc": "2026-11-04T20:00:00Z"}
    assert find_event(fixture, [event()])["id"] == "odds-1"
    assert find_event(fixture, [event(), event()]) is None
    wrong = {**event(), "commence_time": "2026-11-05T20:00:00Z"}
    assert find_event(fixture, [wrong]) is None
    flipped = {**event(), "home_team": "Chelsea", "away_team": "Arsenal"}
    assert find_event(fixture, [flipped]) is None


def fixture_payload():
    return {"competitions": {"premier_league": {"status": "live", "source": "football_data",
        "fixtures": [{"match_id": "fx-arsenal-chelsea", "identity_status": "canonical",
            "provider_match_id": "123", "provider": "football_data", "competition": "premier_league",
            "kickoff_utc": "2026-11-04T20:00:00Z", "status": "TIMED",
            "home": {"name": "Arsenal", "club_id": "arsenal"},
            "away": {"name": "Chelsea", "club_id": "chelsea"}, "blockers": []}]}}}


class FakeStore:
    def __init__(self):
        self.claimed = False
        self.remaining = 500
        self.reservations = 0

    def claim(self, slot):
        previous, self.claimed = self.claimed, True
        return not previous

    def observe(self, quota):
        self.remaining = min(self.remaining, quota["remaining"])
        return {"quota": {"status": "verified", "remaining": self.remaining, "used": 500-self.remaining}}

    def reserve(self, slot, competition):
        self.reservations += 1
        self.remaining -= 2
        return {"reserved": True, "quota": {"remaining": self.remaining, "used": 500-self.remaining}}

    def state(self):
        return {"quota": {"status": "verified", "remaining": self.remaining, "used": 500-self.remaining}}


class FakeOdds:
    def __init__(self, quota=True):
        self.calls = 0
        self.quota = quota

    def probe(self):
        return {"remaining": 500, "used": 0} if self.quota else None

    def fetch(self, sport_key):
        self.calls += 1
        return {"status": "live", "events": [event()], "quota": {"remaining": 498, "used": 2}}


def test_collector_deduplicates_slots_and_keeps_model_gates_closed():
    from src.pipeline.club_sites_run import collect
    store, odds = FakeStore(), FakeOdds()
    now = utc("2026-11-04T13:17:00Z")
    result = collect(fixture_payload(), now, odds, store)
    assert result["matches"][0]["quotes"]
    assert result["matches"][0]["model"] is None
    assert result["gates"] == {"prediction_allowed": False, "value_allowed": False}
    assert collect(fixture_payload(), now, odds, store) is None
    assert odds.calls == store.reservations == 1


def test_unknown_quota_still_publishes_fixtures_without_paid_calls():
    from src.pipeline.club_sites_run import collect
    odds = FakeOdds(quota=False)
    result = collect(fixture_payload(), utc("2026-11-04T13:17:00Z"), odds, FakeStore())
    assert len(result["matches"]) == 1
    assert result["matches"][0]["odds_status"] == "budget_limited"
    assert result["quota"]["status"] == "unknown"
    assert odds.calls == 0


def test_legacy_wm_odds_stop_after_cloud_handover(monkeypatch, tmp_path):
    from src import config
    from src.data_sources import odds_client
    monkeypatch.setattr(config, "DATA_PROCESSED", tmp_path)
    monkeypatch.setattr(config, "ODDS_API_KEY", "not-a-real-key")
    (tmp_path / "club_sites_odds_owner.json").write_text('{"owner":"cloud"}', encoding="utf-8")
    def unexpected(*args, **kwargs):
        raise AssertionError("Lokaler WM-Pfad darf keine Quoten mehr abrufen")
    monkeypatch.setattr(odds_client.requests, "get", unexpected)
    assert odds_client.fetch_all_odds(force=True)["status"] == "managed_by_cloud"


def test_club_diagnostics_reject_future_training_and_unknown_teams():
    from src.model.club_sites_model import diagnostic_forecast
    history = [{"date": "2026-11-05", "home_team": "Arsenal", "away_team": "Chelsea",
                "home_score": 1, "away_score": 0}] * 110
    result = diagnostic_forecast(history, "Arsenal", "Chelsea", utc("2026-11-04T13:17:00Z"))
    assert result["status"] == "insufficient_data"
    old = [{**m, "date": "2026-10-01"} for m in history]
    unknown = diagnostic_forecast(old, "Unbekannt", "Chelsea", utc("2026-11-04T13:17:00Z"))
    assert unknown["status"] == "unknown_team"
    known = diagnostic_forecast(old, "Arsenal", "Chelsea", utc("2026-11-04T13:17:00Z"))
    assert known["prediction_allowed"] is False
    assert known["value_allowed"] is False
    assert abs(sum(known["diagnostic_probs"].values()) - 1) < 1e-9


def test_collector_never_attaches_live_odds_to_already_started_game():
    from src.pipeline.club_sites_run import collect
    payload = fixture_payload()
    later = payload["competitions"]["premier_league"]["fixtures"][0]
    started = {**later, "match_id": "already-started", "provider_match_id": "old",
               "kickoff_utc": "2026-11-04T12:00:00Z", "status": "IN_PLAY"}
    payload["competitions"]["premier_league"]["fixtures"].append(started)
    class LiveOdds(FakeOdds):
        def fetch(self, key):
            result = super().fetch(key)
            result["events"].append({**event(), "id": "live-odds", "commence_time": "2026-11-04T12:00:00Z"})
            return result
    run = collect(payload, utc("2026-11-04T13:17:00Z"), LiveOdds(), FakeStore())
    old = next(m for m in run["matches"] if m["id"] == "already-started")
    assert old["quotes"] == []
    assert old["market_probs"] is None


def test_fixture_cache_without_capture_time_stays_unknown_and_stale():
    from src.pipeline.club_sites_run import collect
    payload = fixture_payload()
    payload["competitions"]["premier_league"]["status"] = "cached"
    result = collect(payload, utc("2026-11-04T13:17:00Z"), FakeOdds(quota=False), FakeStore())
    assert result["matches"][0]["fixture_fetched_at"] is None
    assert result["sources"]["premier_league"]["status"] == "stale"
    assert "fetched_at" not in result["sources"]["premier_league"]


def test_kickoff_during_provider_request_uses_actual_response_time():
    from src.pipeline.club_sites_run import collect
    payload = fixture_payload()
    payload["competitions"]["premier_league"]["fixtures"][0]["kickoff_utc"] = "2026-11-04T14:00:00Z"
    clock = {"now": utc("2026-11-04T13:59:50Z")}
    class SlowOdds(FakeOdds):
        def fetch(self, key):
            result = super().fetch(key)
            result["events"][0]["commence_time"] = "2026-11-04T14:00:00Z"
            clock["now"] = utc("2026-11-04T14:00:05Z")
            return result
    run = collect(payload, clock["now"], SlowOdds(), FakeStore(), clock=lambda: clock["now"])
    assert run["matches"][0]["quotes"] == []

import concurrent.futures
import json
import shutil
from pathlib import Path

import pytest

from src.domain import canonical_match_id
from src.model import club_lockbox as lockbox


VERSION = "closing_residual_v1"
KICKOFF = "2026-08-15T14:00:00Z"
CAPTURED = "2026-08-15T13:54:50Z"
HASH_A, HASH_B, HASH_C, HASH_D = (char * 64 for char in "abcd")
MATCH1 = canonical_match_id("premier_league", "2026-27", "md-1", "arsenal", "chelsea")
MATCH2 = canonical_match_id("premier_league", "2026-27", "md-1", "liverpool", "man_city")
TEST_CLOCK = {"now": "2026-08-15T13:54:57Z"}


@pytest.fixture(autouse=True)
def trusted_receipt_clock(monkeypatch):
    monkeypatch.setattr(lockbox, "_now_utc", lambda: lockbox._utc(
        TEST_CLOCK["now"], "test_now"))
    TEST_CLOCK["now"] = "2026-08-15T13:54:57Z"


def protocol(version=VERSION):
    params = {league: {"alpha": 0.1, "temperature": 1.0, "draw_multiplier": 1.0}
              for league in lockbox.REQUIRED_LEAGUES}
    return {
        "lockbox_id": "club-edge-lockbox", "epoch_id": f"epoch-{version[-2:]}",
        "candidate_name": "closing_residual_blend", "candidate_version": version,
        "frozen_at_utc": "2026-07-20T12:00:00Z", "git_commit": "deadbeef",
        "code_sha256": HASH_A,
        "config": {"sha256": HASH_B, "parameter_grid": {"alpha": [0, 0.1]},
                   "defaults": {"cutoff_minutes": 5}, "frozen_parameters": params},
        "model": {"sha256": HASH_C, "model_version": "club-model-v1",
                  "features": ["ratings", "form"]},
        "training": {"sha256": HASH_D, "period": "2021-2026",
                     "max_information_at_utc": "2026-06-30T23:59:59Z",
                     "files": [{"path": "history.csv", "sha256": HASH_A}]},
        "population": {"required_leagues": list(lockbox.REQUIRED_LEAGUES),
                       "season_epoch": "2026-27", "inclusion_rules": ["regular_final_1x2"]},
        "market": {"source": "the_odds_api", "book_whitelist": ["pinnacle", "bet365"],
                   "source_priority": ["pinnacle", "bet365"], "devig_method": "proportional",
                   "consensus_method": "mean", "official_closing_source": "official_odds",
                   "missing_policy": "unpaired_counts_against_coverage"},
        "capture": {"policy": "fixed_t_minus_5", "minutes_before_kickoff": 5,
                    "boundary": "strictly_before", "max_staleness_seconds": 120,
                    "binding": "same_capture_for_candidate_raw_alpha0"},
        "benchmarks": {"raw_closing": {"source": "same_capture"},
                       "alpha0_calibrator": {"temperature": 1.0, "draw_multiplier": 1.0,
                                              "by_competition": {}}},
        "results": {"authoritative_source": "football_data",
                    "min_match_duration_seconds": 5400,
                    "finality_rule": "final_after_finished_at"},
        "inference": {"metrics": ["rps", "log_loss"], "bootstrap_iterations": 10000,
                      "bootstrap_seed": 20260720, "confidence_level": 0.95,
                      "cluster": "league_x_season_x_matchday_fallback_league_x_date"},
        "gates": {"coverage": 0.98, "diagnostic_total": 3000,
                  "diagnostic_per_league": 500, "definitive_total": 15000,
                  "definitive_per_league": 1500, "league_wins_required": 4},
        "guardrails": {"groups": ["draw", "promoted", "first_six"],
                       "rps_upper_limit": 0.002, "log_loss_upper_limit": 0.01,
                       "minimum_n": 30},
        "evaluation_schedule": [
            {"checkpoint_id": "cp-1", "opens_at_utc": "2026-08-15T16:00:00Z",
             "closes_at_utc": "2026-08-15T16:10:00Z"},
            {"checkpoint_id": "cp-2", "opens_at_utc": "2026-08-16T16:00:00Z",
             "closes_at_utc": "2026-08-16T16:10:00Z"}],
    }


def make_manifest(root, version=VERSION):
    return lockbox.create_manifest(root, protocol(version))


def fixture(match_id=MATCH1, league="premier_league", matchday=1):
    home, away = (("liverpool", "man_city") if match_id == MATCH2
                  else ("arsenal", "chelsea"))
    return {"match_id": match_id, "competition": league, "season": "2026-27",
            "matchday": matchday, "scheduled_kickoff_utc": KICKOFF,
            "home_club_id": home, "away_club_id": away, "eligible": True}


def make_population(root, fixtures=None, version=VERSION):
    return lockbox.write_population(root, {"candidate_version": version,
        "frozen_at_utc": "2026-07-20T12:05:00Z", "fixtures": fixtures or [fixture()]})


def alpha0(raw=None):
    return raw or {"team1_win": 0.4, "draw": 0.3, "team2_win": 0.3}


def forecast(match_id=MATCH1, version=VERSION, league="premier_league",
             capture_id="capture-1", generated="2026-08-15T13:54:55Z", extra=None):
    TEST_CLOCK["now"] = "2026-08-15T13:54:57Z"
    raw = {"team1_win": 0.4, "draw": 0.3, "team2_win": 0.3}
    base = {"team1_win": 0.7, "draw": 0.2, "team2_win": 0.1}
    candidate = {key: 0.9 * raw[key] + 0.1 * base[key] for key in lockbox.OUTCOMES}
    record = {"candidate_version": version, "match_id": match_id,
        "forecast_id": match_id, "capture_id": capture_id, "competition": league,
        "season": "2026-27", "matchday": 1, "promoted_match": False,
        "scheduled_kickoff_utc": KICKOFF, "generated_at_utc": generated,
        "model_version": "club-model-v1", "git_commit": "deadbeef",
        "code_sha256": HASH_A, "config_sha256": HASH_B, "model_sha256": HASH_C,
        "training_sha256": HASH_D, "base_model_probs": base, "raw_market_probs": raw,
        "alpha0_probs": raw, "candidate_probs": candidate,
        "candidate_parameters": {"alpha": 0.1, "temperature": 1.0, "draw_multiplier": 1.0},
        "source_timestamps": {"market": CAPTURED, "features": "2026-08-15T13:50:00Z"},
        "quality_status": "complete", "mode": "shadow", "auto_apply": False,
        "prediction_allowed": False, "value_allowed": False, "stake_allowed": False}
    if extra:
        record.update(extra)
    return record


def closing(match_id=MATCH1, version=VERSION, capture_id="capture-1",
            captured=CAPTURED):
    TEST_CLOCK["now"] = "2026-08-15T13:54:57Z"
    return {"candidate_version": version, "match_id": match_id, "closing_id": match_id,
        "capture_id": capture_id, "scheduled_kickoff_utc": KICKOFF,
        "source_captured_at_utc": captured, "captured_at_utc": captured,
        "source": "the_odds_api", "status": "complete", "books": ["pinnacle", "bet365"],
        "raw_quotes": {"pinnacle": {"team1_win": 2.5, "draw": 10/3, "team2_win": 10/3},
                       "bet365": {"team1_win": 2.5, "draw": 10/3, "team2_win": 10/3}},
        "devig_method": "proportional", "consensus_method": "mean",
        "raw_closing_probs": {"team1_win": 0.4, "draw": 0.3, "team2_win": 0.3},
        "mode": "shadow", "auto_apply": False, "prediction_allowed": False,
        "value_allowed": False, "stake_allowed": False}


def result(match_id=MATCH1, version=VERSION, captured="2026-08-15T16:00:00Z",
           finished="2026-08-15T15:35:00Z"):
    TEST_CLOCK["now"] = "2026-08-15T16:01:00Z"
    return {"candidate_version": version, "match_id": match_id, "result_id": match_id,
        "status": "FINAL", "outcome": "team1_win", "home_goals": 2, "away_goals": 1,
        "captured_at_utc": captured, "actual_kickoff_utc": KICKOFF,
        "finished_at_utc": finished,
        "source": "football_data", "mode": "shadow", "auto_apply": False,
        "prediction_allowed": False, "value_allowed": False, "stake_allowed": False}


def setup_epoch(root, fixtures=None, version=VERSION):
    make_manifest(root, version)
    make_population(root, fixtures, version)


def write_complete_match(root, match_id=MATCH1, version=VERSION,
                         league="premier_league"):
    lockbox.write_forecast(root, forecast(match_id, version, league))
    lockbox.write_closing(root, closing(match_id, version))
    lockbox.write_result(root, result(match_id, version))


def test_manifest_is_normative_hashed_create_only_and_idempotent(tmp_path):
    first, second = make_manifest(tmp_path), make_manifest(tmp_path)
    assert first["write_status"] == "created"
    assert second["write_status"] == "idempotent"
    assert len(first["manifest_sha256"]) == len(first["protocol_sha256"]) == 64
    assert first["gates"]["coverage"] == 0.98
    assert first["inference"]["bootstrap_iterations"] >= 10000
    assert first["release_status"] == "blocked" and first["auto_apply"] is False


def test_manifest_rejects_weakened_normative_thresholds(tmp_path):
    bad = protocol()
    bad["inference"]["bootstrap_iterations"] = 100
    with pytest.raises(lockbox.ValidationError, match="Inferenzplan"):
        lockbox.create_manifest(tmp_path, bad)
    bad = protocol()
    bad["gates"]["coverage"] = 0.5
    with pytest.raises(lockbox.ValidationError, match="Gate-Schwellen"):
        lockbox.create_manifest(tmp_path, bad)


def test_manifest_rejects_malformed_unsorted_or_duplicate_checkpoints(tmp_path):
    for schedule in ([{"checkpoint_id": "cp", "opens_at_utc": "bad",
                       "closes_at_utc": "2027-01-01T01:00:00Z"}],
                     [{"checkpoint_id": "cp", "opens_at_utc": "2027-01-01T00:00:00Z",
                       "closes_at_utc": "2027-01-01T01:00:00Z"},
                      {"checkpoint_id": "cp", "opens_at_utc": "2027-02-01T00:00:00Z",
                       "closes_at_utc": "2027-02-01T01:00:00Z"}],
                     [{"checkpoint_id": "late", "opens_at_utc": "2027-02-01T00:00:00Z",
                       "closes_at_utc": "2027-02-01T01:00:00Z"},
                      {"checkpoint_id": "early", "opens_at_utc": "2027-01-01T00:00:00Z",
                       "closes_at_utc": "2027-01-01T01:00:00Z"}]):
        bad = protocol()
        bad["evaluation_schedule"] = schedule
        with pytest.raises((lockbox.ValidationError, ValueError)):
            lockbox.create_manifest(tmp_path, bad)


def test_epoch_registry_rejects_second_candidate_in_active_epoch(tmp_path):
    make_manifest(tmp_path)
    changed = protocol("closing_residual_v2")
    changed["epoch_id"] = protocol()["epoch_id"]
    with pytest.raises(lockbox.ArtifactConflictError):
        lockbox.create_manifest(tmp_path, changed)


def test_population_is_create_only_and_requires_exact_top5_manifest(tmp_path):
    make_manifest(tmp_path)
    first = make_population(tmp_path)
    assert first["write_status"] == "created"
    changed = fixture(MATCH2)
    with pytest.raises(lockbox.ArtifactConflictError):
        make_population(tmp_path, [changed])


def test_population_ledger_not_forecasts_is_coverage_denominator(tmp_path):
    setup_epoch(tmp_path, [fixture(MATCH1), fixture(MATCH2)])
    write_complete_match(tmp_path, MATCH1)
    evaluated = lockbox.evaluate(tmp_path, evaluation_mode="test")
    assert evaluated["n_population"] == 2 and evaluated["n_forecasts"] == 1
    assert evaluated["n_paired"] == 1 and evaluated["coverage"] == 0.5
    assert evaluated["missing"] == [{"match_id": MATCH2,
                                      "missing": ["forecast", "closing", "result"]}]
    assert evaluated["gates"]["artifact_completeness"] is False


def test_deleted_forecast_never_improves_coverage_and_blocks_completeness(tmp_path):
    setup_epoch(tmp_path)
    written = lockbox.write_forecast(tmp_path, forecast())
    lockbox.write_closing(tmp_path, closing())
    lockbox.write_result(tmp_path, result())
    Path(written["path"]).unlink()
    evaluated = lockbox.evaluate(tmp_path, evaluation_mode="test")
    assert evaluated["n_population"] == 1 and evaluated["n_forecasts"] == 0
    assert evaluated["coverage"] == 0.0
    assert evaluated["artifact_completeness"] is False
    assert evaluated["integrity_ok"] is True
    assert evaluated["gates"]["release"] is False


@pytest.mark.parametrize("bad_time", ["2026-08-15T13:00:00", "2026-08-15T15:00:00+01:00"])
def test_forecast_requires_explicit_utc(tmp_path, bad_time):
    setup_epoch(tmp_path)
    with pytest.raises(lockbox.ValidationError, match="UTC"):
        lockbox.write_forecast(tmp_path, forecast(generated=bad_time))


@pytest.mark.parametrize("at", ["2026-08-15T13:55:00Z", "2026-08-15T13:55:01Z"])
def test_forecast_rejects_exact_or_post_cutoff(tmp_path, at):
    setup_epoch(tmp_path)
    with pytest.raises(lockbox.ValidationError, match="T-5"):
        lockbox.write_forecast(tmp_path, forecast(generated=at))


def test_forecast_rejects_backfill_and_result_fields(tmp_path):
    setup_epoch(tmp_path)
    with pytest.raises(lockbox.ValidationError, match="Backfill"):
        lockbox.write_forecast(tmp_path, forecast(generated="2026-07-20T12:01:00Z"))
    with pytest.raises(lockbox.ValidationError, match="unbekannte"):
        lockbox.write_forecast(tmp_path, forecast(extra={"outcome": "team1_win"}))


def test_trusted_receipt_clock_blocks_post_cutoff_payload_backfill(tmp_path, monkeypatch):
    setup_epoch(tmp_path)
    monkeypatch.setattr(lockbox, "_now_utc", lambda: lockbox._utc(
        "2026-08-15T14:30:00Z", "test_now"))
    with pytest.raises(lockbox.ValidationError, match="Receipt-Zeit"):
        lockbox.write_forecast(tmp_path, forecast())
    with pytest.raises(lockbox.ValidationError, match="Receipt-Zeit"):
        lockbox.write_closing(tmp_path, closing())


def test_forecast_rejects_unknown_non_result_field_too(tmp_path):
    setup_epoch(tmp_path)
    with pytest.raises(lockbox.ValidationError, match="unbekannte"):
        lockbox.write_forecast(tmp_path, forecast(extra={"harmless_but_untyped": 1}))


def test_forecast_requires_all_typed_probabilities_and_manifest_hashes(tmp_path):
    setup_epoch(tmp_path)
    bad = forecast()
    bad["base_model_probs"] = {"team1_win": 0.8, "draw": 0.3, "team2_win": 0.1}
    with pytest.raises(lockbox.ValidationError, match="normiert"):
        lockbox.write_forecast(tmp_path, bad)
    bad = forecast()
    bad["code_sha256"] = HASH_D
    with pytest.raises(lockbox.ValidationError, match="manifestgebunden"):
        lockbox.write_forecast(tmp_path, bad)


def test_candidate_raw_alpha0_must_be_recomputable(tmp_path):
    setup_epoch(tmp_path)
    bad = forecast()
    bad["alpha0_probs"] = {"team1_win": 0.5, "draw": 0.3, "team2_win": 0.2}
    with pytest.raises(lockbox.ValidationError, match="inkonsistent"):
        lockbox.write_forecast(tmp_path, bad)


def test_closing_requires_exact_whitelist_method_status_and_staleness(tmp_path):
    setup_epoch(tmp_path)
    bad = closing()
    bad["books"] = ["pinnacle"]
    with pytest.raises(lockbox.ValidationError, match="Whitelist"):
        lockbox.write_closing(tmp_path, bad)
    with pytest.raises(lockbox.ValidationError, match="Staleness"):
        lockbox.write_closing(tmp_path, closing(captured="2026-08-15T13:50:00Z"))


def test_primary_capture_binding_mismatch_fails_evaluation_closed(tmp_path):
    setup_epoch(tmp_path)
    lockbox.write_forecast(tmp_path, forecast(capture_id="capture-a"))
    lockbox.write_closing(tmp_path, closing(capture_id="capture-b"))
    lockbox.write_result(tmp_path, result())
    evaluated = lockbox.evaluate(tmp_path, evaluation_mode="test")
    assert evaluated["status"] == "blocked" and evaluated["integrity_ok"] is False
    assert evaluated["gates"]["release"] is False


def test_result_must_be_final_post_kickoff_and_post_inputs(tmp_path):
    setup_epoch(tmp_path)
    lockbox.write_forecast(tmp_path, forecast())
    lockbox.write_closing(tmp_path, closing())
    with pytest.raises(lockbox.ValidationError, match="actual kickoff"):
        lockbox.write_result(tmp_path, result(captured="2026-08-15T13:59:59Z"))
    with pytest.raises(lockbox.ValidationError, match="actual kickoff"):
        lockbox.write_result(tmp_path, result(finished=KICKOFF))


def test_result_requires_manifest_source_and_minimum_duration(tmp_path):
    setup_epoch(tmp_path)
    lockbox.write_forecast(tmp_path, forecast())
    lockbox.write_closing(tmp_path, closing())
    wrong = result()
    wrong["source"] = "other"
    with pytest.raises(lockbox.ValidationError, match="Resultatquelle"):
        lockbox.write_result(tmp_path, wrong)
    with pytest.raises(lockbox.ValidationError, match="Mindestspieldauer"):
        lockbox.write_result(tmp_path, result(finished="2026-08-15T15:29:59Z"))


def test_future_result_payload_is_rejected_by_trusted_receipt_clock(tmp_path):
    setup_epoch(tmp_path)
    lockbox.write_forecast(tmp_path, forecast())
    lockbox.write_closing(tmp_path, closing())
    future = result(captured="2026-08-15T18:00:00Z", finished="2026-08-15T17:30:00Z")
    TEST_CLOCK["now"] = "2026-08-15T16:01:00Z"
    with pytest.raises(lockbox.ValidationError, match="Result-Receipt"):
        lockbox.write_result(tmp_path, future)


def test_official_close_is_separate_and_never_primary_input(tmp_path):
    setup_epoch(tmp_path)
    out = lockbox.write_official_closing(tmp_path, {"candidate_version": VERSION,
        "match_id": MATCH1, "official_closing_id": "official-1",
        "captured_at_utc": "2026-08-15T13:59:50Z", "source": "official_odds",
        "status": "official_final",
        "official_closing_probs": {"team1_win": 0.2, "draw": 0.3, "team2_win": 0.5},
        "mode": "shadow", "auto_apply": False, "prediction_allowed": False,
        "value_allowed": False, "stake_allowed": False})
    assert "official_closings" in out["path"]
    evaluated = lockbox.evaluate(tmp_path, evaluation_mode="test")
    assert evaluated["coverage"] == 0 and evaluated["n_paired"] == 0


def test_tamper_fails_closed(tmp_path):
    setup_epoch(tmp_path)
    written = lockbox.write_forecast(tmp_path, forecast())
    artifact = json.loads(Path(written["path"]).read_text(encoding="utf-8"))
    artifact["payload"]["quality_status"] = "tampered"
    Path(written["path"]).write_text(json.dumps(artifact), encoding="utf-8")
    evaluated = lockbox.evaluate(tmp_path, evaluation_mode="test")
    assert evaluated["status"] == "blocked" and evaluated["integrity_ok"] is False


def test_replayed_envelope_under_other_match_path_fails_closed(tmp_path):
    setup_epoch(tmp_path, [fixture(MATCH1), fixture(MATCH2)])
    written = lockbox.write_forecast(tmp_path, forecast(MATCH1))
    replay_path = tmp_path / VERSION / "forecasts" / MATCH2 / f"{MATCH1}.json"
    replay_path.parent.mkdir(parents=True)
    shutil.copyfile(written["path"], replay_path)
    evaluated = lockbox.evaluate(tmp_path, evaluation_mode="test")
    assert evaluated["status"] == "blocked" and evaluated["integrity_ok"] is False


def test_same_id_retry_idempotent_changed_content_conflicts(tmp_path):
    setup_epoch(tmp_path)
    assert lockbox.write_forecast(tmp_path, forecast())["status"] == "created"
    assert lockbox.write_forecast(tmp_path, forecast())["status"] == "idempotent"
    changed = forecast(generated="2026-08-15T13:54:56Z")
    with pytest.raises(lockbox.ArtifactConflictError):
        lockbox.write_forecast(tmp_path, changed)


def test_concurrent_identical_writes_publish_one_artifact(tmp_path):
    setup_epoch(tmp_path)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: lockbox.write_forecast(tmp_path, forecast()), range(8)))
    assert sum(x["status"] == "created" for x in results) == 1
    assert sum(x["status"] == "idempotent" for x in results) == 7


def test_link_failure_fails_closed_without_partial_target(tmp_path, monkeypatch):
    setup_epoch(tmp_path)
    monkeypatch.setattr(lockbox.os, "link", lambda *_: (_ for _ in ()).throw(
        PermissionError("hardlinks disabled")))
    with pytest.raises(lockbox.LockboxError, match="create-only"):
        lockbox.write_forecast(tmp_path, forecast())
    assert not list((tmp_path / VERSION / "forecasts").rglob("*.json"))


def test_versions_never_mix(tmp_path):
    for version, match_id in ((VERSION, MATCH1), ("closing_residual_v2", MATCH2)):
        setup_epoch(tmp_path, [fixture(match_id)], version)
        write_complete_match(tmp_path, match_id, version)
    v1 = lockbox.evaluate(tmp_path, VERSION, evaluation_mode="test")
    v2 = lockbox.evaluate(tmp_path, "closing_residual_v2", evaluation_mode="test")
    assert [x["match_id"] for x in v1["rows"]] == [MATCH1]
    assert [x["match_id"] for x in v2["rows"]] == [MATCH2]


def test_evaluation_reports_per_league_guardrails_and_protocol_bootstrap(tmp_path):
    setup_epoch(tmp_path)
    write_complete_match(tmp_path)
    evaluated = lockbox.evaluate(tmp_path, evaluation_mode="test")
    assert set(evaluated["per_league"]) == set(lockbox.REQUIRED_LEAGUES)
    assert set(evaluated["guardrails"]) == {"draw", "promoted", "first_six"}
    assert evaluated["bootstrap"]["cluster"] == protocol()["inference"]["cluster"]
    assert evaluated["bootstrap"]["test_mode"] is True
    assert evaluated["gates"]["release"] is False
    assert evaluated["release_status"] == "blocked"
    assert evaluated["status"] == "insufficient_data"
    assert evaluated["statistically_definitive"] is False


def test_one_sided_bootstrap_quantile_indices_are_deterministic():
    values = list(range(1, 21))
    assert lockbox._nearest_rank(values, 0.05) == 1
    assert lockbox._nearest_rank(values, 0.95) == 19


def test_production_checkpoint_writes_create_only_receipt_and_blocks_repeek(tmp_path):
    setup_epoch(tmp_path, [fixture(MATCH1), fixture(MATCH2)])
    write_complete_match(tmp_path, MATCH1)
    first = lockbox.evaluate(tmp_path, checkpoint_id="cp-1")
    second = lockbox.evaluate(tmp_path, checkpoint_id="cp-1")
    assert first["evaluation_receipt"]["status"] == "created"
    assert second["evaluation_receipt"]["status"] == "idempotent"
    assert first["statistically_definitive"] is False
    write_complete_match(tmp_path, MATCH2)
    changed = lockbox.evaluate(tmp_path, checkpoint_id="cp-1")
    assert changed["status"] == "blocked"
    assert "Receipt-Konflikt" in changed["note"]


def test_identical_checkpoint_replay_preserves_first_receipt_time_after_window(tmp_path):
    setup_epoch(tmp_path)
    write_complete_match(tmp_path)
    first = lockbox.evaluate(tmp_path, checkpoint_id="cp-1")
    receipt_path = tmp_path / VERSION / "evaluations" / "cp-1.json"
    first_payload, _ = lockbox._read(receipt_path, "evaluation_receipt")
    TEST_CLOCK["now"] = "2026-09-01T00:00:00Z"
    replay = lockbox.evaluate(tmp_path, checkpoint_id="cp-1")
    replay_payload, _ = lockbox._read(receipt_path, "evaluation_receipt")
    assert replay["evaluation_receipt"]["status"] == "idempotent"
    assert replay_payload["evaluated_at_utc"] == first_payload["evaluated_at_utc"]
    assert replay_payload["artifact_cutoff_at_utc"] == first_payload["evaluated_at_utc"]
    assert replay_payload["result_system_receipts"][MATCH1].endswith("Z")


def test_checkpoint_reservation_anchors_evidence_before_evaluation(tmp_path):
    setup_epoch(tmp_path)
    write_complete_match(tmp_path)
    evaluated = lockbox.evaluate(tmp_path, checkpoint_id="cp-1")
    anchor_path = tmp_path / VERSION / "checkpoint_reservations" / "cp-1.json"
    anchor, anchor_digest = lockbox._read(anchor_path, "checkpoint_reservation")
    receipt, _ = lockbox._read(tmp_path / VERSION / "evaluations" / "cp-1.json",
                               "evaluation_receipt")
    assert evaluated["evaluation_receipt"]["status"] == "created"
    assert receipt["checkpoint_reservation_sha256"] == anchor_digest
    assert receipt["artifact_digests"] == anchor["artifact_digests"]
    assert receipt["result_system_receipts"] == anchor["result_system_receipts"]


def test_result_receipt_after_subsecond_artifact_cutoff_is_blocked(tmp_path):
    setup_epoch(tmp_path)
    lockbox.write_forecast(tmp_path, forecast())
    lockbox.write_closing(tmp_path, closing())
    TEST_CLOCK["now"] = "2026-08-15T16:01:00.100000Z"
    reserved = lockbox.reserve_checkpoint(tmp_path, checkpoint_id="cp-1")
    assert reserved["reserved_at_utc"] == "2026-08-15T16:01:00.100000Z"
    result_record = result()
    TEST_CLOCK["now"] = "2026-08-15T16:01:00.900000Z"
    lockbox.write_result(tmp_path, result_record)
    stored_result = lockbox._one_record(tmp_path, VERSION, "results", MATCH1)
    assert stored_result["written_at_utc"] == "2026-08-15T16:01:00.900000Z"
    evaluated = lockbox.evaluate(tmp_path, checkpoint_id="cp-1")
    assert evaluated["status"] == "blocked"
    assert "nach Checkpoint/Evaluation" in evaluated["note"]


def test_production_requires_manifested_checkpoint(tmp_path):
    setup_epoch(tmp_path)
    assert lockbox.evaluate(tmp_path)["status"] == "blocked"
    assert lockbox.evaluate(tmp_path, checkpoint_id="unknown")["status"] == "blocked"


def test_closed_deleted_checkpoint_cannot_be_recreated_or_advanced(tmp_path):
    setup_epoch(tmp_path)
    write_complete_match(tmp_path)
    first = lockbox.evaluate(tmp_path, checkpoint_id="cp-1")
    receipt_path = tmp_path / VERSION / "evaluations" / "cp-1.json"
    assert first["evaluation_receipt"]["status"] == "created"
    receipt_path.unlink()
    TEST_CLOCK["now"] = "2026-08-16T16:01:00Z"
    assert lockbox.evaluate(tmp_path, checkpoint_id="cp-1")["status"] == "blocked"
    advanced = lockbox.evaluate(tmp_path, checkpoint_id="cp-2")
    assert advanced["status"] == "blocked"


def test_cohort_validates_complete_chain_to_selected_receipt(tmp_path):
    _formal_epoch(tmp_path, MATCH1, "epoch-chain")
    TEST_CLOCK["now"] = "2026-08-16T16:01:00Z"
    assert lockbox.evaluate(tmp_path, checkpoint_id="cp-2")["evaluation_receipt"][
        "status"] == "created"
    (tmp_path / VERSION / "evaluations" / "cp-1.json").unlink()
    cohort_root = tmp_path / "cohort-store"
    with pytest.raises(lockbox.IntegrityError, match="Artefakt unlesbar"):
        lockbox.reserve_cohort(cohort_root, "cohort-chain", "hyp-chain", [{
            "root": tmp_path, "version": VERSION, "checkpoint_id": "cp-2"}])


def _formal_epoch(root, match_id, epoch_id, *, config_extra=None):
    p = protocol()
    p["epoch_id"] = epoch_id
    if config_extra:
        p["config"]["extra"] = config_extra
    lockbox.create_manifest(root, p)
    make_population(root, [fixture(match_id)])
    write_complete_match(root, match_id)
    TEST_CLOCK["now"] = "2026-08-15T16:01:00Z"
    assert lockbox.evaluate(root, checkpoint_id="cp-1")["evaluation_receipt"]["status"] == "created"


def test_cohort_combines_disjoint_formal_epochs_but_test_mode_never_definitive(tmp_path):
    root1, root2 = tmp_path / "e1", tmp_path / "e2"
    _formal_epoch(root1, MATCH1, "epoch-1")
    _formal_epoch(root2, MATCH2, "epoch-2")
    cohort = lockbox.evaluate_cohort([
        {"root": root1, "version": VERSION, "checkpoint_id": "cp-1"},
        {"root": root2, "version": VERSION, "checkpoint_id": "cp-1"}],
        evaluation_mode="test")
    assert cohort["n_epochs"] == 2 and cohort["n_paired"] == 2
    assert cohort["statistically_definitive"] is False
    assert cohort["status"] == "insufficient_data"
    assert len(cohort["cohort_inputs_sha256"]) == 64


def test_cohort_blocks_config_mismatch_duplicate_match_and_missing_receipt(tmp_path):
    root1, root2 = tmp_path / "e1", tmp_path / "e2"
    _formal_epoch(root1, MATCH1, "epoch-1")
    _formal_epoch(root2, MATCH2, "epoch-2", config_extra="different")
    members = [{"root": root1, "version": VERSION, "checkpoint_id": "cp-1"},
               {"root": root2, "version": VERSION, "checkpoint_id": "cp-1"}]
    assert lockbox.evaluate_cohort(members, evaluation_mode="test")["status"] == "blocked"
    missing_root = tmp_path / "missing"
    setup_epoch(missing_root)
    assert lockbox.evaluate_cohort([
        {"root": missing_root, "version": VERSION, "checkpoint_id": "cp-1"}],
        evaluation_mode="test")["status"] == "blocked"
    duplicate_root = tmp_path / "duplicate"
    _formal_epoch(duplicate_root, MATCH1, "epoch-3")
    duplicate_members = [members[0],
        {"root": duplicate_root, "version": VERSION, "checkpoint_id": "cp-1"}]
    assert lockbox.evaluate_cohort(duplicate_members, evaluation_mode="test")["status"] == "blocked"


def test_production_cohort_requires_exact_create_only_hypothesis_reservation(tmp_path):
    root1, root2 = tmp_path / "e1", tmp_path / "e2"
    _formal_epoch(root1, MATCH1, "epoch-1")
    _formal_epoch(root2, MATCH2, "epoch-2")
    members = [{"root": root1, "version": VERSION, "checkpoint_id": "cp-1"},
               {"root": root2, "version": VERSION, "checkpoint_id": "cp-1"}]
    cohort_root = tmp_path / "cohort-store"
    reserved = lockbox.reserve_cohort(cohort_root, "cohort-1", "hypothesis-1", members)
    assert reserved["write_status"] == "created"
    assert lockbox.evaluate_cohort(members, cohort_root=cohort_root,
                                   cohort_id="cohort-1",
                                   hypothesis_id="hypothesis-1")["status"] == "blocked"
    evaluated = lockbox.evaluate_cohort(None, cohort_root=cohort_root,
                                        cohort_id="cohort-1",
                                        hypothesis_id="hypothesis-1")
    assert evaluated["n_epochs"] == 2
    assert evaluated["cohort_receipt"]["status"] == "created"
    with pytest.raises(lockbox.ArtifactConflictError):
        lockbox.reserve_cohort(cohort_root, "cohort-alternative", "hypothesis-1",
                               members[:1])


def test_production_evaluation_has_no_runtime_gate_or_bootstrap_override(tmp_path):
    setup_epoch(tmp_path)
    with pytest.raises(TypeError):
        lockbox.evaluate(tmp_path, gate_config={"coverage": 0})
    with pytest.raises(TypeError):
        lockbox.evaluate(tmp_path, bootstrap_iterations=1)

import json
from pathlib import Path

import pytest

from src.model import club_lockbox as lockbox


VERSION = "closing_residual_v1"
KICKOFF = "2026-08-15T14:00:00Z"


def manifest(root: Path, version: str = VERSION):
    return lockbox.create_manifest(
        root,
        candidate_version=version,
        created_at_utc="2026-07-20T12:00:00Z",
        candidate_config={
            "model": "closing_residual_blend",
            "grid": {"alpha": [0.0, 0.025, 0.05, 0.075, 0.1]},
            "frozen_parameters": {"alpha": 0.1},
        },
        training_definition={
            "source": "football-data.co.uk",
            "seasons": [2021, 2022, 2023, 2024, 2025],
            "selection": "prior-seasons-only",
        },
        benchmark_definition={
            "raw_closing": {"devig": "source-provided"},
            "alpha0_calibrator": {"temperature": 0.95, "draw_multiplier": 1.05},
        },
    )


def forecast(match_id="fx-test-1", version=VERSION, at="2026-08-15T13:54:59Z",
             probs=None, competition="premier_league"):
    return {
        "candidate_version": version, "match_id": match_id,
        "competition": competition, "kickoff_utc": KICKOFF,
        "generated_at_utc": at,
        "candidate_probs": probs or {
            "team1_win": 0.7, "draw": 0.2, "team2_win": 0.1},
    }


def closing(match_id="fx-test-1", version=VERSION, at="2026-08-15T13:54:59Z",
            probs=None):
    return {
        "candidate_version": version, "match_id": match_id,
        "kickoff_utc": KICKOFF, "captured_at_utc": at,
        "raw_closing_probs": probs or {
            "team1_win": 0.4, "draw": 0.3, "team2_win": 0.3},
    }


def result(match_id="fx-test-1", version=VERSION, status="FINAL",
           outcome="team1_win"):
    return {
        "candidate_version": version, "match_id": match_id,
        "captured_at_utc": "2026-08-15T16:00:00Z",
        "status": status, "outcome": outcome,
    }


def permissive_gates():
    return {"minimum_coverage": 0.0, "minimum_paired_n": 1,
            "minimum_days": 1, "minimum_leagues": 1,
            "confidence_level": 0.8}


def test_manifest_is_versioned_fingerprinted_create_only_and_idempotent(tmp_path):
    first = manifest(tmp_path)
    second = manifest(tmp_path)

    assert first["write_status"] == "created"
    assert second["write_status"] == "idempotent"
    assert len(first["manifest_sha256"]) == 64
    assert len(first["fingerprint_sha256"]) == 64
    assert set(first["components"]) == {"config", "training", "benchmarks", "cutoff"}
    assert all(len(block["sha256"]) == 64 for block in first["components"].values())
    assert first["release_status"] == "blocked"
    assert first["auto_apply"] is False


def test_manifest_same_version_with_changed_config_conflicts(tmp_path):
    manifest(tmp_path)
    with pytest.raises(lockbox.ArtifactConflictError):
        lockbox.create_manifest(
            tmp_path, candidate_version=VERSION,
            created_at_utc="2026-07-20T12:00:00Z",
            candidate_config={"model": "changed"},
            training_definition={"source": "same"},
            benchmark_definition={"raw_closing": {}, "alpha0_calibrator": {}},
        )


@pytest.mark.parametrize("bad_time", [
    "2026-08-15T13:00:00", "2026-08-15T15:00:00+01:00",
])
def test_forecast_requires_explicit_utc(tmp_path, bad_time):
    manifest(tmp_path)
    with pytest.raises(lockbox.ValidationError, match="UTC"):
        lockbox.write_forecast(tmp_path, forecast(at=bad_time))


@pytest.mark.parametrize("at", [
    "2026-08-15T13:55:00Z",  # exact T-5 boundary
    "2026-08-15T13:55:01Z",  # after fixed cutoff
    "2026-08-15T14:00:01Z",  # after kickoff
])
def test_forecast_and_closing_reject_exact_or_post_cutoff(tmp_path, at):
    manifest(tmp_path)
    with pytest.raises(lockbox.ValidationError, match="strikt vor"):
        lockbox.write_forecast(tmp_path, forecast(at=at))
    with pytest.raises(lockbox.ValidationError, match="strikt vor"):
        lockbox.write_closing(tmp_path, closing(at=at))


def test_artifact_retry_is_idempotent_but_changed_same_id_conflicts(tmp_path):
    manifest(tmp_path)
    first = lockbox.write_forecast(tmp_path, forecast())
    second = lockbox.write_forecast(tmp_path, forecast())

    assert first["status"] == "created"
    assert second["status"] == "idempotent"
    changed = forecast(probs={"team1_win": 0.6, "draw": 0.2, "team2_win": 0.2})
    with pytest.raises(lockbox.ArtifactConflictError):
        lockbox.write_forecast(tmp_path, changed)


def test_probabilities_must_be_normalized_and_all_guards_stay_false(tmp_path):
    manifest(tmp_path)
    with pytest.raises(lockbox.ValidationError, match="normiert"):
        lockbox.write_forecast(tmp_path, forecast(probs={
            "team1_win": 0.7, "draw": 0.3, "team2_win": 0.1}))
    unsafe = forecast()
    unsafe["value_allowed"] = True
    with pytest.raises(lockbox.ValidationError, match="value_allowed"):
        lockbox.write_forecast(tmp_path, unsafe)


def test_tamper_fails_evaluation_closed(tmp_path):
    manifest(tmp_path)
    written = lockbox.write_forecast(tmp_path, forecast())
    path = Path(written["path"])
    artifact = json.loads(path.read_text(encoding="utf-8"))
    artifact["payload"]["candidate_probs"]["team1_win"] = 0.9
    path.write_text(json.dumps(artifact), encoding="utf-8")

    evaluated = lockbox.evaluate(tmp_path, bootstrap_iterations=20)

    assert evaluated["status"] == "blocked"
    assert evaluated["integrity_ok"] is False
    assert evaluated["gates"]["release"] is False
    assert evaluated["release_status"] == "blocked"


def test_missing_closing_remains_in_forecast_coverage_denominator(tmp_path):
    manifest(tmp_path)
    lockbox.write_forecast(tmp_path, forecast("fx-test-1"))
    lockbox.write_forecast(tmp_path, forecast("fx-test-2"))
    lockbox.write_closing(tmp_path, closing("fx-test-1"))
    lockbox.write_result(tmp_path, result("fx-test-1"))
    lockbox.write_result(tmp_path, result("fx-test-2"))

    evaluated = lockbox.evaluate(tmp_path, gate_config=permissive_gates(),
                                 bootstrap_iterations=50)

    assert evaluated["n_forecasts"] == 2
    assert evaluated["n_paired"] == 1
    assert evaluated["coverage"] == 0.5
    assert evaluated["unpaired"] == [{"match_id": "fx-test-2", "reason": "missing_closing"}]


def test_only_final_results_are_scored(tmp_path):
    manifest(tmp_path)
    lockbox.write_forecast(tmp_path, forecast())
    lockbox.write_closing(tmp_path, closing())
    lockbox.write_result(tmp_path, result(status="SCHEDULED", outcome=None))

    evaluated = lockbox.evaluate(tmp_path, bootstrap_iterations=20)

    assert evaluated["n_forecasts"] == 1
    assert evaluated["n_paired"] == 0
    assert evaluated["unpaired"][0]["reason"] == "missing_final_result"


def test_candidate_versions_are_evaluated_separately(tmp_path):
    manifest(tmp_path, VERSION)
    manifest(tmp_path, "closing_residual_v2")
    for version, match_id in ((VERSION, "fx-v1"), ("closing_residual_v2", "fx-v2")):
        lockbox.write_forecast(tmp_path, forecast(match_id, version))
        lockbox.write_closing(tmp_path, closing(match_id, version))
        lockbox.write_result(tmp_path, result(match_id, version))

    v1 = lockbox.evaluate(tmp_path, VERSION, gate_config=permissive_gates(),
                          bootstrap_iterations=20)
    v2 = lockbox.evaluate(tmp_path, "closing_residual_v2", gate_config=permissive_gates(),
                          bootstrap_iterations=20)

    assert v1["n_forecasts"] == v2["n_forecasts"] == 1
    assert v1["rows"][0]["match_id"] == "fx-v1"
    assert v2["rows"][0]["match_id"] == "fx-v2"


def test_evaluation_has_unrounded_paired_metrics_for_both_benchmarks(tmp_path):
    manifest(tmp_path)
    lockbox.write_forecast(tmp_path, forecast())
    lockbox.write_closing(tmp_path, closing())
    lockbox.write_result(tmp_path, result())

    evaluated = lockbox.evaluate(tmp_path, gate_config=permissive_gates(),
                                 bootstrap_iterations=30)
    row = evaluated["rows"][0]

    assert row["candidate"]["rps"] == pytest.approx(0.05)
    assert row["candidate"]["log_loss"] == pytest.approx(-__import__("math").log(0.7))
    assert set(evaluated["comparisons"]) == {"raw_closing", "alpha0_calibrator"}
    assert "delta_rps_vs_raw_closing" in row
    assert "delta_log_loss_vs_alpha0_calibrator" in row


def test_release_gate_remains_blocked_even_when_statistical_thresholds_are_permissive(tmp_path):
    manifest(tmp_path)
    # Perfect candidate versus deliberately weak market; all statistical checks can pass.
    for i in range(3):
        match_id = f"fx-win-{i}"
        lockbox.write_forecast(tmp_path, forecast(match_id, probs={
            "team1_win": 1.0, "draw": 0.0, "team2_win": 0.0}))
        lockbox.write_closing(tmp_path, closing(match_id, probs={
            "team1_win": 0.2, "draw": 0.3, "team2_win": 0.5}))
        lockbox.write_result(tmp_path, result(match_id))

    evaluated = lockbox.evaluate(tmp_path, gate_config=permissive_gates(),
                                 bootstrap_iterations=100)

    assert evaluated["statistical_gates_pass"] is True
    assert evaluated["gates"]["release"] is False
    assert evaluated["release_status"] == "blocked"
    assert evaluated["auto_apply"] is False
    assert evaluated["prediction_allowed"] is False
    assert evaluated["value_allowed"] is False
    assert evaluated["stake_allowed"] is False


def test_default_bootstrap_budget_is_production_sized():
    assert lockbox.DEFAULT_BOOTSTRAP_ITERATIONS >= 10_000

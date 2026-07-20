"""Prospective, append-only shadow lockbox for club-football forecasts.

The lockbox is intentionally independent from live sources and the production
pipeline.  Its protocol is frozen in a create-only manifest and population
ledger; every operational artifact is schema checked, hash bound to that
manifest, and permanently non-releasing.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import os
import random
import re
import tempfile
from pathlib import Path
from typing import Iterable

from src.domain import canonical_match_id
from src.model.calibration import log_loss, rps


SCHEMA_VERSION = "club-lockbox-v2"
DEFAULT_CANDIDATE_VERSION = "closing_residual_v1"
OUTCOMES = ("team1_win", "draw", "team2_win")
REQUIRED_LEAGUES = ("premier_league", "la_liga", "bundesliga", "serie_a", "ligue_1")
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class LockboxError(RuntimeError):
    pass


class ArtifactConflictError(LockboxError):
    pass


class IntegrityError(LockboxError):
    pass


class ValidationError(LockboxError, ValueError):
    pass


def _canonical_bytes(value: dict) -> bytes:
    try:
        encoded = json.dumps(value, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"Nicht kanonisch serialisierbar: {exc}") from exc
    return (encoded + "\n").encode("utf-8")


def _sha(value: dict) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _safe(value: object, field: str) -> str:
    clean = str(value or "").strip()
    if not _SAFE_ID.fullmatch(clean):
        raise ValidationError(f"{field} muss eine sichere stabile ID sein")
    return clean


def _hash(value: object, field: str) -> str:
    clean = str(value or "").lower()
    if not _SHA256.fullmatch(clean):
        raise ValidationError(f"{field} muss ein SHA256 sein")
    return clean


def _utc(value: object, field: str) -> dt.datetime:
    raw = str(value or "")
    try:
        parsed = dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValidationError(f"{field} ist kein gueltiger ISO-Zeitpunkt") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != dt.timedelta(0):
        raise ValidationError(f"{field} muss explizit UTC sein")
    return parsed.astimezone(dt.timezone.utc)


def _now_utc() -> dt.datetime:
    """Trusted process receipt clock; tests may monkeypatch this private seam."""
    return dt.datetime.now(dt.timezone.utc)


def _probs(value: object, field: str) -> dict[str, float]:
    if not isinstance(value, dict) or set(value) != set(OUTCOMES):
        raise ValidationError(f"{field} braucht exakt die drei 1X2-Ausgaenge")
    try:
        out = {key: float(value[key]) for key in OUTCOMES}
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field} enthaelt ungueltige Zahlen") from exc
    if any(not math.isfinite(p) or p < 0 or p > 1 for p in out.values()):
        raise ValidationError(f"{field} muss endliche Werte in [0,1] enthalten")
    if not math.isclose(sum(out.values()), 1.0, rel_tol=0, abs_tol=1e-9):
        raise ValidationError(f"{field} muss auf 1 normiert sein")
    return out


def _envelope(kind: str, payload: dict) -> dict:
    signed = {"schema_version": SCHEMA_VERSION, "kind": kind, "payload": payload}
    return {**signed, "integrity": {"algorithm": "sha256", "digest": _sha(signed)}}


def _verify(value: dict, kind: str) -> dict:
    if not isinstance(value, dict) or value.get("schema_version") != SCHEMA_VERSION:
        raise IntegrityError("Unbekanntes oder ungueltiges Lockbox-Schema")
    if value.get("kind") != kind:
        raise IntegrityError("Falscher Artefakttyp")
    signed = {key: value.get(key) for key in ("schema_version", "kind", "payload")}
    integrity = value.get("integrity") or {}
    if integrity.get("algorithm") != "sha256" or integrity.get("digest") != _sha(signed):
        raise IntegrityError("SHA256-Integritaetspruefung fehlgeschlagen")
    if not isinstance(value.get("payload"), dict):
        raise IntegrityError("Payload fehlt")
    return value["payload"]


def _atomic_create(path: Path, value: dict) -> str:
    """Publish a fully fsynced file atomically without overwrite semantics."""
    path.parent.mkdir(parents=True, exist_ok=True)
    content = _canonical_bytes(value)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(tmp, path)
        except FileExistsError:
            try:
                existing = path.read_bytes()
            except OSError as exc:
                raise ArtifactConflictError(f"Bestehendes Artefakt unlesbar: {path}") from exc
            if existing != content:
                raise ArtifactConflictError(f"Create-only-Konflikt: {path}")
            return "idempotent"
        except OSError as exc:
            # No rename fallback: replacing a concurrent target would violate create-only.
            raise LockboxError(f"Atomare create-only Publikation fehlgeschlagen: {exc}") from exc
        return "created"
    finally:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass


def _read(path: Path, kind: str) -> tuple[dict, str]:
    try:
        envelope = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise IntegrityError(f"Artefakt unlesbar: {path}") from exc
    payload = _verify(envelope, kind)
    return payload, envelope["integrity"]["digest"]


def _flags(record: dict) -> None:
    if record.get("mode", "shadow") != "shadow":
        raise ValidationError("mode muss shadow sein")
    for name in ("auto_apply", "prediction_allowed", "value_allowed", "stake_allowed"):
        if record.get(name, False) is not False:
            raise ValidationError(f"{name} muss false bleiben")


def _blocked_fields() -> dict:
    return {"mode": "shadow", "release_status": "blocked", "auto_apply": False,
            "prediction_allowed": False, "value_allowed": False, "stake_allowed": False}


def _validate_manifest_protocol(protocol: dict) -> None:
    required = {"lockbox_id", "epoch_id", "candidate_name", "candidate_version",
                "frozen_at_utc", "git_commit", "code_sha256", "config", "model",
                "training", "population", "market", "capture", "benchmarks", "results",
                "inference", "gates", "guardrails", "evaluation_schedule"}
    if set(protocol) != required:
        raise ValidationError(f"Manifestfelder muessen exakt {sorted(required)} sein")
    _safe(protocol["lockbox_id"], "lockbox_id")
    _safe(protocol["epoch_id"], "epoch_id")
    _safe(protocol["candidate_version"], "candidate_version")
    _utc(protocol["frozen_at_utc"], "frozen_at_utc")
    if not str(protocol["git_commit"] or "").strip():
        raise ValidationError("git_commit fehlt")
    _hash(protocol["code_sha256"], "code_sha256")
    for component in ("config", "model", "training"):
        block = protocol[component]
        if not isinstance(block, dict) or not block:
            raise ValidationError(f"{component} fehlt")
        _hash(block.get("sha256"), f"{component}.sha256")
    training = protocol["training"]
    max_information = _utc(training.get("max_information_at_utc"),
                           "training.max_information_at_utc")
    if max_information >= _utc(protocol["frozen_at_utc"], "frozen_at_utc"):
        raise ValidationError("Training-Maximalinformation muss vor dem Freeze liegen")
    files = training.get("files")
    if (not isinstance(files, list) or not files
            or any(not isinstance(row, dict) or not str(row.get("path") or "").strip()
                   or not _SHA256.fullmatch(str(row.get("sha256", ""))) for row in files)):
        raise ValidationError("training.files braucht Datei-SHA256")
    population = protocol["population"]
    if tuple(population.get("required_leagues") or ()) != REQUIRED_LEAGUES:
        raise ValidationError("Population muss exakt die festen Top-5-Ligen enthalten")
    if not population.get("season_epoch") or not population.get("inclusion_rules"):
        raise ValidationError("Population/Einschlussregeln fehlen")
    market = protocol["market"]
    if (not market.get("book_whitelist") or market.get("devig_method") != "proportional"
            or market.get("consensus_method") != "mean"
            or not _SAFE_ID.fullmatch(str(market.get("official_closing_source", "")))
            or market.get("missing_policy") != "unpaired_counts_against_coverage"):
        raise ValidationError("Markt-Whitelist/De-vig/Konsens/Missing-Regel unvollstaendig")
    config_params = protocol["config"].get("frozen_parameters") or {}
    if set(config_params) != set(REQUIRED_LEAGUES):
        raise ValidationError("Eingefrorene Kandidatenparameter fehlen fuer Top-5-Ligen")
    alpha0_spec = protocol["benchmarks"].get("alpha0_calibrator") or {}
    alpha0_by_league = alpha0_spec.get("by_competition") or {}
    for league, params in config_params.items():
        if set(params) != {"alpha", "temperature", "draw_multiplier"}:
            raise ValidationError("Kandidatenparameter sind unvollstaendig")
        if not 0 <= float(params["alpha"]) <= 1 or float(params["temperature"]) <= 0 or float(
                params["draw_multiplier"]) <= 0:
            raise ValidationError("Kandidatenparameter liegen ausserhalb des Wertebereichs")
        benchmark_params = alpha0_by_league.get(league, alpha0_spec)
        if (float(params["temperature"]) != float(benchmark_params.get("temperature", 0))
                or float(params["draw_multiplier"]) != float(
                    benchmark_params.get("draw_multiplier", 0))):
            raise ValidationError("Alpha0- und Kandidaten-Rekalibrierung muessen identisch sein")
    capture = protocol["capture"]
    if (capture.get("policy") != "fixed_t_minus_5" or capture.get("minutes_before_kickoff") != 5
            or capture.get("boundary") != "strictly_before"
            or int(capture.get("max_staleness_seconds", -1)) < 0
            or capture.get("binding") != "same_capture_for_candidate_raw_alpha0"):
        raise ValidationError("T-5-Capture-Policy ist nicht protokollkonform")
    benchmarks = protocol["benchmarks"]
    if set(benchmarks) != {"raw_closing", "alpha0_calibrator"}:
        raise ValidationError("Beide Pflichtbenchmarks muessen festgeschrieben sein")
    results = protocol["results"]
    if (set(results) != {"authoritative_source", "min_match_duration_seconds",
                        "finality_rule"}
            or not _SAFE_ID.fullmatch(str(results.get("authoritative_source", "")))
            or int(results.get("min_match_duration_seconds", 0)) < 90 * 60
            or results.get("finality_rule") != "final_after_finished_at"):
        raise ValidationError("Resultatquelle/Finalitaetsregel ist unvollstaendig")
    inference = protocol["inference"]
    if (inference.get("metrics") != ["rps", "log_loss"]
            or int(inference.get("bootstrap_iterations", 0)) < 10_000
            or float(inference.get("confidence_level", 0)) != 0.95
            or inference.get("cluster") != "league_x_season_x_matchday_fallback_league_x_date"
            or not isinstance(inference.get("bootstrap_seed"), int)):
        raise ValidationError("Inferenzplan ist nicht normativ vollstaendig")
    gates = protocol["gates"]
    expected = {"coverage": 0.98, "diagnostic_total": 3000, "diagnostic_per_league": 500,
                "definitive_total": 15000, "definitive_per_league": 1500,
                "league_wins_required": 4}
    if any(gates.get(key) != val for key, val in expected.items()):
        raise ValidationError("Gate-Schwellen weichen vom Protokoll ab")
    guardrails = protocol["guardrails"]
    if (set(guardrails.get("groups") or ()) != {"draw", "promoted", "first_six"}
            or guardrails.get("rps_upper_limit") != 0.002
            or guardrails.get("log_loss_upper_limit") != 0.01
            or int(guardrails.get("minimum_n", 0)) < 1):
        raise ValidationError("Guardrails sind unvollstaendig")
    schedule = protocol["evaluation_schedule"]
    if not isinstance(schedule, list) or not schedule:
        raise ValidationError("Auswertungsplan fehlt")
    checkpoint_ids, checkpoint_times = [], []
    checkpoint_closes = []
    for row in schedule:
        if not isinstance(row, dict) or set(row) != {
                "checkpoint_id", "opens_at_utc", "closes_at_utc"}:
            raise ValidationError("Auswertungsplan-Eintrag ist ungueltig")
        checkpoint_ids.append(_safe(row["checkpoint_id"], "checkpoint_id"))
        opened = _utc(row["opens_at_utc"], "checkpoint.opens_at_utc")
        closed = _utc(row["closes_at_utc"], "checkpoint.closes_at_utc")
        if opened >= closed:
            raise ValidationError("Checkpoint-Fenster ist leer")
        checkpoint_times.append(opened)
        checkpoint_closes.append(closed)
    overlaps = any(checkpoint_times[i] < checkpoint_closes[i - 1]
                   for i in range(1, len(checkpoint_times)))
    invalid_schedule = (
        len(set(checkpoint_ids)) != len(checkpoint_ids)
        or len(set(checkpoint_times)) != len(checkpoint_times)
        or checkpoint_times != sorted(checkpoint_times)
        or checkpoint_times[0] <= _utc(protocol["frozen_at_utc"], "frozen_at_utc")
        or overlaps
    )
    if invalid_schedule:
        raise ValidationError("Checkpoints muessen eindeutig, sortiert und nach Freeze sein")


def create_manifest(root: Path, protocol: dict) -> dict:
    """Freeze the complete normative protocol for one version and epoch."""
    _validate_manifest_protocol(protocol)
    payload = dict(protocol)
    payload["component_fingerprints"] = {
        name: _sha(protocol[name]) for name in
        ("config", "model", "training", "population", "market", "capture",
         "benchmarks", "results", "inference", "gates", "guardrails", "evaluation_schedule")}
    payload["protocol_sha256"] = _sha(payload["component_fingerprints"])
    payload.update(_blocked_fields())
    envelope = _envelope("manifest", payload)
    version = protocol["candidate_version"]
    epoch_reservation = _envelope("epoch_registry", {
        "lockbox_id": protocol["lockbox_id"], "epoch_id": protocol["epoch_id"],
        "candidate_version": version, "population": protocol["population"]})
    _atomic_create(Path(root) / "epoch_registry" /
                   f"{protocol['lockbox_id']}__{protocol['epoch_id']}.json", epoch_reservation)
    status = _atomic_create(Path(root) / version / "manifest.json", envelope)
    return {**payload, "manifest_sha256": envelope["integrity"]["digest"],
            "write_status": status}


def load_manifest(root: Path, version: str = DEFAULT_CANDIDATE_VERSION) -> dict:
    version = _safe(version, "candidate_version")
    payload, digest = _read(Path(root) / version / "manifest.json", "manifest")
    if payload.get("candidate_version") != version:
        raise IntegrityError("Manifest-Version passt nicht zum Pfad")
    protocol = {key: payload[key] for key in (
        "lockbox_id", "epoch_id", "candidate_name", "candidate_version", "frozen_at_utc",
        "git_commit", "code_sha256", "config", "model", "training", "population", "market",
        "capture", "benchmarks", "results", "inference", "gates", "guardrails",
        "evaluation_schedule")}
    _validate_manifest_protocol(protocol)
    expected = {name: _sha(payload[name]) for name in payload["component_fingerprints"]}
    if payload.get("component_fingerprints") != expected or payload.get(
            "protocol_sha256") != _sha(expected):
        raise IntegrityError("Manifest-Komponentenfingerprint ist ungueltig")
    registry, _ = _read(Path(root) / "epoch_registry" /
                        f"{payload['lockbox_id']}__{payload['epoch_id']}.json",
                        "epoch_registry")
    if registry != {"lockbox_id": payload["lockbox_id"], "epoch_id": payload["epoch_id"],
                    "candidate_version": version, "population": payload["population"]}:
        raise IntegrityError("Rootweite Epoch-Reservierung stimmt nicht mit Manifest ueberein")
    return {**payload, "manifest_sha256": digest}


def _record_path(root: Path, version: str, kind: str, match_id: str, record_id: str) -> Path:
    return Path(root) / version / kind / match_id / f"{record_id}.json"


def write_population(root: Path, record: dict) -> dict:
    """Freeze every eligible fixture before any forecast can be recorded."""
    version = _safe(record.get("candidate_version"), "candidate_version")
    manifest = load_manifest(root, version)
    _flags(record)
    frozen = _utc(record.get("frozen_at_utc"), "population.frozen_at_utc")
    if frozen < _utc(manifest["frozen_at_utc"], "manifest.frozen_at_utc"):
        raise ValidationError("Population darf nicht vor dem Manifest eingefroren werden")
    fixtures = record.get("fixtures")
    if not isinstance(fixtures, list) or not fixtures:
        raise ValidationError("Population braucht Fixtures")
    normalized, seen = [], set()
    for fixture in fixtures:
        required = {"match_id", "competition", "season", "matchday", "scheduled_kickoff_utc",
                    "home_club_id", "away_club_id", "eligible"}
        if not isinstance(fixture, dict) or set(fixture) != required:
            raise ValidationError("Population-Fixture hat unbekannte/fehlende Felder")
        match_id = _safe(fixture["match_id"], "match_id")
        if match_id in seen:
            raise ValidationError("Doppelte Match-ID im Population-Ledger")
        seen.add(match_id)
        competition = _safe(fixture["competition"], "competition")
        if competition not in REQUIRED_LEAGUES:
            raise ValidationError("Fixture liegt ausserhalb der festen Population")
        kickoff = _utc(fixture["scheduled_kickoff_utc"], "scheduled_kickoff_utc")
        if frozen >= kickoff:
            raise ValidationError("Population muss prospektiv vor Anpfiff eingefroren sein")
        if not isinstance(fixture["matchday"], int) or fixture["matchday"] < 1:
            raise ValidationError("matchday muss positiv sein")
        if fixture["eligible"] is not True:
            raise ValidationError("Ledger enthaelt nur vorab eligible Fixtures")
        home = _safe(fixture["home_club_id"], "home_club_id")
        away = _safe(fixture["away_club_id"], "away_club_id")
        if home == away:
            raise ValidationError("Heim- und Auswaertsclub muessen verschieden sein")
        if fixture["season"] != manifest["population"]["season_epoch"]:
            raise ValidationError("Fixture-Saison weicht von der Manifest-Epoch ab")
        expected_match_id = canonical_match_id(competition, fixture["season"],
                                               f"md-{fixture['matchday']}", home, away)
        if match_id != expected_match_id:
            raise ValidationError("match_id ist nicht die kanonische Fixture-ID")
        normalized.append(dict(fixture))
    payload = {"candidate_version": version, "lockbox_id": manifest["lockbox_id"],
               "epoch_id": manifest["epoch_id"], "frozen_at_utc": record["frozen_at_utc"],
               "fixtures": sorted(normalized, key=lambda x: x["match_id"]),
               "manifest_sha256": manifest["manifest_sha256"], **_blocked_fields()}
    envelope = _envelope("population", payload)
    path = Path(root) / version / "population.json"
    status = _atomic_create(path, envelope)
    return {**payload, "population_sha256": envelope["integrity"]["digest"],
            "write_status": status}


def load_population(root: Path, version: str) -> dict:
    manifest = load_manifest(root, version)
    payload, digest = _read(Path(root) / version / "population.json", "population")
    if payload.get("candidate_version") != version or payload.get(
            "manifest_sha256") != manifest["manifest_sha256"]:
        raise IntegrityError("Population ist nicht an das Manifest gebunden")
    return {**payload, "population_sha256": digest}


def _fixture(root: Path, version: str, match_id: str) -> tuple[dict, dict, dict]:
    manifest = load_manifest(root, version)
    population = load_population(root, version)
    fixture = next((x for x in population["fixtures"] if x["match_id"] == match_id), None)
    if not fixture:
        raise ValidationError("Match ist nicht im eingefrorenen Population-Ledger")
    return manifest, population, fixture


_FORECAST_FIELDS = {
    "candidate_version", "match_id", "forecast_id", "capture_id", "competition", "season",
    "matchday", "promoted_match", "scheduled_kickoff_utc", "generated_at_utc", "model_version",
    "git_commit", "code_sha256", "config_sha256", "model_sha256", "training_sha256",
    "base_model_probs", "raw_market_probs", "alpha0_probs", "candidate_probs",
    "candidate_parameters", "source_timestamps", "quality_status", "mode", "auto_apply",
    "prediction_allowed", "value_allowed", "stake_allowed"}


def _same_probs(left: dict, right: dict) -> bool:
    return all(math.isclose(left[key], right[key], rel_tol=0, abs_tol=1e-12) for key in OUTCOMES)


def _alpha0(raw: dict, manifest: dict, league: str) -> dict:
    spec = manifest["benchmarks"]["alpha0_calibrator"]
    params = (spec.get("by_competition") or {}).get(league, spec)
    temperature = float(params["temperature"])
    draw_multiplier = float(params["draw_multiplier"])
    adjusted = {key: max(raw[key], 1e-12) ** (1 / temperature) for key in OUTCOMES}
    adjusted["draw"] *= draw_multiplier
    total = sum(adjusted.values())
    return {key: adjusted[key] / total for key in OUTCOMES}


def write_forecast(root: Path, record: dict) -> dict:
    if set(record) != _FORECAST_FIELDS:
        raise ValidationError("Forecast hat unbekannte oder fehlende Felder")
    if any(token in key.lower() for key in record for token in ("outcome", "result", "score", "goal")):
        raise ValidationError("Forecast darf keine Ergebnisfelder enthalten")
    _flags(record)
    version = _safe(record["candidate_version"], "candidate_version")
    match_id = _safe(record["match_id"], "match_id")
    _safe(record["capture_id"], "capture_id")
    manifest, population, fixture = _fixture(root, version, match_id)
    if any(record[key] != fixture[key] for key in
           ("competition", "season", "matchday", "scheduled_kickoff_utc")):
        raise ValidationError("Forecast-Fixture weicht vom Population-Ledger ab")
    if record["competition"] not in REQUIRED_LEAGUES or not isinstance(record["promoted_match"], bool):
        raise ValidationError("Forecast-Liga/promoted_match ungueltig")
    generated = _utc(record["generated_at_utc"], "generated_at_utc")
    kickoff = _utc(record["scheduled_kickoff_utc"], "scheduled_kickoff_utc")
    cutoff = kickoff - dt.timedelta(minutes=5)
    written_at = _now_utc()
    if generated < _utc(manifest["frozen_at_utc"], "frozen_at_utc") or generated < _utc(
            population["frozen_at_utc"], "population.frozen_at_utc"):
        raise ValidationError("Retrospektiver Forecast-Backfill ist verboten")
    if generated >= cutoff:
        raise ValidationError("Forecast muss strikt vor T-5 liegen")
    if (written_at < generated
            or written_at < _utc(manifest["frozen_at_utc"], "frozen_at_utc")
            or written_at < _utc(population["frozen_at_utc"], "population.frozen_at_utc")
            or written_at >= cutoff):
        raise ValidationError("Vertrauenswuerdige Forecast-Receipt-Zeit liegt ausserhalb des Fensters")
    timestamps = record["source_timestamps"]
    if not isinstance(timestamps, dict) or "market" not in timestamps:
        raise ValidationError("source_timestamps.market fehlt")
    source_times = {_safe(key, "source_timestamp_key"): _utc(
        value, f"source_timestamps.{key}") for key, value in timestamps.items()}
    if any(value > generated or value >= cutoff for value in source_times.values()):
        raise ValidationError("Forecast nutzt spaete Quelldaten")
    expected_hashes = {"code_sha256": manifest["code_sha256"],
                       "config_sha256": manifest["config"]["sha256"],
                       "model_sha256": manifest["model"]["sha256"],
                       "training_sha256": manifest["training"]["sha256"]}
    if any(record[key] != value for key, value in expected_hashes.items()) or record[
            "git_commit"] != manifest["git_commit"] or record["model_version"] != manifest[
                "model"]["model_version"]:
        raise ValidationError("Forecast-Code/Config/Modell/Training nicht manifestgebunden")
    base = _probs(record["base_model_probs"], "base_model_probs")
    raw = _probs(record["raw_market_probs"], "raw_market_probs")
    alpha0 = _probs(record["alpha0_probs"], "alpha0_probs")
    candidate = _probs(record["candidate_probs"], "candidate_probs")
    frozen_params = manifest["config"]["frozen_parameters"][record["competition"]]
    if record["candidate_parameters"] != frozen_params:
        raise ValidationError("Kandidatenparameter sind nicht eingefroren")
    expected_alpha0 = _alpha0(raw, manifest, record["competition"])
    alpha = float(frozen_params["alpha"])
    expected_candidate = {key: (1 - alpha) * expected_alpha0[key] + alpha * base[key]
                          for key in OUTCOMES}
    if not _same_probs(alpha0, expected_alpha0) or not _same_probs(candidate, expected_candidate):
        raise ValidationError("Candidate/raw/alpha0 sind rechnerisch inkonsistent")
    if record["quality_status"] != "complete":
        raise ValidationError("Primaerer Forecast braucht quality_status=complete")
    payload = dict(record)
    payload.update({"manifest_sha256": manifest["manifest_sha256"],
                    "population_sha256": population["population_sha256"],
                    "written_at_utc": written_at.isoformat(timespec="seconds").replace("+00:00", "Z"),
                    "cutoff_utc": cutoff.isoformat().replace("+00:00", "Z"),
                    **_blocked_fields()})
    return _write(root, version, "forecasts", match_id, record["forecast_id"], payload)


_CLOSING_FIELDS = {"candidate_version", "match_id", "closing_id", "capture_id",
                   "scheduled_kickoff_utc", "source_captured_at_utc", "captured_at_utc",
                   "source", "status", "books", "raw_quotes", "devig_method",
                   "consensus_method", "raw_closing_probs", "mode", "auto_apply",
                   "prediction_allowed", "value_allowed", "stake_allowed"}


def write_closing(root: Path, record: dict) -> dict:
    if set(record) != _CLOSING_FIELDS:
        raise ValidationError("Closing hat unbekannte oder fehlende Felder")
    _flags(record)
    version, match_id = _safe(record["candidate_version"], "candidate_version"), _safe(
        record["match_id"], "match_id")
    _safe(record["capture_id"], "capture_id")
    manifest, population, fixture = _fixture(root, version, match_id)
    if record["scheduled_kickoff_utc"] != fixture["scheduled_kickoff_utc"]:
        raise ValidationError("Closing-Kickoff weicht vom Ledger ab")
    source_at = _utc(record["source_captured_at_utc"], "source_captured_at_utc")
    captured_at = _utc(record["captured_at_utc"], "captured_at_utc")
    if source_at != captured_at:
        raise ValidationError("Primary Closing muss atomar denselben Capture-Zeitpunkt verwenden")
    kickoff = _utc(record["scheduled_kickoff_utc"], "scheduled_kickoff_utc")
    cutoff = kickoff - dt.timedelta(minutes=5)
    written_at = _now_utc()
    staleness = (cutoff - source_at).total_seconds()
    if source_at >= cutoff or staleness > manifest["capture"]["max_staleness_seconds"]:
        raise ValidationError("Closing liegt ausserhalb der T-5-Staleness-Policy")
    if source_at < _utc(population["frozen_at_utc"], "population.frozen_at_utc"):
        raise ValidationError("Retrospektiver Closing-Backfill ist verboten")
    if (written_at < captured_at or written_at < source_at
            or written_at < _utc(manifest["frozen_at_utc"], "frozen_at_utc")
            or written_at < _utc(population["frozen_at_utc"], "population.frozen_at_utc")
            or written_at >= cutoff):
        raise ValidationError("Vertrauenswuerdige Closing-Receipt-Zeit liegt ausserhalb des Fensters")
    whitelist = manifest["market"]["book_whitelist"]
    if (record["books"] != whitelist or set(record["raw_quotes"]) != set(whitelist)
            or record["devig_method"] != manifest["market"]["devig_method"]
            or record["consensus_method"] != manifest["market"]["consensus_method"]
            or record["source"] != manifest["market"]["source"]
            or record["status"] != "complete"):
        raise ValidationError("Closing-Quelle/Whitelist/Methodik/Status nicht manifestkonform")
    for book, odds in record["raw_quotes"].items():
        if set(odds) != set(OUTCOMES) or any(not isinstance(v, (int, float)) or v <= 1 for v in odds.values()):
            raise ValidationError(f"Ungueltige Rohquoten fuer {book}")
    raw = _probs(record["raw_closing_probs"], "raw_closing_probs")
    per_book = []
    for odds in record["raw_quotes"].values():
        inverse = {key: 1.0 / odds[key] for key in OUTCOMES}
        total = sum(inverse.values())
        per_book.append({key: inverse[key] / total for key in OUTCOMES})
    expected_raw = {key: sum(row[key] for row in per_book) / len(per_book)
                    for key in OUTCOMES}
    if not _same_probs(raw, expected_raw):
        raise ValidationError("Raw Closing stimmt nicht mit Whitelist/De-vig/Konsens ueberein")
    payload = dict(record)
    payload.update({"manifest_sha256": manifest["manifest_sha256"],
                    "population_sha256": population["population_sha256"],
                    "written_at_utc": written_at.isoformat(timespec="seconds").replace("+00:00", "Z"),
                    **_blocked_fields()})
    return _write(root, version, "closings", match_id, record["closing_id"], payload)


def write_official_closing(root: Path, record: dict) -> dict:
    """Store a secondary official close; it is never read by primary evaluation."""
    allowed = {"candidate_version", "match_id", "official_closing_id", "captured_at_utc",
               "source", "status", "official_closing_probs", "mode", "auto_apply",
               "prediction_allowed", "value_allowed", "stake_allowed"}
    if set(record) != allowed:
        raise ValidationError("Official Closing hat unbekannte oder fehlende Felder")
    version, match_id = _safe(record.get("candidate_version"), "candidate_version"), _safe(
        record.get("match_id"), "match_id")
    manifest, population, _ = _fixture(root, version, match_id)
    _flags(record)
    _utc(record.get("captured_at_utc"), "captured_at_utc")
    if (record["source"] != manifest["market"]["official_closing_source"]
            or record["status"] != "official_final"):
        raise ValidationError("Official-Closing-Quelle/Status ist nicht manifestkonform")
    probs = _probs(record.get("official_closing_probs"), "official_closing_probs")
    payload = {**record, "official_closing_probs": probs,
               "manifest_sha256": manifest["manifest_sha256"],
               "population_sha256": population["population_sha256"], **_blocked_fields()}
    return _write(root, version, "official_closings", match_id,
                  record.get("official_closing_id") or match_id, payload)


def _write(root: Path, version: str, kind: str, match_id: str,
           record_id: object, payload: dict) -> dict:
    record_id = _safe(record_id, f"{kind}_id")
    envelope = _envelope(kind, payload)
    path = _record_path(root, version, kind, match_id, record_id)
    if path.exists():
        existing, digest = _read(path, kind)
        comparable_existing, comparable_new = dict(existing), dict(payload)
        comparable_existing.pop("written_at_utc", None)
        comparable_new.pop("written_at_utc", None)
        if comparable_existing == comparable_new:
            return {"status": "idempotent", "path": str(path), "sha256": digest}
    status = _atomic_create(path, envelope)
    return {"status": status, "path": str(path), "sha256": envelope["integrity"]["digest"]}


def _one_record(root: Path, version: str, kind: str, match_id: str) -> dict | None:
    paths = sorted((Path(root) / version / kind / match_id).glob("*.json"))
    if len(paths) > 1:
        raise IntegrityError(f"Mehrdeutige {kind} fuer {match_id}")
    if not paths:
        return None
    payload, digest = _read(paths[0], kind)
    id_fields = {"forecasts": "forecast_id", "closings": "closing_id",
                 "results": "result_id", "official_closings": "official_closing_id"}
    id_field = id_fields.get(kind)
    if (payload.get("candidate_version") != version or payload.get("match_id") != match_id
            or not id_field or payload.get(id_field) != paths[0].stem):
        raise IntegrityError(f"Pfad/Payload-Bindung fuer {kind}/{match_id} gebrochen")
    return {**payload, "_artifact_digest": digest, "_record_id": payload[id_field]}


def write_result(root: Path, record: dict) -> dict:
    allowed = {"candidate_version", "match_id", "result_id", "status", "outcome",
               "home_goals", "away_goals", "captured_at_utc", "actual_kickoff_utc",
               "finished_at_utc", "source", "mode", "auto_apply", "prediction_allowed", "value_allowed",
               "stake_allowed"}
    if set(record) != allowed:
        raise ValidationError("Resultat hat unbekannte oder fehlende Felder")
    _flags(record)
    version, match_id = _safe(record["candidate_version"], "candidate_version"), _safe(
        record["match_id"], "match_id")
    manifest, population, fixture = _fixture(root, version, match_id)
    if record["status"] != "FINAL" or record["outcome"] not in OUTCOMES:
        raise ValidationError("Nur regulaere FINAL-Resultate sind primaer auswertbar")
    actual = _utc(record["actual_kickoff_utc"], "actual_kickoff_utc")
    finished = _utc(record["finished_at_utc"], "finished_at_utc")
    captured = _utc(record["captured_at_utc"], "captured_at_utc")
    written_at = _now_utc()
    if not actual < finished <= captured:
        raise ValidationError("FINAL braucht actual kickoff < finished <= captured")
    if written_at < captured:
        raise ValidationError("Result-Receipt muss nach captured/finished/actual liegen")
    if (finished - actual).total_seconds() < manifest["results"]["min_match_duration_seconds"]:
        raise ValidationError("FINAL unterschreitet die manifestierte Mindestspieldauer")
    if record["source"] != manifest["results"]["authoritative_source"]:
        raise ValidationError("Resultatquelle ist nicht manifestkonform")
    forecast = _one_record(root, version, "forecasts", match_id)
    closing = _one_record(root, version, "closings", match_id)
    if not forecast or not closing:
        raise ValidationError("FINAL-Resultat erfordert vorherigen Forecast und Capture")
    if captured <= max(_utc(forecast["generated_at_utc"], "generated_at_utc"),
                       _utc(closing["source_captured_at_utc"], "source_captured_at_utc")):
        raise ValidationError("Resultat-Chronologie ist ungueltig")
    if actual <= max(_utc(closing["source_captured_at_utc"], "source_captured_at_utc"),
                     _utc(forecast["generated_at_utc"], "generated_at_utc"),
                     *(_utc(value, f"source_timestamps.{key}")
                       for key, value in forecast["source_timestamps"].items())):
        raise ValidationError("Forecast/Input lag nach actual kickoff")
    goals = (record["home_goals"], record["away_goals"])
    if any(not isinstance(x, int) or x < 0 for x in goals):
        raise ValidationError("Tore muessen nichtnegative Ganzzahlen sein")
    expected = "team1_win" if goals[0] > goals[1] else ("team2_win" if goals[1] > goals[0] else "draw")
    if record["outcome"] != expected:
        raise ValidationError("Outcome und Tore widersprechen sich")
    payload = {**record, "scheduled_kickoff_utc": fixture["scheduled_kickoff_utc"],
               "manifest_sha256": manifest["manifest_sha256"],
               "population_sha256": population["population_sha256"], **_blocked_fields()}
    payload["written_at_utc"] = written_at.isoformat(timespec="seconds").replace("+00:00", "Z")
    return _write(root, version, "results", match_id, record["result_id"], payload)


def _bootstrap_bounds(rows: list[dict], field: str, manifest: dict, test_mode: bool) -> tuple[float, float]:
    if not rows:
        return (math.nan, math.nan)
    clusters: dict[str, list[float]] = {}
    for row in rows:
        clusters.setdefault(row["cluster"], []).append(row[field])
    iterations = 100 if test_mode else manifest["inference"]["bootstrap_iterations"]
    seed = manifest["inference"]["bootstrap_seed"]
    confidence = manifest["inference"]["confidence_level"]
    rng, keys, estimates = random.Random(seed), sorted(clusters), []
    for _ in range(iterations):
        sampled = [rng.choice(keys) for _ in keys]
        values = [v for key in sampled for v in clusters[key]]
        estimates.append(sum(values) / len(values))
    estimates.sort()
    lo = _nearest_rank(estimates, 1 - confidence)
    hi = _nearest_rank(estimates, confidence)
    return lo, hi


def _nearest_rank(sorted_values: list[float], quantile: float) -> float:
    if not sorted_values or not 0 <= quantile <= 1:
        raise ValidationError("Ungueltiges Quantil")
    index = min(len(sorted_values) - 1, max(0, math.ceil(quantile * len(sorted_values)) - 1))
    return sorted_values[index]


def _comparison(rows: list[dict], benchmark: str, manifest: dict, test_mode: bool) -> dict:
    out = {}
    for metric in ("rps", "log_loss"):
        field = f"delta_{metric}_vs_{benchmark}"
        values = [row[field] for row in rows]
        lower, upper = _bootstrap_bounds(rows, field, manifest, test_mode)
        out[metric] = {"n": len(values), "mean_delta": sum(values) / len(values) if values else None,
                       "bootstrap_lower": lower if values else None,
                       "bootstrap_upper": upper if values else None,
                       "passed": bool(values and sum(values) / len(values) < 0 and upper < 0)}
    return out


def _blocked(version: str, note: str) -> dict:
    return {"status": "blocked", "candidate_version": version, "integrity_ok": False,
            "n_population": 0, "n_paired": 0, "coverage": 0.0, "missing": [], "rows": [],
            "gates": {"integrity": False, "artifact_completeness": False, "release": False},
            **_blocked_fields(), "note": note}


def evaluate(root: Path, version: str = DEFAULT_CANDIDATE_VERSION, *,
             evaluation_mode: str = "production", checkpoint_id: str | None = None) -> dict:
    """Evaluate one frozen epoch. Production settings come only from its manifest."""
    version = _safe(version, "candidate_version")
    if evaluation_mode not in ("production", "test"):
        raise ValidationError("evaluation_mode muss production oder test sein")
    test_mode = evaluation_mode == "test"
    try:
        manifest, population = load_manifest(root, version), load_population(root, version)
        checkpoint_valid = False
        checkpoint = None
        if not test_mode:
            requested = _safe(checkpoint_id, "checkpoint_id")
            checkpoint = next((row for row in manifest["evaluation_schedule"]
                               if row["checkpoint_id"] == requested), None)
            if checkpoint is None:
                raise ValidationError("Checkpoint ist nicht manifestiert")
            evaluated_at = _now_utc()
            opened = _utc(checkpoint["opens_at_utc"], "checkpoint.opens_at_utc")
            closed = _utc(checkpoint["closes_at_utc"], "checkpoint.closes_at_utc")
            if not opened <= evaluated_at <= closed:
                raise ValidationError("Formale Evaluation liegt ausserhalb des Checkpoint-Fensters")
            checkpoint_valid = True
        fixtures = {row["match_id"]: row for row in population["fixtures"]}
        rows, missing = [], []
        artifact_receipts: dict[str, dict[str, str]] = {kind: {} for kind in
                                                       ("forecasts", "closings", "results")}
        seen_ids: dict[str, set[str]] = {kind: set() for kind in artifact_receipts}
        seen_digests: dict[str, set[str]] = {kind: set() for kind in artifact_receipts}
        for match_id, fixture in sorted(fixtures.items()):
            forecast = _one_record(root, version, "forecasts", match_id)
            closing = _one_record(root, version, "closings", match_id)
            result = _one_record(root, version, "results", match_id)
            for kind, artifact in (("forecasts", forecast), ("closings", closing),
                                   ("results", result)):
                if artifact is None:
                    continue
                record_id, digest = artifact["_record_id"], artifact["_artifact_digest"]
                if record_id in seen_ids[kind] or digest in seen_digests[kind]:
                    raise IntegrityError(f"Doppelte Artefakt-ID/Digest ueber Matches: {kind}")
                seen_ids[kind].add(record_id)
                seen_digests[kind].add(digest)
                artifact_receipts[kind][match_id] = digest
            absent = [name for name, value in (("forecast", forecast), ("closing", closing),
                                                ("result", result)) if value is None]
            if absent:
                missing.append({"match_id": match_id, "missing": absent})
                continue
            if (forecast["manifest_sha256"] != manifest["manifest_sha256"]
                    or closing["manifest_sha256"] != manifest["manifest_sha256"]
                    or result["manifest_sha256"] != manifest["manifest_sha256"]
                    or any(x["population_sha256"] != population["population_sha256"]
                           for x in (forecast, closing, result))):
                raise IntegrityError("Record-Bindung an Manifest/Population gebrochen")
            for artifact in (forecast, closing, result):
                written = _utc(artifact["written_at_utc"], "written_at_utc")
                if not test_mode and (written > closed or written > evaluated_at):
                    raise IntegrityError("Artefakt wurde nach Checkpoint/Evaluation geschrieben")
            if not (_utc(result["actual_kickoff_utc"], "actual_kickoff_utc")
                    < _utc(result["finished_at_utc"], "finished_at_utc")
                    <= _utc(result["captured_at_utc"], "captured_at_utc")
                    <= _utc(result["written_at_utc"], "written_at_utc")):
                raise IntegrityError("Result-Receipt-Chronologie ist ungueltig")
            if (result["source"] != manifest["results"]["authoritative_source"]
                    or (_utc(result["finished_at_utc"], "finished_at_utc")
                        - _utc(result["actual_kickoff_utc"], "actual_kickoff_utc")).total_seconds()
                    < manifest["results"]["min_match_duration_seconds"]):
                raise IntegrityError("Result-Receipt verletzt Quelle/Mindestdauer")
            if (forecast["capture_id"] != closing["capture_id"]
                    or forecast["scheduled_kickoff_utc"] != closing["scheduled_kickoff_utc"]
                    or forecast["source_timestamps"]["market"] != closing["source_captured_at_utc"]
                    or not _same_probs(forecast["raw_market_probs"], closing["raw_closing_probs"])):
                raise IntegrityError("Forecast und primaerer Closing-Capture sind nicht atomar gebunden")
            raw, alpha0, candidate = (_probs(forecast[name], name) for name in
                                      ("raw_market_probs", "alpha0_probs", "candidate_probs"))
            if not _same_probs(alpha0, _alpha0(raw, manifest, fixture["competition"])):
                raise IntegrityError("Alpha0 stimmt nicht mit dem Capture ueberein")
            outcome = result["outcome"]
            cluster = (f"{fixture['competition']}|{fixture['season']}|md{fixture['matchday']}"
                       if fixture.get("matchday") else
                       f"{fixture['competition']}|{fixture['scheduled_kickoff_utc'][:10]}")
            row = {"match_id": match_id, "competition": fixture["competition"],
                   "season": fixture["season"], "matchday": fixture["matchday"],
                   "promoted_match": forecast["promoted_match"], "outcome": outcome,
                   "cluster": cluster, "groups": {"draw": outcome == "draw",
                   "promoted": forecast["promoted_match"], "first_six": fixture["matchday"] <= 6},
                   "candidate": {"rps": rps(candidate, outcome), "log_loss": log_loss(candidate, outcome)},
                   "raw_closing": {"rps": rps(raw, outcome), "log_loss": log_loss(raw, outcome)},
                   "alpha0_calibrator": {"rps": rps(alpha0, outcome), "log_loss": log_loss(alpha0, outcome)}}
            for bench in ("raw_closing", "alpha0_calibrator"):
                for metric in ("rps", "log_loss"):
                    row[f"delta_{metric}_vs_{bench}"] = row["candidate"][metric] - row[bench][metric]
            rows.append(row)
    except (LockboxError, OSError, KeyError, TypeError, ValueError) as exc:
        return _blocked(version, f"Integritaetsfehler: {exc}")

    n_population, n_paired = len(fixtures), len(rows)
    coverage = n_paired / n_population if n_population else 0.0
    comparisons = {bench: _comparison(rows, bench, manifest, test_mode)
                   for bench in ("raw_closing", "alpha0_calibrator")}
    per_league = {}
    league_point_wins = 0
    no_clear_harm = True
    for league in REQUIRED_LEAGUES:
        league_rows = [row for row in rows if row["competition"] == league]
        blocks = {bench: _comparison(league_rows, bench, manifest, test_mode)
                  for bench in ("raw_closing", "alpha0_calibrator")}
        point_win = bool(league_rows and all(
            blocks[bench][metric]["mean_delta"] < 0
            for bench in blocks for metric in ("rps", "log_loss")))
        league_point_wins += int(point_win)
        for bench in blocks:
            for metric in blocks[bench].values():
                no_clear_harm &= metric["bootstrap_lower"] is None or metric["bootstrap_lower"] <= 0
        per_league[league] = {"n": len(league_rows), "point_win_all": point_win,
                              "comparisons": blocks}
    guardrails = {}
    guardrail_ok = True
    for group in manifest["guardrails"]["groups"]:
        group_rows = [row for row in rows if row["groups"][group]]
        blocks = {bench: _comparison(group_rows, bench, manifest, test_mode)
                  for bench in ("raw_closing", "alpha0_calibrator")}
        enough = len(group_rows) >= manifest["guardrails"]["minimum_n"]
        passed = enough and all(
            blocks[bench]["rps"]["bootstrap_upper"] <= manifest["guardrails"]["rps_upper_limit"]
            and blocks[bench]["log_loss"]["bootstrap_upper"] <= manifest[
                "guardrails"]["log_loss_upper_limit"] for bench in blocks)
        guardrail_ok &= passed
        guardrails[group] = {"status": "passed" if passed else (
            "insufficient_data" if not enough else "failed"), "n": len(group_rows),
            "comparisons": blocks}
    league_ns = [per_league[x]["n"] for x in REQUIRED_LEAGUES]
    gates = {"integrity": True, "artifact_completeness": not missing,
             "coverage": coverage >= manifest["gates"]["coverage"],
             "diagnostic_sample": n_paired >= manifest["gates"]["diagnostic_total"] and min(
                 league_ns, default=0) >= manifest["gates"]["diagnostic_per_league"],
             "definitive_sample": n_paired >= manifest["gates"]["definitive_total"] and min(
                 league_ns, default=0) >= manifest["gates"]["definitive_per_league"],
             "aggregate_both_benchmarks_metrics": all(
                 comparisons[b][m]["passed"] for b in comparisons for m in ("rps", "log_loss")),
             "league_wins": league_point_wins >= manifest["gates"]["league_wins_required"],
             "no_clear_league_harm": no_clear_harm, "guardrails": guardrail_ok,
             "scheduled_evaluation": checkpoint_valid,
             "release": False}
    diagnostic_ready = gates["diagnostic_sample"]
    definitive_gate_keys = ("integrity", "coverage", "definitive_sample",
                            "aggregate_both_benchmarks_metrics", "league_wins",
                            "no_clear_league_harm", "guardrails", "scheduled_evaluation")
    statistically_definitive = bool(not test_mode and checkpoint_valid and all(
        gates[key] for key in definitive_gate_keys))
    quant_status = ("definitive_ready" if statistically_definitive else
                    ("diagnostic" if diagnostic_ready else "insufficient_data"))
    output = {"status": quant_status, "quant_status": quant_status,
            "candidate_version": version, "lockbox_id": manifest["lockbox_id"],
            "epoch_id": manifest["epoch_id"], "manifest_sha256": manifest["manifest_sha256"],
            "population_sha256": population["population_sha256"], "integrity_ok": True,
            "artifact_completeness": not missing, "n_population": n_population,
            "n_forecasts": sum(_one_record(root, version, "forecasts", x) is not None for x in fixtures),
            "n_paired": n_paired, "coverage": coverage, "missing": missing, "rows": rows,
            "comparisons": comparisons, "per_league": per_league, "guardrails": guardrails,
            "bootstrap": {"iterations": 100 if test_mode else manifest["inference"]["bootstrap_iterations"],
                          "seed": manifest["inference"]["bootstrap_seed"],
                          "confidence_level": manifest["inference"]["confidence_level"],
                          "cluster": manifest["inference"]["cluster"], "test_mode": test_mode},
            "gates": gates, "statistically_definitive": statistically_definitive,
            "checkpoint_id": checkpoint_id if not test_mode else None,
            **_blocked_fields(), "note": "Shadow-Lockbox; reale Freigabe bleibt blockiert."}
    if not test_mode:
        receipt_payload = {"candidate_version": version, "checkpoint_id": checkpoint_id,
                           "checkpoint_opens_at_utc": checkpoint["opens_at_utc"],
                           "checkpoint_closes_at_utc": checkpoint["closes_at_utc"],
                           "evaluated_at_utc": evaluated_at.isoformat(timespec="seconds").replace(
                               "+00:00", "Z"),
                           "manifest_sha256": manifest["manifest_sha256"],
                           "population_sha256": population["population_sha256"],
                           "artifact_digests": artifact_receipts,
                           "evaluation_sha256": _sha({key: output[key] for key in
                                                      ("n_population", "n_paired", "coverage",
                                                       "comparisons", "per_league", "guardrails",
                                                       "gates", "statistically_definitive")}),
                           "previous_receipt_sha256": None, **_blocked_fields()}
        try:
            checkpoint_index = manifest["evaluation_schedule"].index(checkpoint)
            previous_digest = None
            for previous in manifest["evaluation_schedule"][:checkpoint_index]:
                previous_path = (Path(root) / version / "evaluations" /
                                 f"{previous['checkpoint_id']}.json")
                previous_payload, previous_digest = _read(previous_path, "evaluation_receipt")
                if (previous_payload.get("candidate_version") != version
                        or previous_payload.get("checkpoint_id") != previous["checkpoint_id"]
                        or previous_payload.get("previous_receipt_sha256") != (
                            None if previous == manifest["evaluation_schedule"][0]
                            else prior_chain_digest)):
                    raise IntegrityError("Frueheres Checkpoint-Receipt ist ungueltig")
                prior_chain_digest = previous_digest
            receipt_payload["previous_receipt_sha256"] = previous_digest
            receipt = _envelope("evaluation_receipt", receipt_payload)
            receipt_status = _atomic_create(Path(root) / version / "evaluations" /
                                            f"{checkpoint_id}.json", receipt)
        except (LockboxError, OSError) as exc:
            return _blocked(version, f"Checkpoint-Receipt-Konflikt: {exc}")
        output["evaluation_receipt"] = {"status": receipt_status,
                                        "sha256": receipt["integrity"]["digest"]}
    return output


def evaluate_cohort(members: list[dict], *, evaluation_mode: str = "production",
                    cohort_root: Path | None = None, cohort_id: str | None = None) -> dict:
    """Combine formally closed, fingerprint-identical and disjoint epochs read-only."""
    if evaluation_mode not in ("production", "test") or not members:
        raise ValidationError("Cohort braucht Mitglieder und gueltigen Modus")
    test_mode = evaluation_mode == "test"
    try:
        manifests, populations, all_rows, inputs = [], [], [], []
        expected_fingerprint = None
        epoch_keys, population_hashes, match_ids = set(), set(), set()
        fingerprint_names = ("config", "model", "training", "market", "capture",
                             "benchmarks", "results", "inference", "gates", "guardrails")
        for member in members:
            if not isinstance(member, dict) or set(member) != {"root", "version", "checkpoint_id"}:
                raise IntegrityError("Ungueltiger Cohort-Member")
            root, version = Path(member["root"]), _safe(member["version"], "candidate_version")
            manifest, population = load_manifest(root, version), load_population(root, version)
            receipt_path = root / version / "evaluations" / f"{member['checkpoint_id']}.json"
            receipt, receipt_digest = _read(receipt_path, "evaluation_receipt")
            if (receipt.get("candidate_version") != version
                    or receipt.get("checkpoint_id") != member["checkpoint_id"]
                    or receipt.get("manifest_sha256") != manifest["manifest_sha256"]
                    or receipt.get("population_sha256") != population["population_sha256"]):
                raise IntegrityError("Cohort-Checkpoint-Receipt ist nicht gebunden")
            current_digests = {kind: {} for kind in ("forecasts", "closings", "results")}
            for fixture_row in population["fixtures"]:
                for kind in current_digests:
                    artifact = _one_record(root, version, kind, fixture_row["match_id"])
                    if artifact is not None:
                        current_digests[kind][fixture_row["match_id"]] = artifact["_artifact_digest"]
            if receipt.get("artifact_digests") != current_digests:
                raise IntegrityError("Cohort-Artefakte weichen vom formalen Receipt ab")
            fingerprint = {"candidate_name": manifest["candidate_name"],
                           "candidate_version": manifest["candidate_version"],
                           "code_sha256": manifest["code_sha256"],
                           **{name: manifest["component_fingerprints"][name]
                              for name in fingerprint_names}}
            if expected_fingerprint is None:
                expected_fingerprint = fingerprint
            elif fingerprint != expected_fingerprint:
                raise IntegrityError("Cohort-Fingerprints stimmen nicht ueberein")
            epoch_key = (manifest["lockbox_id"], manifest["epoch_id"])
            if epoch_key in epoch_keys or population["population_sha256"] in population_hashes:
                raise IntegrityError("Cohort-Epochen/Populationen sind nicht disjunkt")
            epoch_keys.add(epoch_key)
            population_hashes.add(population["population_sha256"])
            current_ids = {row["match_id"] for row in population["fixtures"]}
            if match_ids & current_ids:
                raise IntegrityError("Doppelte match_id ueber Cohort-Epochen")
            match_ids |= current_ids
            evaluated = evaluate(root, version, evaluation_mode="test")
            if not evaluated["integrity_ok"]:
                raise IntegrityError("Cohort-Epoch ist nicht integer")
            all_rows.extend(evaluated["rows"])
            manifests.append(manifest)
            populations.append(population)
            inputs.append({"lockbox_id": manifest["lockbox_id"], "epoch_id": manifest["epoch_id"],
                           "manifest_sha256": manifest["manifest_sha256"],
                           "population_sha256": population["population_sha256"],
                           "checkpoint_id": member["checkpoint_id"],
                           "receipt_sha256": receipt_digest})
        manifest = manifests[0]
        comparisons = {bench: _comparison(all_rows, bench, manifest, test_mode)
                       for bench in ("raw_closing", "alpha0_calibrator")}
        per_league, league_wins, no_harm = {}, 0, True
        for league in REQUIRED_LEAGUES:
            league_rows = [row for row in all_rows if row["competition"] == league]
            blocks = {bench: _comparison(league_rows, bench, manifest, test_mode)
                      for bench in comparisons}
            won = bool(league_rows and all(blocks[b][m]["mean_delta"] < 0
                                           for b in blocks for m in ("rps", "log_loss")))
            league_wins += int(won)
            no_harm &= all(blocks[b][m]["bootstrap_lower"] is None
                           or blocks[b][m]["bootstrap_lower"] <= 0
                           for b in blocks for m in ("rps", "log_loss"))
            per_league[league] = {"n": len(league_rows), "point_win_all": won,
                                  "comparisons": blocks}
        guardrails, guardrail_ok = {}, True
        for group in manifest["guardrails"]["groups"]:
            grouped = [row for row in all_rows if row["groups"][group]]
            blocks = {bench: _comparison(grouped, bench, manifest, test_mode)
                      for bench in comparisons}
            enough = len(grouped) >= manifest["guardrails"]["minimum_n"]
            passed = enough and all(
                blocks[b]["rps"]["bootstrap_upper"] <= manifest["guardrails"]["rps_upper_limit"]
                and blocks[b]["log_loss"]["bootstrap_upper"] <= manifest[
                    "guardrails"]["log_loss_upper_limit"] for b in blocks)
            guardrail_ok &= passed
            guardrails[group] = {"n": len(grouped), "status": "passed" if passed else (
                "insufficient_data" if not enough else "failed"), "comparisons": blocks}
    except (LockboxError, OSError, KeyError, TypeError, ValueError) as exc:
        return _blocked("cohort", f"Cohort-Integritaetsfehler: {exc}")
    league_ns = [per_league[x]["n"] for x in REQUIRED_LEAGUES]
    n_population, n_paired = sum(len(x["fixtures"]) for x in populations), len(all_rows)
    coverage = n_paired / n_population if n_population else 0.0
    gates = {"integrity": True, "coverage": coverage >= manifest["gates"]["coverage"],
             "diagnostic_sample": n_paired >= manifest["gates"]["diagnostic_total"] and min(
                 league_ns) >= manifest["gates"]["diagnostic_per_league"],
             "definitive_sample": n_paired >= manifest["gates"]["definitive_total"] and min(
                 league_ns) >= manifest["gates"]["definitive_per_league"],
             "aggregate_both_benchmarks_metrics": all(comparisons[b][m]["passed"]
                 for b in comparisons for m in ("rps", "log_loss")),
             "league_wins": league_wins >= manifest["gates"]["league_wins_required"],
             "no_clear_league_harm": no_harm, "guardrails": guardrail_ok, "release": False}
    definitive = bool(not test_mode and all(v for k, v in gates.items() if k != "release"))
    quant_status = "definitive_ready" if definitive else (
        "diagnostic" if gates["diagnostic_sample"] else "insufficient_data")
    output = {"status": quant_status, "quant_status": quant_status,
              "candidate_version": manifest["candidate_version"], "n_epochs": len(members),
              "n_population": n_population, "n_paired": n_paired, "coverage": coverage,
              "rows": all_rows, "comparisons": comparisons, "per_league": per_league,
              "guardrails": guardrails, "gates": gates, "statistically_definitive": definitive,
              "cohort_inputs": inputs, "cohort_inputs_sha256": _sha({"inputs": inputs}),
              **_blocked_fields()}
    if not test_mode:
        if cohort_root is None:
            return _blocked("cohort", "Production-Cohort braucht create-only cohort_root")
        safe_cohort = _safe(cohort_id, "cohort_id")
        receipt = _envelope("cohort_receipt", {"cohort_id": safe_cohort,
            "inputs": inputs, "inputs_sha256": output["cohort_inputs_sha256"],
            "evaluation_sha256": _sha({"gates": gates, "comparisons": comparisons,
                                       "per_league": per_league, "guardrails": guardrails}),
            **_blocked_fields()})
        try:
            status = _atomic_create(Path(cohort_root) / "cohorts" / f"{safe_cohort}.json", receipt)
        except LockboxError as exc:
            return _blocked("cohort", f"Cohort-Receipt-Konflikt: {exc}")
        output["cohort_receipt"] = {"status": status, "sha256": receipt["integrity"]["digest"]}
    return output

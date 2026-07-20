"""Append-only shadow lockbox for prospective club-football forecasts.

The module deliberately has no network or production-pipeline dependencies.  It
stores forecasts, fixed-cutoff market captures, and results as separate,
create-only JSON artifacts and evaluates exactly one frozen candidate version.
Every public result remains report-only and blocked from automatic use.
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

from src.model.calibration import log_loss, rps


SCHEMA_VERSION = "club-lockbox-v1"
DEFAULT_CANDIDATE_VERSION = "closing_residual_v1"
DEFAULT_CUTOFF_MINUTES = 5
DEFAULT_BOOTSTRAP_ITERATIONS = 10_000
OUTCOMES = ("team1_win", "draw", "team2_win")
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")

DEFAULT_GATE_CONFIG = {
    "minimum_coverage": 0.95,
    "minimum_paired_n": 200,
    "minimum_days": 60,
    "minimum_leagues": 4,
    "confidence_level": 0.95,
}


class LockboxError(RuntimeError):
    """Base exception for a rejected lockbox operation."""


class ArtifactConflictError(LockboxError):
    """A create-only identifier already exists with different content."""


class IntegrityError(LockboxError):
    """An artifact or manifest failed its SHA-256 check."""


class ValidationError(LockboxError, ValueError):
    """A record violates the prospective lockbox contract."""


def _canonical_bytes(value: dict) -> bytes:
    try:
        text = json.dumps(value, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"Nicht kanonisch serialisierbar: {exc}") from exc
    return (text + "\n").encode("utf-8")


def _sha256(value: dict) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _safe_id(value: object, field: str) -> str:
    clean = str(value or "").strip()
    if not _SAFE_ID.fullmatch(clean):
        raise ValidationError(f"{field} muss eine sichere stabile ID sein")
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


def _probabilities(value: object, field: str) -> dict[str, float]:
    if not isinstance(value, dict) or set(value) != set(OUTCOMES):
        raise ValidationError(f"{field} muss exakt die drei 1X2-Ausgaenge enthalten")
    try:
        probs = {key: float(value[key]) for key in OUTCOMES}
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field} enthaelt keine gueltigen Zahlen") from exc
    if any(not math.isfinite(p) or p < 0.0 or p > 1.0 for p in probs.values()):
        raise ValidationError(f"{field} muss endliche Wahrscheinlichkeiten in [0,1] enthalten")
    if not math.isclose(sum(probs.values()), 1.0, rel_tol=0.0, abs_tol=1e-9):
        raise ValidationError(f"{field} muss auf 1 normiert sein")
    return probs


def _envelope(kind: str, payload: dict) -> dict:
    signed = {"schema_version": SCHEMA_VERSION, "kind": kind, "payload": payload}
    return {**signed, "integrity": {"algorithm": "sha256", "digest": _sha256(signed)}}


def _verify_envelope(value: dict, expected_kind: str | None = None) -> dict:
    if not isinstance(value, dict):
        raise IntegrityError("Artefakt ist kein JSON-Objekt")
    integrity = value.get("integrity") or {}
    signed = {key: value.get(key) for key in ("schema_version", "kind", "payload")}
    if value.get("schema_version") != SCHEMA_VERSION:
        raise IntegrityError("Unbekannte Lockbox-Schemaversion")
    if expected_kind and value.get("kind") != expected_kind:
        raise IntegrityError("Falscher Artefakttyp")
    if integrity.get("algorithm") != "sha256" or integrity.get("digest") != _sha256(signed):
        raise IntegrityError("SHA-256-Integritaetspruefung fehlgeschlagen")
    if not isinstance(value.get("payload"), dict):
        raise IntegrityError("Artefakt-Payload fehlt")
    return value["payload"]


def _atomic_create(path: Path, value: dict) -> str:
    """Atomically create *path*; identical retries are idempotent."""
    path.parent.mkdir(parents=True, exist_ok=True)
    content = _canonical_bytes(value)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp",
                                    dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(tmp_name, path)
        except FileExistsError:
            try:
                existing = path.read_bytes()
            except OSError as exc:
                raise ArtifactConflictError(f"Bestehendes Artefakt nicht lesbar: {path}") from exc
            if existing != content:
                raise ArtifactConflictError(f"Create-only-Konflikt: {path}")
            return "idempotent"
        return "created"
    finally:
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass


def _read(path: Path, kind: str | None = None) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise IntegrityError(f"Artefakt unlesbar: {path}") from exc
    return _verify_envelope(value, kind)


def _fingerprinted(label: str, value: dict) -> dict:
    if not isinstance(value, dict) or not value:
        raise ValidationError(f"{label} darf nicht leer sein")
    return {"value": value, "sha256": _sha256(value)}


def create_manifest(root: Path, *,
                    candidate_version: str = DEFAULT_CANDIDATE_VERSION,
                    created_at_utc: str,
                    candidate_config: dict,
                    training_definition: dict,
                    benchmark_definition: dict,
                    cutoff_minutes: int = DEFAULT_CUTOFF_MINUTES) -> dict:
    """Freeze a complete candidate manifest with independent fingerprints."""
    version = _safe_id(candidate_version, "candidate_version")
    _utc(created_at_utc, "created_at_utc")
    if not isinstance(cutoff_minutes, int) or cutoff_minutes < 1:
        raise ValidationError("cutoff_minutes muss eine positive ganze Zahl sein")
    cutoff = {"policy": "fixed_pre_kickoff", "minutes_before_kickoff": cutoff_minutes,
              "boundary": "strictly_before"}
    components = {
        "config": _fingerprinted("candidate_config", candidate_config),
        "training": _fingerprinted("training_definition", training_definition),
        "benchmarks": _fingerprinted("benchmark_definition", benchmark_definition),
        "cutoff": _fingerprinted("cutoff", cutoff),
    }
    fingerprint_input = {name: block["sha256"] for name, block in components.items()}
    payload = {
        "candidate_version": version,
        "candidate_name": "closing_residual_blend",
        "created_at_utc": created_at_utc,
        "components": components,
        "fingerprint_sha256": _sha256(fingerprint_input),
        "mode": "shadow",
        "release_status": "blocked",
        "auto_apply": False,
        "prediction_allowed": False,
        "value_allowed": False,
        "stake_allowed": False,
    }
    envelope = _envelope("manifest", payload)
    status = _atomic_create(Path(root) / version / "manifest.json", envelope)
    return {**payload, "manifest_sha256": envelope["integrity"]["digest"],
            "write_status": status}


def load_manifest(root: Path, candidate_version: str = DEFAULT_CANDIDATE_VERSION) -> dict:
    version = _safe_id(candidate_version, "candidate_version")
    path = Path(root) / version / "manifest.json"
    payload = _read(path, "manifest")
    if payload.get("candidate_version") != version:
        raise IntegrityError("Manifest-Version und Pfad stimmen nicht ueberein")
    # Recompute every component as well as the aggregate fingerprint.
    components = payload.get("components") or {}
    for name in ("config", "training", "benchmarks", "cutoff"):
        block = components.get(name) or {}
        if block.get("sha256") != _sha256(block.get("value") or {}):
            raise IntegrityError(f"Manifest-Komponente {name} ist veraendert")
    aggregate = {name: components[name]["sha256"] for name in
                 ("config", "training", "benchmarks", "cutoff")}
    if payload.get("fingerprint_sha256") != _sha256(aggregate):
        raise IntegrityError("Manifest-Gesamtfingerprint ist ungueltig")
    envelope = json.loads(path.read_text(encoding="utf-8"))
    return {**payload, "manifest_sha256": envelope["integrity"]["digest"]}


def _artifact_path(root: Path, version: str, kind: str,
                   match_id: str, artifact_id: str) -> Path:
    return Path(root) / version / kind / match_id / f"{artifact_id}.json"


def _guard_flags(record: dict) -> None:
    if record.get("mode", "shadow") != "shadow":
        raise ValidationError("Lockbox-Artefakte duerfen nur shadow sein")
    for field in ("auto_apply", "prediction_allowed", "value_allowed", "stake_allowed"):
        if record.get(field, False) is not False:
            raise ValidationError(f"{field} muss false bleiben")


def _base_payload(root: Path, record: dict, time_field: str,
                  probs_field: str | None) -> tuple[dict, dict, str, str]:
    version = _safe_id(record.get("candidate_version"), "candidate_version")
    manifest = load_manifest(root, version)
    match_id = _safe_id(record.get("match_id"), "match_id")
    kickoff = _utc(record.get("kickoff_utc"), "kickoff_utc")
    captured = _utc(record.get(time_field), time_field)
    cutoff_minutes = manifest["components"]["cutoff"]["value"]["minutes_before_kickoff"]
    cutoff = kickoff - dt.timedelta(minutes=cutoff_minutes)
    if captured >= cutoff:
        raise ValidationError(f"{time_field} muss strikt vor dem festen Cutoff liegen")
    _guard_flags(record)
    payload = dict(record)
    if probs_field:
        payload[probs_field] = _probabilities(record.get(probs_field), probs_field)
    payload.update({
        "candidate_version": version,
        "match_id": match_id,
        "manifest_sha256": manifest["manifest_sha256"],
        "cutoff_utc": cutoff.isoformat().replace("+00:00", "Z"),
        "mode": "shadow", "release_status": "blocked", "auto_apply": False,
        "prediction_allowed": False, "value_allowed": False, "stake_allowed": False,
    })
    return payload, manifest, version, match_id


def _write_record(root: Path, kind: str, payload: dict, version: str,
                  match_id: str, artifact_id: str) -> dict:
    safe_artifact = _safe_id(artifact_id, f"{kind}_id")
    envelope = _envelope(kind, payload)
    path = _artifact_path(root, version, kind, match_id, safe_artifact)
    status = _atomic_create(path, envelope)
    return {"status": status, "path": str(path), "sha256": envelope["integrity"]["digest"]}


def write_forecast(root: Path, record: dict) -> dict:
    payload, _, version, match_id = _base_payload(
        root, record, "generated_at_utc", "candidate_probs")
    competition = _safe_id(record.get("competition"), "competition")
    payload["competition"] = competition
    artifact_id = record.get("forecast_id") or match_id
    payload["forecast_id"] = _safe_id(artifact_id, "forecast_id")
    return _write_record(root, "forecasts", payload, version, match_id, artifact_id)


def write_closing(root: Path, record: dict) -> dict:
    payload, _, version, match_id = _base_payload(
        root, record, "captured_at_utc", "raw_closing_probs")
    artifact_id = record.get("closing_id") or match_id
    payload["closing_id"] = _safe_id(artifact_id, "closing_id")
    return _write_record(root, "closings", payload, version, match_id, artifact_id)


def write_result(root: Path, record: dict) -> dict:
    version = _safe_id(record.get("candidate_version"), "candidate_version")
    manifest = load_manifest(root, version)
    match_id = _safe_id(record.get("match_id"), "match_id")
    _utc(record.get("captured_at_utc"), "captured_at_utc")
    _guard_flags(record)
    status = str(record.get("status") or "").upper()
    outcome = record.get("outcome")
    if status == "FINAL" and outcome not in OUTCOMES:
        raise ValidationError("FINAL-Resultat braucht einen gueltigen 1X2-Ausgang")
    if outcome is not None and outcome not in OUTCOMES:
        raise ValidationError("Unbekannter 1X2-Ausgang")
    payload = dict(record)
    payload.update({
        "candidate_version": version, "match_id": match_id, "status": status,
        "manifest_sha256": manifest["manifest_sha256"], "mode": "shadow",
        "release_status": "blocked", "auto_apply": False,
        "prediction_allowed": False, "value_allowed": False, "stake_allowed": False,
    })
    artifact_id = record.get("result_id") or f"{match_id}-{status.lower()}"
    payload["result_id"] = _safe_id(artifact_id, "result_id")
    return _write_record(root, "results", payload, version, match_id, artifact_id)


def _load_kind(root: Path, version: str, kind: str) -> list[dict]:
    base = Path(root) / version / kind
    if not base.exists():
        return []
    records = []
    for path in sorted(base.glob("*/*.json")):
        payload = _read(path, kind)
        if payload.get("candidate_version") != version:
            raise IntegrityError(f"Versionsvermischung in {path}")
        manifest = load_manifest(root, version)
        if payload.get("manifest_sha256") != manifest["manifest_sha256"]:
            raise IntegrityError(f"Manifest-Referenz stimmt nicht: {path}")
        records.append(payload)
    return records


def _unique_by_match(records: Iterable[dict], kind: str,
                     predicate=lambda _: True) -> dict[str, dict]:
    grouped: dict[str, list[dict]] = {}
    for record in records:
        if predicate(record):
            grouped.setdefault(record["match_id"], []).append(record)
    duplicate = [match_id for match_id, rows in grouped.items() if len(rows) != 1]
    if duplicate:
        raise IntegrityError(f"Mehrdeutige {kind}-Artefakte: {', '.join(sorted(duplicate))}")
    return {match_id: rows[0] for match_id, rows in grouped.items()}


def _alpha0_probs(raw: dict, manifest: dict, competition: str) -> dict:
    definition = manifest["components"]["benchmarks"]["value"]
    alpha0 = definition.get("alpha0_calibrator") or {}
    per_league = alpha0.get("by_competition") or {}
    params = per_league.get(competition, alpha0)
    temperature = float(params.get("temperature", 1.0))
    draw_multiplier = float(params.get("draw_multiplier", 1.0))
    if temperature <= 0 or draw_multiplier <= 0:
        raise IntegrityError("Ungueltige alpha0-Kalibratorparameter im Manifest")
    power = 1.0 / temperature
    adjusted = {key: max(raw[key], 1e-12) ** power for key in OUTCOMES}
    adjusted["draw"] *= draw_multiplier
    total = sum(adjusted.values())
    return {key: adjusted[key] / total for key in OUTCOMES}


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _bootstrap_upper(rows: list[dict], delta_field: str, *, iterations: int,
                     confidence_level: float, seed: int) -> float | None:
    if not rows:
        return None
    clusters: dict[str, list[float]] = {}
    for row in rows:
        clusters.setdefault(row["cluster_day"], []).append(row[delta_field])
    keys = sorted(clusters)
    rng = random.Random(seed)
    estimates = []
    for _ in range(iterations):
        sampled = [rng.choice(keys) for _ in keys]
        values = [value for key in sampled for value in clusters[key]]
        estimates.append(sum(values) / len(values))
    estimates.sort()
    index = min(len(estimates) - 1, max(0, math.ceil(confidence_level * len(estimates)) - 1))
    return estimates[index]


def _blocked_evaluation(version: str, note: str, *, integrity_ok: bool = False) -> dict:
    return {
        "status": "blocked", "candidate_version": version, "integrity_ok": integrity_ok,
        "n_forecasts": 0, "n_paired": 0, "coverage": 0.0, "rows": [],
        "gates": {"integrity": integrity_ok, "release": False},
        "release_status": "blocked", "auto_apply": False,
        "prediction_allowed": False, "value_allowed": False, "stake_allowed": False,
        "note": note,
    }


def evaluate(root: Path, candidate_version: str = DEFAULT_CANDIDATE_VERSION, *,
             gate_config: dict | None = None,
             bootstrap_iterations: int = DEFAULT_BOOTSTRAP_ITERATIONS,
             bootstrap_seed: int = 20260720) -> dict:
    """Evaluate one candidate version against raw close and alpha=0 calibration.

    Forecasts define the coverage denominator.  Only one forecast, one closing
    capture and one FINAL result per match are allowed; ambiguity fails closed.
    Per-match scores and deltas are intentionally left unrounded.
    """
    version = _safe_id(candidate_version, "candidate_version")
    if not isinstance(bootstrap_iterations, int) or bootstrap_iterations < 1:
        raise ValidationError("bootstrap_iterations muss positiv sein")
    gates_cfg = {**DEFAULT_GATE_CONFIG, **(gate_config or {})}
    try:
        manifest = load_manifest(root, version)
        forecasts = _unique_by_match(_load_kind(root, version, "forecasts"), "Forecast")
        closings = _unique_by_match(_load_kind(root, version, "closings"), "Closing")
        results = _unique_by_match(
            _load_kind(root, version, "results"), "FINAL-Resultat",
            lambda row: row.get("status") == "FINAL")
    except (LockboxError, OSError, KeyError, TypeError, ValueError) as exc:
        return _blocked_evaluation(version, f"Integritaetsfehler: {exc}")

    rows = []
    unpaired = []
    for match_id, forecast in sorted(forecasts.items()):
        closing, result = closings.get(match_id), results.get(match_id)
        if not closing or not result:
            unpaired.append({"match_id": match_id,
                             "reason": "missing_closing" if not closing else "missing_final_result"})
            continue
        # Revalidate chronology at evaluation time (including tamper-resistant manifest cutoff).
        kickoff = _utc(forecast["kickoff_utc"], "kickoff_utc")
        cutoff_minutes = manifest["components"]["cutoff"]["value"]["minutes_before_kickoff"]
        cutoff = kickoff - dt.timedelta(minutes=cutoff_minutes)
        if (_utc(forecast["generated_at_utc"], "generated_at_utc") >= cutoff or
                _utc(closing["captured_at_utc"], "captured_at_utc") >= cutoff):
            unpaired.append({"match_id": match_id, "reason": "late_capture"})
            continue
        candidate = _probabilities(forecast["candidate_probs"], "candidate_probs")
        raw = _probabilities(closing["raw_closing_probs"], "raw_closing_probs")
        alpha0 = _alpha0_probs(raw, manifest, forecast["competition"])
        outcome = result["outcome"]
        row = {
            "match_id": match_id, "competition": forecast["competition"],
            "cluster_day": kickoff.date().isoformat(), "outcome": outcome,
            "candidate": {"rps": rps(candidate, outcome),
                          "log_loss": log_loss(candidate, outcome)},
            "raw_closing": {"rps": rps(raw, outcome),
                            "log_loss": log_loss(raw, outcome)},
            "alpha0_calibrator": {"rps": rps(alpha0, outcome),
                                  "log_loss": log_loss(alpha0, outcome)},
        }
        for benchmark in ("raw_closing", "alpha0_calibrator"):
            row[f"delta_rps_vs_{benchmark}"] = row["candidate"]["rps"] - row[benchmark]["rps"]
            row[f"delta_log_loss_vs_{benchmark}"] = (row["candidate"]["log_loss"] -
                                                        row[benchmark]["log_loss"])
        rows.append(row)

    n_forecasts, n_paired = len(forecasts), len(rows)
    coverage = n_paired / n_forecasts if n_forecasts else 0.0
    days = {row["cluster_day"] for row in rows}
    leagues = {row["competition"] for row in rows}
    confidence = float(gates_cfg["confidence_level"])
    comparisons = {}
    benchmark_gates = []
    for benchmark in ("raw_closing", "alpha0_calibrator"):
        metric_block = {}
        for metric in ("rps", "log_loss"):
            field = f"delta_{metric}_vs_{benchmark}"
            values = [row[field] for row in rows]
            mean_delta = _mean(values)
            upper = _bootstrap_upper(rows, field, iterations=bootstrap_iterations,
                                     confidence_level=confidence,
                                     seed=bootstrap_seed + len(comparisons) * 10 + len(metric_block))
            passed = bool(mean_delta is not None and mean_delta < 0 and upper is not None and upper < 0)
            metric_block[metric] = {"mean_delta": mean_delta,
                                    "cluster_bootstrap_upper": upper, "passed": passed}
            benchmark_gates.append(passed)
        comparisons[benchmark] = metric_block

    gates = {
        "integrity": True,
        "coverage": coverage >= float(gates_cfg["minimum_coverage"]),
        "minimum_paired_n": n_paired >= int(gates_cfg["minimum_paired_n"]),
        "minimum_days": len(days) >= int(gates_cfg["minimum_days"]),
        "minimum_leagues": len(leagues) >= int(gates_cfg["minimum_leagues"]),
        "beats_raw_closing_rps": comparisons["raw_closing"]["rps"]["passed"],
        "beats_raw_closing_log_loss": comparisons["raw_closing"]["log_loss"]["passed"],
        "beats_alpha0_calibrator_rps": comparisons["alpha0_calibrator"]["rps"]["passed"],
        "beats_alpha0_calibrator_log_loss": comparisons["alpha0_calibrator"]["log_loss"]["passed"],
    }
    statistical_gates_pass = all(gates.values()) and all(benchmark_gates)
    # Sprint 1 never releases automatically, even if all statistical gates pass.
    gates["release"] = False
    return {
        "status": "diagnostic" if n_forecasts else "insufficient_data",
        "candidate_version": version, "manifest_sha256": manifest["manifest_sha256"],
        "integrity_ok": True, "n_forecasts": n_forecasts, "n_paired": n_paired,
        "coverage": coverage, "n_days": len(days), "n_leagues": len(leagues),
        "unpaired": unpaired, "rows": rows, "comparisons": comparisons,
        "bootstrap": {"method": "cluster_by_kickoff_day", "iterations": bootstrap_iterations,
                      "confidence_level": confidence, "seed": bootstrap_seed},
        "gates": gates, "statistical_gates_pass": statistical_gates_pass,
        "release_status": "blocked", "auto_apply": False,
        "prediction_allowed": False, "value_allowed": False, "stake_allowed": False,
        "note": "Prospektive Shadow-Auswertung; Freigabe bleibt unabhaengig von Metriken blockiert.",
    }

"""Automatischer Betriebsmodus-Wechsel nach dem letzten WM-Spiel.

Der Wechsel aktiviert den Vereinsfussball-Betriebsmodus erst nach offiziell
beendeter WM. Er uebernimmt keine Modell-, Gewichtungs- oder Stakingparameter
und laesst Prognose-/Value-Freigaben an den bestehenden Gates haengen.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from src import config
from src.data_sources import results_client
from src.pipeline import club_migration_readiness


MODE_PATH = config.DATA_PROCESSED / "operation_mode.json"


def _read_existing(path: Path = MODE_PATH) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _write(payload: dict, path: Path = MODE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _compact_readiness(readiness: dict) -> dict:
    return {"status": readiness.get("status"),
            "release_status": readiness.get("release_status"),
            "auto_apply": readiness.get("auto_apply"),
            "gates": readiness.get("gates")}


def check_and_switch(*, fixtures: dict | None = None,
                     now: dt.datetime | None = None,
                     mode_path: Path = MODE_PATH) -> dict:
    existing = _read_existing(mode_path)
    if existing and existing.get("mode") == "club_football":
        return {"status": "already_switched", "mode": "club_football",
                "operation_mode_path": str(mode_path), "switch": existing}

    fixtures = fixtures or results_client.fetch_fixtures(force=True)
    completion = results_client.world_cup_completion_status(fixtures)
    if not completion["complete"]:
        return {"status": "waiting_for_world_cup_finish", "mode": "world_cup",
                "world_cup": completion, "operation_mode_path": str(mode_path),
                "note": "Keine Umschaltung vor offiziell beendetem Finale."}

    timestamp = (now or dt.datetime.now(dt.timezone.utc)).isoformat(timespec="seconds")
    readiness = club_migration_readiness.run(
        config.MEMORY_DIR / "club_migration_readiness.md",
        world_cup_finished_confirmed=True,
        human_approved=True,
    )
    prediction_allowed = readiness.get("status") == "ready_for_manual_switch"
    payload = {
        "mode": "club_football",
        "previous_mode": "world_cup",
        "switched_at": timestamp,
        "trigger": "world_cup_final_finished",
        "world_cup": completion,
        "prediction_allowed": prediction_allowed,
        "value_allowed": False,
        "auto_apply": False,
        "readiness": _compact_readiness(readiness),
        "note": ("Vereinsfussball-Betriebsmodus automatisch aktiviert; "
                 "Value/Staking bleibt bis zu bestandenen Gates gesperrt."),
    }
    _write(payload, mode_path)
    return {"status": "switched", "mode": "club_football",
            "operation_mode_path": str(mode_path), "switch": payload}


def compact(result: dict) -> dict:
    switch = result.get("switch") or {}
    world_cup = result.get("world_cup") or switch.get("world_cup") or {}
    return {"status": result.get("status"), "mode": result.get("mode"),
            "world_cup_complete": world_cup.get("complete"),
            "n_finished": world_cup.get("n_finished"),
            "n_fixtures": world_cup.get("n_fixtures"),
            "prediction_allowed": switch.get("prediction_allowed"),
            "value_allowed": switch.get("value_allowed"),
            "operation_mode_path": result.get("operation_mode_path")}

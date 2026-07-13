"""Readiness-Gate fuer die spaetere Vereinsfussball-Umstellung.

Dieses Modul schaltet nichts um. Es verdichtet nur Shadow-Fixtures und
Backtest-Diagnosen zu einem blockierenden Report, damit der WM-Betrieb bis zur
menschlichen Freigabe unveraendert bleibt.
"""
from __future__ import annotations

import json
from pathlib import Path

from src import config
from src.model import club_backtest
from src.pipeline import club_shadow_run


def _all_fixtures_locked(shadow: dict) -> bool:
    for competition in shadow.get("competitions", {}).values():
        for fixture in competition.get("fixtures", []):
            if fixture.get("prediction_allowed") or fixture.get("value_allowed"):
                return False
    return True


def evaluate(shadow: dict, backtest: dict, *,
             world_cup_finished_confirmed: bool = False,
             human_approved: bool = False) -> dict:
    competitions = shadow.get("competitions", {})
    gates = {
        "shadow_all_sources_live": bool(shadow.get("n_competitions") and
                                        shadow.get("n_live_competitions") ==
                                        shadow.get("n_competitions")),
        "no_identity_pending": (shadow.get("n_identity_pending") == 0),
        "shadow_mode_only": (shadow.get("mode") == "shadow" and
                             shadow.get("auto_apply") is False and
                             all(row.get("mode") == "shadow" and
                                 row.get("auto_apply") is False
                                 for row in competitions.values())),
        "prediction_and_value_locked": _all_fixtures_locked(shadow),
        "backtest_all_competitions_diagnostic": bool(
            (backtest.get("gates") or {}).get("all_competitions_diagnostic")),
        "backtest_beats_naive": bool((backtest.get("gates") or {}).get("beats_naive_rps")),
        "backtest_logloss_guard": bool(
            (backtest.get("gates") or {}).get("logloss_guard_vs_naive")),
        "backtest_beats_market": bool((backtest.get("gates") or {}).get("beats_market_rps")),
        "world_cup_finished_confirmed": world_cup_finished_confirmed,
        "human_approved": human_approved,
    }
    ready = all(gates.values())
    return {
        "status": "ready_for_manual_switch" if ready else "blocked",
        "auto_apply": False,
        "release_status": "blocked" if not ready else "manual_only",
        "gates": gates,
        "shadow": {
            "status": shadow.get("status"),
            "n_competitions": shadow.get("n_competitions"),
            "n_live_competitions": shadow.get("n_live_competitions"),
            "n_fixtures": shadow.get("n_fixtures"),
            "n_identity_pending": shadow.get("n_identity_pending"),
        },
        "backtest": {
            "status": backtest.get("status"),
            "n_history": backtest.get("n_history"),
            "n_out_of_sample": backtest.get("n_out_of_sample"),
            "model": backtest.get("model"),
            "market_benchmark": backtest.get("market_benchmark"),
            "market_rps_gap": backtest.get("market_rps_gap"),
        },
        "note": "Keine automatische Umstellung; WM-Betrieb bleibt bis zur Freigabe aktiv.",
    }


def write_report(result: dict, path: Path) -> None:
    lines = ["# Vereinsfussball Readiness-Gate", "",
             f"Status: **{result['status']}**  ",
             f"Auto-Apply: `{result['auto_apply']}`  ",
             f"Release: `{result['release_status']}`  ",
             "", "## Shadow-Fixtures", ""]
    shadow = result.get("shadow") or {}
    lines += [
        f"- Status: `{shadow.get('status')}`",
        f"- Quellen live: `{shadow.get('n_live_competitions')}/{shadow.get('n_competitions')}`",
        f"- Fixtures: `{shadow.get('n_fixtures')}`",
        f"- Identity pending: `{shadow.get('n_identity_pending')}`",
        "", "## Backtest", "",
    ]
    backtest = result.get("backtest") or {}
    model = backtest.get("model") or {}
    market = backtest.get("market_benchmark") or {}
    lines += [
        f"- Status: `{backtest.get('status')}`",
        f"- Historie/OOS: `{backtest.get('n_history')}` / `{backtest.get('n_out_of_sample')}`",
        f"- Modell-RPS: `{model.get('mean_rps', 'n/a')}`",
        f"- Markt-RPS: `{market.get('mean_rps', 'n/a')}`",
        f"- RPS-Abstand Modell minus Markt: `{backtest.get('market_rps_gap')}`",
        "", "## Gates", "",
    ]
    lines.extend(f"- {key}: `{value}`" for key, value in result.get("gates", {}).items())
    lines += ["", "_Dieser Report ist ein Blocker/Pruefpunkt, kein Deployment-Schalter._", ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def run(report_path: Path | None = None,
        world_cup_finished_confirmed: bool = False,
        human_approved: bool = False) -> dict:
    shadow = club_shadow_run.run_all(days=60)
    backtest = club_backtest.run()
    result = evaluate(shadow, backtest,
                      world_cup_finished_confirmed=world_cup_finished_confirmed,
                      human_approved=human_approved)
    if report_path:
        write_report(result, report_path)
        result["report_path"] = str(report_path)
    return result


if __name__ == "__main__":
    output = config.MEMORY_DIR / "club_migration_readiness.md"
    report = run(output)
    print(f"Vereinsfussball-Readiness: {report['status']}, "
          f"Auto-Apply={report['auto_apply']}")

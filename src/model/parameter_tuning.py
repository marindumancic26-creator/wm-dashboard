"""Parameter-Tuning als Vorschlag, ohne Auto-Uebernahme in config.py.

Ziel: ELO_PER_GOAL auf der echten WM-2026-Slate gegen reale Ergebnisse pruefen.
rho bleibt primaer historisch geankert (StatsBomb WM 2018/22, backtest.py);
ein Live-rho-Grid wird nur als Sanity-Check berichtet.

Wichtig: Das Replay nutzt gespeicherte Snapshot-Inputs und laedt keine Live-Daten
nach. Nur der letzte Pre-Kickoff-Snapshot je Spiel wird verwendet.
"""
from __future__ import annotations

import datetime as dt
import json
import math
from pathlib import Path

from src import config
from src.model import backtest, calibration, features

OUTCOMES = ("team1_win", "draw", "team2_win")
ELO_GRID = (180.0, 200.0, 220.0, 240.0, 260.0, 280.0, 320.0)
RHO_SANITY_GRID = (0.0, -0.05, -0.10, -0.15, -0.20)
MIN_DIAGNOSTIC_N = 20
MIN_ADOPTION_N = 50
MIN_RPS_MARGIN = 0.01


def _parse_time(value: str | None):
    if not value:
        return None
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(dt.timezone.utc)
    except Exception:
        return None


def _is_pre_kickoff(entry: dict, fallback_cutoff: str | None = None) -> bool:
    t = _parse_time(entry.get("forecast_at"))
    kickoff = _parse_time(entry.get("kickoff_utc"))
    if kickoff and t:
        return t < kickoff
    cutoff = _parse_time(fallback_cutoff)
    if cutoff and t:
        return t <= cutoff
    return True


def _select_last_pre_kickoff(entries: list[dict], fallback_cutoff: str | None = None) -> dict | None:
    valid = [e for e in entries if _is_pre_kickoff(e, fallback_cutoff)]
    if not valid:
        return None
    return sorted(valid, key=lambda e: _parse_time(e.get("forecast_at")) or dt.datetime.min.replace(
        tzinfo=dt.timezone.utc))[-1]


def _score(probs: dict, outcome: str) -> dict:
    return {"rps": calibration.rps(probs, outcome),
            "log_loss": calibration.log_loss(probs, outcome),
            "brier": calibration.brier(probs, outcome),
            "hit": int(calibration.argmax_outcome(probs) == outcome)}


def _replay_probs(case: dict, elo_per_goal: float, rho: float) -> dict:
    return features.attack_defense_lambdas(
        case["team1"], case["team2"], {},
        elo_per_goal=elo_per_goal,
        rho=rho,
        baseline_total_goals=case["baseline_total_goals"],
        replay_model=case["model"],
    )["probs"]


def _score_cases(cases: list[dict], elo_per_goal: float, rho: float) -> dict:
    vals = [_score(_replay_probs(c, elo_per_goal, rho), c["outcome"]) for c in cases]
    if not vals:
        return {"n": 0, "mean_rps": None, "mean_log_loss": None, "mean_brier": None,
                "hit_rate": None}
    return {"n": len(vals),
            "mean_rps": round(sum(v["rps"] for v in vals) / len(vals), 4),
            "mean_log_loss": round(sum(v["log_loss"] for v in vals) / len(vals), 4),
            "mean_brier": round(sum(v["brier"] for v in vals) / len(vals), 4),
            "hit_rate": round(sum(v["hit"] for v in vals) / len(vals), 4)}


def _with_current(grid: tuple[float, ...]) -> tuple[float, ...]:
    return tuple(sorted({float(x) for x in grid} | {float(config.ELO_PER_GOAL)}))


def _in_sample_grid(cases: list[dict], elo_grid: tuple[float, ...], rho: float) -> list[dict]:
    cur = _score_cases(cases, config.ELO_PER_GOAL, rho)
    rows = []
    for elo in _with_current(elo_grid):
        s = _score_cases(cases, elo, rho)
        s.update({"elo_per_goal": elo,
                  "margin_rps_vs_current": (
                      round(cur["mean_rps"] - s["mean_rps"], 4)
                      if cur["mean_rps"] is not None and s["mean_rps"] is not None else None)})
        rows.append(s)
    return rows


def _walk_forward_folds(n: int) -> list[tuple[int, int, int]]:
    if n < MIN_DIAGNOSTIC_N:
        return []
    initial = max(10, n // 2)
    remaining = n - initial
    if remaining <= 0:
        return []
    n_folds = min(5, max(2, remaining // 5))
    fold_size = max(1, math.ceil(remaining / n_folds))
    folds = []
    start = initial
    while start < n:
        end = min(n, start + fold_size)
        folds.append((start, start, end))
        start = end
    return folds


def _walk_forward_grid(cases: list[dict], elo_grid: tuple[float, ...], rho: float) -> list[dict]:
    folds = _walk_forward_folds(len(cases))
    if not folds:
        return []
    cur_rows = []
    for train_n, start, end in folds:
        s = _score_cases(cases[start:end], config.ELO_PER_GOAL, rho)
        cur_rows.append({"train_n": train_n, "valid_n": end - start, **s})

    rows = []
    for elo in _with_current(elo_grid):
        fold_rows = []
        for train_n, start, end in folds:
            s = _score_cases(cases[start:end], elo, rho)
            cur = next(r for r in cur_rows if r["train_n"] == train_n and r["valid_n"] == end - start)
            margin = cur["mean_rps"] - s["mean_rps"]
            fold_rows.append({"train_n": train_n, "valid_n": end - start,
                              "mean_rps": s["mean_rps"],
                              "mean_log_loss": s["mean_log_loss"],
                              "margin_rps_vs_current": round(margin, 4)})
        total_n = sum(f["valid_n"] for f in fold_rows)
        rows.append({"elo_per_goal": elo, "n": total_n,
                     "mean_rps": round(sum(f["mean_rps"] * f["valid_n"] for f in fold_rows) / total_n, 4),
                     "mean_log_loss": round(sum(f["mean_log_loss"] * f["valid_n"] for f in fold_rows) / total_n, 4),
                     "margin_rps_vs_current": round(
                         sum(f["margin_rps_vs_current"] * f["valid_n"] for f in fold_rows) / total_n, 4),
                     "folds": fold_rows})
    return rows


def _rho_sanity(cases: list[dict]) -> list[dict]:
    rows = []
    for rho in RHO_SANITY_GRID:
        s = _score_cases(cases, config.ELO_PER_GOAL, rho)
        s["rho"] = rho
        rows.append(s)
    return rows


def _historical_rho_anchor() -> dict:
    try:
        res = backtest.run()
        if res.get("status") == "ok":
            return {"rho": res["best_rho"], "source": "backtest.py StatsBomb WM 2018/22",
                    "status": "ok", "n_matches": res.get("n_matches")}
        return {"rho": config.DIXON_COLES_RHO, "source": "config fallback",
                "status": "fallback", "note": res.get("note")}
    except Exception as exc:
        return {"rho": config.DIXON_COLES_RHO, "source": "config fallback",
                "status": "fallback", "note": str(exc)}


def load_cases(dashboard_path: Path | None = None,
               snapshot_dir: Path | None = None) -> tuple[list[dict], dict]:
    dashboard_path = dashboard_path or (config.DATA_PROCESSED / "dashboard_data.json")
    snapshot_dir = snapshot_dir or config.DATA_SNAPSHOTS
    data = json.loads(dashboard_path.read_text(encoding="utf-8"))
    resolved = {r["slug"]: r for r in data.get("calibration", {}).get("matches", [])
                if r.get("outcome")}
    by_slug: dict[str, list] = {s: [] for s in resolved}
    audit = {"snapshots": 0, "resolved": len(resolved), "entries": 0,
             "missing_model_inputs": 0, "missing_baseline_total_goals": 0}

    for fp in sorted(snapshot_dir.glob("*.json")):
        try:
            snap = json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            continue
        audit["snapshots"] += 1
        snap_cfg = snap.get("config", {})
        if "baseline_total_goals" not in snap_cfg:
            audit["missing_baseline_total_goals"] += 1
        for m in snap.get("matches", []):
            slug = m.get("slug")
            if slug not in by_slug:
                continue
            model = m.get("model") or {}
            if not (model.get("elo") and model.get("strength")):
                audit["missing_model_inputs"] += 1
                continue
            forecast_at = (m.get("market") or {}).get("fetched_at") or snap.get("generated_at") or fp.stem
            by_slug[slug].append({
                "slug": slug, "team1": m.get("team1"), "team2": m.get("team2"),
                "forecast_at": forecast_at,
                "kickoff_utc": (m.get("match_info") or {}).get("kickoff_utc"),
                "snapshot_file": fp.name,
                "model": model,
                "baseline_total_goals": snap_cfg.get("baseline_total_goals",
                                                     config.BASELINE_TOTAL_GOALS),
                "snapshot_elo_per_goal": snap_cfg.get("elo_per_goal"),
            })
            audit["entries"] += 1

    cases = []
    for slug, row in resolved.items():
        selected = _select_last_pre_kickoff(by_slug.get(slug, []), row.get("forecast_at"))
        if not selected:
            continue
        selected = dict(selected)
        selected["outcome"] = row["outcome"]
        selected["result"] = row.get("result")
        selected["calibration_forecast_at"] = row.get("forecast_at")
        selected["model_version"] = row.get("model_version")
        cases.append(selected)
    cases.sort(key=lambda c: _parse_time(c.get("forecast_at")) or dt.datetime.min.replace(
        tzinfo=dt.timezone.utc))
    audit["cases"] = len(cases)
    return cases, audit


def suggest_parameter_tuning(cases: list[dict] | None = None,
                             rho_anchor: float | None = None,
                             run_historical_backtest: bool = True) -> dict:
    audit = {}
    if cases is None:
        cases, audit = load_cases()
    else:
        cases = sorted(cases, key=lambda c: _parse_time(c.get("forecast_at")) or dt.datetime.min.replace(
            tzinfo=dt.timezone.utc))
        audit = {"cases": len(cases), "source": "provided"}

    n = len(cases)
    current = {"elo_per_goal": config.ELO_PER_GOAL, "rho": config.DIXON_COLES_RHO,
               "baseline_total_goals": config.BASELINE_TOTAL_GOALS}
    anchor = ({"rho": float(rho_anchor), "source": "provided", "status": "ok"}
              if rho_anchor is not None else
              (_historical_rho_anchor() if run_historical_backtest else
               {"rho": config.DIXON_COLES_RHO, "source": "config", "status": "skipped"}))
    if n < MIN_DIAGNOSTIC_N:
        return {"status": "prior", "n": n, "min_n": MIN_DIAGNOSTIC_N,
                "adoption_min_n": MIN_ADOPTION_N, "current": current,
                "rho_anchor": anchor, "best_candidate": None, "grid": {}, "input_audit": audit,
                "note": f"n={n} < {MIN_DIAGNOSTIC_N}: kein Live-Tuning, nur aktuelle Config berichten."}

    rho = float(anchor["rho"])

    walk = _walk_forward_grid(cases, ELO_GRID, rho)
    ins = _in_sample_grid(cases, ELO_GRID, rho)
    rho_grid = _rho_sanity(cases)
    best = min(walk, key=lambda r: (r["mean_rps"], r["mean_log_loss"])) if walk else None
    cur = next((r for r in walk if abs(r["elo_per_goal"] - config.ELO_PER_GOAL) < 1e-9), None)
    if best and cur:
        stable = all(f["margin_rps_vs_current"] > 0 for f in best["folds"])
        margin = best["margin_rps_vs_current"]
        logloss_ok = best["mean_log_loss"] <= cur["mean_log_loss"] + 0.02
        adoption_ready = n >= MIN_ADOPTION_N and margin >= MIN_RPS_MARGIN and stable and logloss_ok
        best_candidate = {"elo_per_goal": best["elo_per_goal"], "rho": rho,
                          "walk_forward_rps": best["mean_rps"],
                          "walk_forward_log_loss": best["mean_log_loss"],
                          "margin_rps_vs_current": margin,
                          "stable_across_folds": stable,
                          "log_loss_guard_ok": logloss_ok,
                          "adoption_ready": adoption_ready}
    else:
        best_candidate = None
        adoption_ready = False

    status = "proposal" if adoption_ready else "diagnostic"
    return {"status": status, "n": n, "min_n": MIN_DIAGNOSTIC_N,
            "adoption_min_n": MIN_ADOPTION_N, "current": current,
            "rho_anchor": anchor, "best_candidate": best_candidate,
            "grid": {"walk_forward": walk, "in_sample": ins, "rho_sanity": rho_grid},
            "input_audit": audit,
            "note": ("Vorschlag, keine Auto-Uebernahme. Headline ist Walk-forward-RPS; "
                     "In-sample und Live-rho-Grid sind nur Diagnose.")}


def _fmt(x):
    return "-" if x is None else str(x)


def write_report(result: dict, report_path: Path | None = None) -> Path:
    report_path = report_path or (config.MEMORY_DIR / "parameter_tuning_report.md")
    lines = ["# Parameter-Tuning-Report", "",
             "Status: **" + result["status"] + "**",
             f"n={result['n']} | Diagnose ab n>={result['min_n']} | Uebernahme erst ab n>={result['adoption_min_n']}",
             "",
             "## Aktuelle Config", "",
             f"- ELO_PER_GOAL: `{result['current']['elo_per_goal']}`",
             f"- DIXON_COLES_RHO: `{result['current']['rho']}`",
             f"- BASELINE_TOTAL_GOALS: `{result['current']['baseline_total_goals']}`",
             "",
             "## rho-Anker", ""]
    anchor = result.get("rho_anchor") or {}
    lines.append(f"- rho: `{anchor.get('rho', result['current']['rho'])}` ({anchor.get('source', 'n/a')}, {anchor.get('status', 'n/a')})")
    if anchor.get("note"):
        lines.append(f"- Hinweis: {anchor['note']}")

    lines += ["", "## Headline: Walk-forward ELO_PER_GOAL", "",
              "| ELO_PER_GOAL | RPS | LogLoss | Marge RPS vs. aktuell | n |",
              "|---:|---:|---:|---:|---:|"]
    for r in result.get("grid", {}).get("walk_forward", []):
        lines.append(f"| {r['elo_per_goal']:.0f} | {r['mean_rps']} | {r['mean_log_loss']} | "
                     f"{r['margin_rps_vs_current']} | {r['n']} |")

    lines += ["", "## Diagnose: In-sample Score-Flaeche", "",
              "| ELO_PER_GOAL | RPS | LogLoss | Brier | Hit | Marge RPS vs. aktuell | n |",
              "|---:|---:|---:|---:|---:|---:|---:|"]
    for r in result.get("grid", {}).get("in_sample", []):
        lines.append(f"| {r['elo_per_goal']:.0f} | {r['mean_rps']} | {r['mean_log_loss']} | "
                     f"{r['mean_brier']} | {r['hit_rate']} | {r['margin_rps_vs_current']} | {r['n']} |")

    lines += ["", "## Sanity: Live-rho-Grid (kein Treiber der Empfehlung)", "",
              "| rho | RPS | LogLoss | Brier | Hit | n |",
              "|---:|---:|---:|---:|---:|---:|"]
    for r in result.get("grid", {}).get("rho_sanity", []):
        lines.append(f"| {r['rho']} | {r['mean_rps']} | {r['mean_log_loss']} | "
                     f"{r['mean_brier']} | {r['hit_rate']} | {r['n']} |")

    lines += ["", "## Kandidat", ""]
    cand = result.get("best_candidate")
    if cand:
        lines += [f"- ELO_PER_GOAL: `{cand['elo_per_goal']}`",
                  f"- rho: `{cand['rho']}`",
                  f"- Walk-forward RPS: `{cand['walk_forward_rps']}`",
                  f"- Marge gegen aktuelle Config: `{cand['margin_rps_vs_current']}`",
                  f"- stabil ueber Folds: `{cand['stable_across_folds']}`",
                  f"- LogLoss-Guard OK: `{cand['log_loss_guard_ok']}`",
                  f"- Uebernahme-reif: `{cand['adoption_ready']}`"]
    else:
        lines.append("- Kein Kandidat: zu wenig Daten oder keine Walk-forward-Folds.")

    audit = result.get("input_audit", {})
    lines += ["", "## Input-Audit", ""]
    for k, v in audit.items():
        lines.append(f"- {k}: `{v}`")
    lines += ["", "_Keine automatische Aenderung an config.py. Parameter-Aenderungen bleiben Menschenentscheidung._", ""]
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def run() -> dict:
    result = suggest_parameter_tuning()
    path = write_report(result)
    result["report_path"] = str(path)
    return result


if __name__ == "__main__":
    res = run()
    print(f"status={res['status']} n={res['n']} report={res['report_path']}")

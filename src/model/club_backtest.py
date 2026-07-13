"""Walk-forward-Validierung der Vereinsmodell-Struktur auf echten Resultaten.

Das Training waechst saisonweise und sieht niemals die Testsaison. RPS ist die
Headline, LogLoss ein Guard. Marktquoten sind nur Benchmark und kein Target.
Dieser Report aendert weder Konfiguration noch Prognose-/Value-Freigaben.
"""
from __future__ import annotations

import statistics
from pathlib import Path

from src import config
from src.data_sources import football_data_uk_history as history
from src.model import backtest, calibration


MIN_TRAIN_MATCHES = 100


def _outcome(match: dict) -> str:
    if match["home_score"] > match["away_score"]:
        return "team1_win"
    if match["home_score"] < match["away_score"]:
        return "team2_win"
    return "draw"


def _score(rows: list[tuple[dict, str]]) -> dict | None:
    if not rows:
        return None
    rps_values = [calibration.rps(probs, outcome) for probs, outcome in rows]
    log_values = [calibration.log_loss(probs, outcome) for probs, outcome in rows]
    hits = [int(max(probs, key=probs.get) == outcome) for probs, outcome in rows]
    return {"mean_rps": round(statistics.mean(rps_values), 4),
            "mean_log_loss": round(statistics.mean(log_values), 4),
            "hit_rate": round(statistics.mean(hits), 4), "n": len(rows)}


def _naive_probs(train: list[dict]) -> dict:
    counts = {"team1_win": 0, "draw": 0, "team2_win": 0}
    for match in train:
        counts[_outcome(match)] += 1
    total = sum(counts.values())
    return {key: value / total for key, value in counts.items()}


def walk_forward_eval(matches: list[dict], rho: float = config.DIXON_COLES_RHO) -> dict:
    seasons = sorted({match["season_start"] for match in matches})
    folds, all_model, all_naive, all_market = [], [], [], []
    for test_season in seasons[1:]:
        train = [match for match in matches if match["season_start"] < test_season]
        test = [match for match in matches if match["season_start"] == test_season]
        if len(train) < MIN_TRAIN_MATCHES or not test:
            continue
        fit = backtest.fit_attack_defense(train)
        naive_probs = _naive_probs(train)
        model_rows, naive_rows, market_rows = [], [], []
        for match in test:
            raw = backtest._predict(fit, match["home_team"], match["away_team"], rho)
            model_probs = {"team1_win": raw[0], "draw": raw[1], "team2_win": raw[2]}
            outcome = _outcome(match)
            model_rows.append((model_probs, outcome))
            naive_rows.append((naive_probs, outcome))
            if match.get("market_probs"):
                market_rows.append((match["market_probs"], outcome))
        fold = {"test_season": test_season, "train_n": len(train), "test_n": len(test),
                "model": _score(model_rows), "naive": _score(naive_rows),
                "market_benchmark": _score(market_rows)}
        fold["model_beats_naive_rps"] = (
            fold["model"]["mean_rps"] < fold["naive"]["mean_rps"])
        folds.append(fold)
        all_model.extend(model_rows)
        all_naive.extend(naive_rows)
        all_market.extend(market_rows)

    model_score, naive_score, market_score = (_score(all_model), _score(all_naive),
                                               _score(all_market))
    gates = {
        "minimum_history": len(matches) >= MIN_TRAIN_MATCHES,
        "beats_naive_rps": bool(model_score and naive_score and
                                model_score["mean_rps"] < naive_score["mean_rps"]),
        "logloss_guard_vs_naive": bool(model_score and naive_score and
                                       model_score["mean_log_loss"] <=
                                       naive_score["mean_log_loss"]),
        "fold_stability": bool(folds and all(fold["model_beats_naive_rps"] for fold in folds)),
        "market_benchmark_available": bool(market_score),
        "beats_market_rps": bool(model_score and market_score and
                                 model_score["mean_rps"] <= market_score["mean_rps"]),
    }
    market_gap = (round(model_score["mean_rps"] - market_score["mean_rps"], 4)
                  if model_score and market_score else None)
    return {"status": "diagnostic" if folds else "insufficient_data",
            "n_history": len(matches), "n_out_of_sample": len(all_model),
            "rho_fixed": rho, "folds": folds, "model": model_score,
            "naive": naive_score, "market_benchmark": market_score, "gates": gates,
            "market_rps_gap": market_gap,
            "release_status": "blocked", "auto_apply": False,
            "note": "Keine Freigabe und keine Parameteruebernahme; menschliche Entscheidung erforderlich."}


def write_report(result: dict, path: Path) -> None:
    lines = ["# Vereinsmodell Walk-forward-Report", "",
             f"Status: **{result['status']}**  ",
             f"Historie: {result['n_history']} Spiele; Out-of-sample: {result['n_out_of_sample']}  ",
             f"rho fixiert auf aktuelle Config: `{result['rho_fixed']}`  ",
             "Freigabe: **BLOCKIERT** (Report-only, keine Auto-Uebernahme)", "",
             "| Testsaison | Train n | Test n | Modell RPS | Naiv RPS | Markt RPS | Modell besser? |",
             "|---:|---:|---:|---:|---:|---:|---|"]
    for fold in result.get("folds", []):
        market = fold.get("market_benchmark") or {}
        lines.append(f"| {fold['test_season']} | {fold['train_n']} | {fold['test_n']} | "
                     f"{fold['model']['mean_rps']} | {fold['naive']['mean_rps']} | "
                     f"{market.get('mean_rps', 'n/a')} | {fold['model_beats_naive_rps']} |")
    lines += ["", "## Gesamt (Out-of-sample)", ""]
    for label, key in (("Modell", "model"), ("Naive Basisrate", "naive"),
                       ("Markt-Benchmark", "market_benchmark")):
        score = result.get(key)
        if score:
            lines.append(f"- {label}: RPS `{score['mean_rps']}`, LogLoss "
                         f"`{score['mean_log_loss']}`, Treffer `{score['hit_rate']}` (n={score['n']})")
    lines.append(f"- RPS-Abstand Modell minus Markt: `{result.get('market_rps_gap')}`")
    lines += ["", "## Gates", ""]
    lines.extend(f"- {key}: `{value}`" for key, value in result.get("gates", {}).items())
    lines += ["", "_Marktpreise wurden nicht trainiert oder optimiert; sie dienen nur als Diagnose._", ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def run(report_path: Path | None = None, force_download: bool = False) -> dict:
    loaded = history.fetch_history(force=force_download)
    result = walk_forward_eval(loaded.get("matches", []))
    result["data_source"] = {key: loaded.get(key) for key in
                             ("status", "source", "seasons", "errors", "note")}
    if report_path:
        write_report(result, report_path)
        result["report_path"] = str(report_path)
    return result


if __name__ == "__main__":
    output = config.MEMORY_DIR / "club_backtest_report.md"
    report = run(output)
    print(f"Vereinsmodell: {report['status']}, OOS n={report['n_out_of_sample']}, "
          f"Freigabe={report['release_status']}")

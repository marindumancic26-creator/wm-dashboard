"""Walk-forward-Validierung der Vereinsmodell-Struktur auf echten Resultaten.

Das Training waechst saisonweise und sieht niemals die Testsaison. RPS ist die
Headline, LogLoss ein Guard. Marktquoten sind nur Benchmark und kein Target.
Dieser Report aendert weder Konfiguration noch Prognose-/Value-Freigaben.
"""
from __future__ import annotations

import datetime as dt
import math
import random
import statistics
from collections import defaultdict
from pathlib import Path

from src import config
from src.data_sources import football_data_uk_history as history
from src.model import backtest, calibration, features


MIN_TRAIN_MATCHES = 100
DEFAULT_COMPETITIONS = tuple(history.COMPETITION_DIVISIONS)
DECAYED_RHO_GRID = (0.0, -0.05, -0.10, -0.15)
DECAYED_HALF_LIFE_GRID = (180, 365, 730)
OUTCOMES = ("team1_win", "draw", "team2_win")
MARKET_RESIDUAL_ALPHA_GRID = (0.0, 0.025, 0.05, 0.075, 0.10)
MARKET_TEMPERATURE_GRID = (0.90, 0.95, 1.0, 1.05, 1.10)
MARKET_DRAW_MULTIPLIER_GRID = (0.90, 0.95, 1.0, 1.05, 1.10)


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


def _score_raw(rows: list[tuple[dict, str]]) -> dict | None:
    if not rows:
        return None
    rps_values = [calibration.rps(probs, outcome) for probs, outcome in rows]
    log_values = [calibration.log_loss(probs, outcome) for probs, outcome in rows]
    hits = [int(max(probs, key=probs.get) == outcome) for probs, outcome in rows]
    return {"mean_rps": statistics.mean(rps_values),
            "mean_log_loss": statistics.mean(log_values),
            "hit_rate": statistics.mean(hits), "n": len(rows)}


def _round_score(score: dict | None) -> dict | None:
    if not score:
        return None
    return {"mean_rps": round(score["mean_rps"], 4),
            "mean_log_loss": round(score["mean_log_loss"], 4),
            "hit_rate": round(score["hit_rate"], 4), "n": score["n"]}


def _naive_probs(train: list[dict]) -> dict:
    counts = {"team1_win": 0, "draw": 0, "team2_win": 0}
    for match in train:
        counts[_outcome(match)] += 1
    total = sum(counts.values())
    if total <= 0:
        return {key: 1 / 3 for key in counts}
    return {key: value / total for key, value in counts.items()}


def _sort_key(match: dict) -> tuple:
    return (match.get("date") or "", match.get("block_key") or match.get("date") or "",
            match.get("home_team") or "", match.get("away_team") or "")


def _blocks(matches: list[dict]) -> list[tuple[str, list[dict]]]:
    grouped = defaultdict(list)
    for match in sorted(matches, key=_sort_key):
        grouped[match.get("block_key") or match.get("date") or "unknown"].append(match)
    return [(key, grouped[key]) for key in sorted(grouped)]


def _safe_date(value: str | None):
    try:
        return dt.date.fromisoformat((value or "")[:10])
    except ValueError:
        return None


def _decayed_fit(train: list[dict], as_of: str | None, half_life_days: int) -> dict:
    """Zeitgewichtetes Poisson-Modell fuer den Diagnose-Kandidaten.

    Das ist bewusst ein Report-Modell: keine Config-Aenderung, kein Markt-Target.
    """
    known_dates = [_safe_date(m.get("date")) for m in train if _safe_date(m.get("date"))]
    as_date = _safe_date(as_of) or (max(known_dates) if known_dates else None)
    teams = sorted({m["home_team"] for m in train} | {m["away_team"] for m in train})
    if not train or not teams:
        return {"attack": {}, "defense": {}, "home": 1.0, "base": 1.30}
    weights = []
    for match in train:
        match_date = _safe_date(match.get("date"))
        age = max((as_date - match_date).days, 0) if as_date and match_date else 0
        weights.append(0.5 ** (age / max(half_life_days, 1)))
    total_w = sum(weights) or 1.0
    total_goals = sum(w * (m["home_score"] + m["away_score"])
                      for w, m in zip(weights, train))
    base = max(total_goals / (2 * total_w), 0.35)
    home_goals = sum(w * m["home_score"] for w, m in zip(weights, train))
    away_goals = sum(w * m["away_score"] for w, m in zip(weights, train))
    home = max(min((home_goals / max(away_goals, 1e-6)), 1.65), 0.75)

    scored = defaultdict(float)
    conceded = defaultdict(float)
    weight_seen = defaultdict(float)
    for w, match in zip(weights, train):
        h, a = match["home_team"], match["away_team"]
        scored[h] += w * match["home_score"]
        scored[a] += w * match["away_score"]
        conceded[h] += w * match["away_score"]
        conceded[a] += w * match["home_score"]
        weight_seen[h] += w
        weight_seen[a] += w

    attack, defense = {}, {}
    for team in teams:
        seen = weight_seen[team]
        shrink = seen / (seen + 8.0)
        atk_raw = scored[team] / max(base * seen, 1e-6)
        def_raw = conceded[team] / max(base * seen, 1e-6)
        attack[team] = max(0.35, min(2.4, shrink * atk_raw + (1 - shrink)))
        defense[team] = max(0.35, min(2.4, shrink * def_raw + (1 - shrink)))
    mean_attack = statistics.mean(attack.values()) if attack else 1.0
    mean_defense = statistics.mean(defense.values()) if defense else 1.0
    attack = {team: value / mean_attack for team, value in attack.items()}
    defense = {team: value / mean_defense for team, value in defense.items()}
    return {"attack": attack, "defense": defense, "home": home, "base": base}


def _predict_from_fit(fit: dict, home: str, away: str, rho: float) -> tuple[dict, float, float]:
    lam_h = fit["base"] * fit["attack"].get(home, 1.0) * fit["defense"].get(away, 1.0) * fit["home"]
    lam_a = fit["base"] * fit["attack"].get(away, 1.0) * fit["defense"].get(home, 1.0)
    raw = features.poisson_1x2(lam_h, lam_a, rho=rho)
    return {"team1_win": raw[0], "draw": raw[1], "team2_win": raw[2]}, lam_h, lam_a


def _prequential_rows(train_start: list[dict], test: list[dict], *,
                      rho: float, half_life_days: int) -> list[dict]:
    revealed = list(sorted(train_start, key=_sort_key))
    season_teams = {m["home_team"] for m in train_start} | {m["away_team"] for m in train_start}
    rows, block_index = [], 0
    for block_key, block in _blocks(test):
        block_index += 1
        fit = _decayed_fit(revealed, block[0].get("date"), half_life_days)
        naive = _naive_probs(revealed)
        for match in block:
            probs, lam_h, lam_a = _predict_from_fit(
                fit, match["home_team"], match["away_team"], rho)
            outcome = _outcome(match)
            rows.append({"match": match, "probs": probs, "naive_probs": naive,
                         "outcome": outcome, "block_key": block_key,
                         "block_index": block_index,
                         "market_probs": match.get("market_probs"),
                         "promoted_match": match["home_team"] not in season_teams or
                         match["away_team"] not in season_teams,
                         "expected_goals": lam_h + lam_a,
                         "strength_diff": abs(lam_h - lam_a),
                         "favorite_prob": max(probs.values()),
                         "is_draw": outcome == "draw"})
        revealed.extend(block)
    return rows


def _score_prediction_rows(rows: list[dict], key: str = "probs",
                           market_only: bool = False) -> dict | None:
    filtered = [row for row in rows if (not market_only or row.get("market_probs"))]
    return _round_score(_score_raw([(row[key], row["outcome"]) for row in filtered]))


def _market_score(rows: list[dict]) -> dict | None:
    return _round_score(_score_raw([(row["market_probs"], row["outcome"])
                                    for row in rows if row.get("market_probs")]))


def _adjust_market(market: dict, temperature: float,
                   draw_multiplier: float) -> dict:
    power = 1.0 / max(temperature, 1e-6)
    adjusted = {key: max(market[key], 1e-12) ** power for key in OUTCOMES}
    adjusted["draw"] *= draw_multiplier
    total = sum(adjusted.values())
    return {key: adjusted[key] / total for key in OUTCOMES}


def _blend_market_residual(market: dict, model: dict, alpha: float,
                           temperature: float = 1.0,
                           draw_multiplier: float = 1.0) -> dict:
    """Kleine Modellkorrektur des Closing-Konsenses; alpha=0 ist der Markt."""
    adjusted_market = _adjust_market(market, temperature, draw_multiplier)
    blended = {key: (1.0 - alpha) * adjusted_market[key] + alpha * model[key]
               for key in OUTCOMES}
    total = sum(blended.values())
    return {key: blended[key] / total for key in OUTCOMES}


def _market_residual_candidate(rows: list[dict]) -> dict:
    """Waehlt die Residualstaerke nur auf bereits abgeschlossenen Saisons."""
    paired = [row for row in rows if row.get("market_probs")]
    seasons = sorted({row["match"].get("season_start") for row in paired})
    transformed, selections = [], []
    for season in seasons:
        prior = [row for row in paired
                 if row["match"].get("season_start") < season]
        current = [row for row in paired
                   if row["match"].get("season_start") == season]
        best = (0.0, 1.0, 1.0)
        if prior:
            candidates = []
            for alpha in MARKET_RESIDUAL_ALPHA_GRID:
                for temperature in MARKET_TEMPERATURE_GRID:
                    for draw_multiplier in MARKET_DRAW_MULTIPLIER_GRID:
                        scored = _score_raw([
                            (_blend_market_residual(
                                row["market_probs"], row["probs"], alpha,
                                temperature, draw_multiplier), row["outcome"])
                            for row in prior
                        ])
                        candidates.append((
                            scored["mean_rps"] + 0.25 * scored["mean_log_loss"],
                            scored["mean_rps"], scored["mean_log_loss"],
                            alpha, temperature, draw_multiplier))
            chosen = min(candidates)
            best = (chosen[3], chosen[4], chosen[5])
        best_alpha, temperature, draw_multiplier = best
        selections.append({"season_start": season, "train_n": len(prior),
                           "alpha": best_alpha, "temperature": temperature,
                           "draw_multiplier": draw_multiplier})
        for row in current:
            transformed.append({
                **row,
                "base_model_probs": row["probs"],
                "probs": _blend_market_residual(
                    row["market_probs"], row["probs"], best_alpha,
                    temperature, draw_multiplier),
                "market_residual_alpha": best_alpha,
            })
    coverage = _coverage([row["match"] for row in transformed])
    gates = _gate(transformed, coverage)
    return {
        "candidate": "closing_residual_blend",
        "status": "diagnostic" if transformed else "insufficient_data",
        "n_out_of_sample": len(transformed),
        "model": _score_prediction_rows(transformed, market_only=True),
        "market_benchmark": _market_score(transformed),
        "gates": gates,
        "diagnostics": _diagnostics(transformed),
        "market_rps_gap": gates.get("delta_rps"),
        "selections": selections,
        "release_status": "blocked", "auto_apply": False,
        "note": "Closing-Markt plus nur auf frueheren Saisons gewaehlte Modellkorrektur.",
        "_rows": transformed,
    }


def _coverage(matches: list[dict]) -> dict:
    total = len(matches)
    covered = sum(1 for match in matches if match.get("market_probs"))
    return {"n": total, "covered": covered,
            "rate": round(covered / total, 4) if total else 0.0,
            "gate": bool(total and covered / total >= 0.98)}


def _bootstrap_upper(rows: list[dict], metric: str, n_boot: int = 300,
                     seed: int = 7) -> float | None:
    paired = [row for row in rows if row.get("market_probs")]
    if not paired:
        return None
    by_block = defaultdict(list)
    for row in paired:
        match = row["match"]
        key = (match.get("competition"), match.get("season_start"), row.get("block_key"))
        by_block[key].append(row)
    blocks = list(by_block.values())
    if not blocks:
        return None
    rng = random.Random(seed)
    values = []
    for _ in range(n_boot):
        sampled = []
        for _ in blocks:
            sampled.extend(rng.choice(blocks))
        if metric == "rps":
            vals = [calibration.rps(row["probs"], row["outcome"]) -
                    calibration.rps(row["market_probs"], row["outcome"])
                    for row in sampled]
        else:
            vals = [calibration.log_loss(row["probs"], row["outcome"]) -
                    calibration.log_loss(row["market_probs"], row["outcome"])
                    for row in sampled]
        values.append(statistics.mean(vals))
    values.sort()
    return round(values[min(int(0.95 * len(values)), len(values) - 1)], 4)


def _league_wins(rows: list[dict]) -> dict:
    by_league = defaultdict(list)
    for row in rows:
        if row.get("market_probs"):
            by_league[row["match"].get("competition")].append(row)
    wins, table = 0, {}
    for league, league_rows in by_league.items():
        model = _score_prediction_rows(league_rows, market_only=True)
        market = _market_score(league_rows)
        ok = bool(model and market and model["mean_rps"] < market["mean_rps"] and
                  model["mean_log_loss"] < market["mean_log_loss"])
        wins += int(ok)
        table[league] = {"wins_both": ok, "model": model, "market": market}
    return {"wins_both": wins, "required": 4, "leagues": table}


def _gate(rows: list[dict], coverage: dict) -> dict:
    model = _score_prediction_rows(rows, market_only=True)
    market = _market_score(rows)
    delta_rps = (round(model["mean_rps"] - market["mean_rps"], 4)
                 if model and market else None)
    delta_logloss = (round(model["mean_log_loss"] - market["mean_log_loss"], 4)
                     if model and market else None)
    ci_rps = _bootstrap_upper(rows, "rps")
    ci_logloss = _bootstrap_upper(rows, "log_loss")
    league = _league_wins(rows)
    return {
        "closing_coverage": coverage,
        "aggregate_delta_rps_lt_0": bool(delta_rps is not None and delta_rps < 0),
        "aggregate_delta_logloss_lt_0": bool(delta_logloss is not None and delta_logloss < 0),
        "bootstrap_upper95_delta_rps_lt_0": bool(ci_rps is not None and ci_rps < 0),
        "bootstrap_upper95_delta_logloss_lt_0": bool(ci_logloss is not None and ci_logloss < 0),
        "league_wins_both": league["wins_both"],
        "league_wins_required": league["required"],
        "league_wins_gate": league["wins_both"] >= league["required"],
        "closing_coverage_gate": coverage["gate"],
        "closing_market_outperformance": bool(
            delta_rps is not None and delta_logloss is not None and delta_rps < 0 and
            delta_logloss < 0 and ci_rps is not None and ci_rps < 0 and
            ci_logloss is not None and ci_logloss < 0 and
            league["wins_both"] >= league["required"] and coverage["gate"]),
        "delta_rps": delta_rps,
        "delta_logloss": delta_logloss,
        "upper95_delta_rps": ci_rps,
        "upper95_delta_logloss": ci_logloss,
        "league_breakdown": league["leagues"],
    }


def _diagnostics(rows: list[dict]) -> dict:
    paired = [row for row in rows if row.get("market_probs")]
    if not paired:
        return {}
    sorted_strength = sorted(row["strength_diff"] for row in paired)

    def decile(value: float) -> int:
        if not sorted_strength:
            return 1
        rank = sum(1 for x in sorted_strength if x <= value)
        return min(10, max(1, math.ceil(rank / len(sorted_strength) * 10)))

    groups = {
        "aufsteiger": lambda r: "ja" if r["promoted_match"] else "nein",
        "erste_sechs_spieltage": lambda r: "ja" if r["block_index"] <= 6 else "nein",
        "remis": lambda r: "ja" if r["is_draw"] else "nein",
        "staerke_diff_decile": lambda r: str(decile(r["strength_diff"])),
        "favoritenwahrscheinlichkeit": lambda r: (
            "hoch" if r["favorite_prob"] >= 0.6 else
            ("mittel" if r["favorite_prob"] >= 0.45 else "flach")),
        "erwartete_tore": lambda r: (
            "hoch" if r["expected_goals"] >= 3.0 else
            ("mittel" if r["expected_goals"] >= 2.2 else "niedrig")),
        "liga": lambda r: r["match"].get("competition") or "unknown",
        "saison": lambda r: str(r["match"].get("season_start")),
    }
    out = {}
    for name, key_fn in groups.items():
        buckets = defaultdict(list)
        for row in paired:
            buckets[key_fn(row)].append(row)
        out[name] = {}
        for key, bucket_rows in sorted(buckets.items()):
            model = _score_prediction_rows(bucket_rows, market_only=True)
            market = _market_score(bucket_rows)
            out[name][key] = {
                "n": len(bucket_rows),
                "delta_rps": round(model["mean_rps"] - market["mean_rps"], 4),
                "delta_logloss": round(model["mean_log_loss"] - market["mean_log_loss"], 4),
            }
    return out


def _select_decayed_params(train: list[dict]) -> dict:
    seasons = sorted({m["season_start"] for m in train})
    if len(seasons) < 2:
        return {"rho": config.DIXON_COLES_RHO, "half_life_days": 365,
                "grid": [], "note": "Zu wenig Historie fuer inneres Rolling-Fold."}
    val_season = seasons[-1]
    inner_train = [m for m in train if m["season_start"] < val_season]
    validation = [m for m in train if m["season_start"] == val_season]
    grid = []
    for rho in DECAYED_RHO_GRID:
        for half_life in DECAYED_HALF_LIFE_GRID:
            fit = _decayed_fit(inner_train, validation[0].get("date") if validation else None,
                               half_life)
            rows = []
            for match in validation:
                probs, lam_h, lam_a = _predict_from_fit(
                    fit, match["home_team"], match["away_team"], rho)
                rows.append({"match": match, "probs": probs,
                             "outcome": _outcome(match),
                             "market_probs": match.get("market_probs"),
                             "block_key": match.get("block_key") or match.get("date"),
                             "expected_goals": lam_h + lam_a,
                             "strength_diff": abs(lam_h - lam_a),
                             "favorite_prob": max(probs.values())})
            score = _score_prediction_rows(rows, market_only=True) or _score_prediction_rows(rows)
            grid.append({"rho": rho, "half_life_days": half_life,
                         "mean_rps": score["mean_rps"] if score else None,
                         "mean_log_loss": score["mean_log_loss"] if score else None,
                         "n": score["n"] if score else 0})
    valid = [row for row in grid if row["mean_rps"] is not None]
    best = min(valid, key=lambda row: (row["mean_rps"], row["mean_log_loss"])) if valid else None
    return {"rho": best["rho"] if best else config.DIXON_COLES_RHO,
            "half_life_days": best["half_life_days"] if best else 365,
            "grid": grid, "validation_season": val_season}


def prequential_candidate_eval(matches: list[dict],
                               candidate: str = "decayed_dixon_coles",
                               include_rows: bool = False) -> dict:
    seasons = sorted({match["season_start"] for match in matches})
    folds, all_rows = [], []
    for test_season in seasons[1:]:
        train = [match for match in matches if match["season_start"] < test_season]
        test = [match for match in matches if match["season_start"] == test_season]
        if len(train) < MIN_TRAIN_MATCHES or not test:
            continue
        params = _select_decayed_params(train)
        rows = _prequential_rows(train, test, rho=params["rho"],
                                 half_life_days=params["half_life_days"])
        folds.append({"test_season": test_season, "train_n": len(train),
                      "test_n": len(test), "params": params,
                      "model": _score_prediction_rows(rows, market_only=True),
                      "market_benchmark": _market_score(rows),
                      "naive": _score_prediction_rows(rows, "naive_probs")})
        all_rows.extend(rows)
    coverage = _coverage([row["match"] for row in all_rows])
    gates = _gate(all_rows, coverage)
    model = _score_prediction_rows(all_rows, market_only=True)
    market = _market_score(all_rows)
    result = {"candidate": candidate,
              "status": "diagnostic" if folds else "insufficient_data",
              "n_out_of_sample": len(all_rows), "folds": folds,
              "model": model, "naive": _score_prediction_rows(all_rows, "naive_probs"),
              "market_benchmark": market, "gates": gates,
              "diagnostics": _diagnostics(all_rows),
              "market_rps_gap": gates.get("delta_rps"),
              "release_status": "blocked", "auto_apply": False,
              "note": "Prequential: vor Block prognostizieren, danach Ergebnis offenlegen."}
    if include_rows:
        result["_rows"] = all_rows
    return result


def _aggregate_prequential(results: list[dict],
                           candidate: str = "decayed_dixon_coles") -> dict:
    rows = [row for result in results for row in result.get("_rows", [])]
    coverage = _coverage([row["match"] for row in rows])
    gates = _gate(rows, coverage)
    return {"candidate": candidate,
            "status": "diagnostic" if rows else "insufficient_data",
            "n_out_of_sample": len(rows),
            "model": _score_prediction_rows(rows, market_only=True),
            "naive": _score_prediction_rows(rows, "naive_probs"),
            "market_benchmark": _market_score(rows),
            "gates": gates, "diagnostics": _diagnostics(rows),
            "market_rps_gap": gates.get("delta_rps"),
            "release_status": "blocked", "auto_apply": False,
            "note": "Global aggregierter prequentialer Kandidat; Markt nur Benchmark."}


def walk_forward_eval(matches: list[dict], rho: float = config.DIXON_COLES_RHO) -> dict:
    seasons = sorted({match["season_start"] for match in matches})
    folds, all_model, all_naive, all_market, all_model_market = [], [], [], [], []
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
                all_model_market.append((model_probs, outcome))
        fold = {"test_season": test_season, "train_n": len(train), "test_n": len(test),
                "model": _score(model_rows), "naive": _score(naive_rows),
                "market_benchmark": _score(market_rows),
                "model_on_market_games": _score([
                    (model_rows[i][0], model_rows[i][1])
                    for i, match in enumerate(test) if match.get("market_probs")
                ])}
        fold["model_beats_naive_rps"] = (
            fold["model"]["mean_rps"] < fold["naive"]["mean_rps"])
        folds.append(fold)
        all_model.extend(model_rows)
        all_naive.extend(naive_rows)
        all_market.extend(market_rows)

    model_score, naive_score, market_score = (_score(all_model), _score(all_naive),
                                               _score(all_market))
    model_market_score = _score(all_model_market)
    gates = {
        "minimum_history": len(matches) >= MIN_TRAIN_MATCHES,
        "beats_naive_rps": bool(model_score and naive_score and
                                model_score["mean_rps"] < naive_score["mean_rps"]),
        "logloss_guard_vs_naive": bool(model_score and naive_score and
                                       model_score["mean_log_loss"] <=
                                       naive_score["mean_log_loss"]),
        "fold_stability": bool(folds and all(fold["model_beats_naive_rps"] for fold in folds)),
        "market_benchmark_available": bool(market_score),
        "beats_market_rps": bool(model_market_score and market_score and
                                 model_market_score["mean_rps"] <= market_score["mean_rps"]),
    }
    market_gap = (round(model_market_score["mean_rps"] - market_score["mean_rps"], 4)
                  if model_market_score and market_score else None)
    return {"status": "diagnostic" if folds else "insufficient_data",
            "n_history": len(matches), "n_out_of_sample": len(all_model),
            "rho_fixed": rho, "folds": folds, "model": model_score,
            "model_on_market_games": model_market_score,
            "naive": naive_score, "market_benchmark": market_score, "gates": gates,
            "market_rps_gap": market_gap,
            "release_status": "blocked", "auto_apply": False,
            "note": "Keine Freigabe und keine Parameteruebernahme; menschliche Entscheidung erforderlich."}


def _weighted_summary(results: list[dict], key: str) -> dict | None:
    rows = [result.get(key) for result in results if result.get(key)]
    total_n = sum(row["n"] for row in rows)
    if total_n <= 0:
        return None
    return {"mean_rps": round(sum(row["mean_rps"] * row["n"] for row in rows) / total_n, 4),
            "mean_log_loss": round(sum(row["mean_log_loss"] * row["n"] for row in rows) / total_n, 4),
            "hit_rate": round(sum(row["hit_rate"] * row["n"] for row in rows) / total_n, 4),
            "n": total_n}


def walk_forward_by_competition(histories: dict,
                                rho: float = config.DIXON_COLES_RHO) -> dict:
    competition_results, decayed_results, residual_results = {}, [], []
    for key, loaded in histories.get("competitions", {}).items():
        result = walk_forward_eval(loaded.get("matches", []), rho)
        decayed = prequential_candidate_eval(loaded.get("matches", []), include_rows=True)
        residual = _market_residual_candidate(decayed.get("_rows", []))
        decayed_public = {k: v for k, v in decayed.items() if k != "_rows"}
        residual_public = {k: v for k, v in residual.items() if k != "_rows"}
        result["candidates"] = {
            "current_maher_poisson": {
                "candidate": "current_maher_poisson",
                "status": result.get("status"),
                "model": result.get("model_on_market_games") or result.get("model"),
                "naive": result.get("naive"),
                "market_benchmark": result.get("market_benchmark"),
                "market_rps_gap": result.get("market_rps_gap"),
                "release_status": "blocked",
                "auto_apply": False,
            },
            "decayed_dixon_coles": decayed_public,
            "closing_residual_blend": residual_public,
        }
        result["competition"] = key
        result["data_source"] = {field: loaded.get(field) for field in
                                 ("status", "source", "seasons", "errors", "note")}
        competition_results[key] = result
        decayed_results.append(decayed)
        residual_results.append(residual)

    diagnostics = [result for result in competition_results.values()
                   if result.get("status") == "diagnostic"]
    decayed_summary = _aggregate_prequential(decayed_results)
    residual_summary = _aggregate_prequential(
        residual_results, candidate="closing_residual_blend")
    primary_summary = residual_summary
    model_score = primary_summary.get("model") or _weighted_summary(diagnostics, "model")
    naive_score = decayed_summary.get("naive") or _weighted_summary(diagnostics, "naive")
    market_score = primary_summary.get("market_benchmark") or _weighted_summary(diagnostics, "market_benchmark")
    market_gap = (round(model_score["mean_rps"] - market_score["mean_rps"], 4)
                  if model_score and market_score else None)
    full_gate = (primary_summary.get("gates") or {}).get("closing_market_outperformance")
    gates = {
        "minimum_history": bool(diagnostics),
        "beats_naive_rps": bool(model_score and naive_score and
                                model_score["mean_rps"] < naive_score["mean_rps"]),
        "logloss_guard_vs_naive": bool(model_score and naive_score and
                                       model_score["mean_log_loss"] <=
                                       naive_score["mean_log_loss"]),
        "all_competitions_diagnostic": len(diagnostics) == len(competition_results),
        "market_benchmark_available": bool(market_score),
        "beats_market_rps": bool(model_score and market_score and
                                 model_score["mean_rps"] <= market_score["mean_rps"]),
        "closing_market_outperformance": bool(full_gate),
    }
    gates.update({f"closing_gate_{key}": value for key, value
                  in (primary_summary.get("gates") or {}).items()
                  if key != "league_breakdown"})
    return {"status": "diagnostic" if diagnostics else "insufficient_data",
            "n_history": sum(result.get("n_history", 0)
                             for result in competition_results.values()),
            "n_out_of_sample": sum(result.get("n_out_of_sample", 0)
                                   for result in competition_results.values()),
            "rho_fixed": rho, "competitions": competition_results,
            "primary_candidate": "closing_residual_blend",
            "candidates": {"decayed_dixon_coles": decayed_summary,
                           "closing_residual_blend": residual_summary},
            "diagnostics": primary_summary.get("diagnostics"),
            "model": model_score, "naive": naive_score,
            "market_benchmark": market_score, "gates": gates,
            "market_rps_gap": market_gap,
            "release_status": "blocked", "auto_apply": False,
            "note": "Wettbewerbe werden getrennt validiert; keine Auto-Freigabe."}


def write_report(result: dict, path: Path) -> None:
    lines = ["# Vereinsmodell Walk-forward-Report", "",
             f"Status: **{result['status']}**  ",
             f"Historie: {result['n_history']} Spiele; Out-of-sample: {result['n_out_of_sample']}  ",
             f"rho fixiert auf aktuelle Config: `{result['rho_fixed']}`  ",
             f"Primaerer Kandidat: `{result.get('primary_candidate', 'current_maher_poisson')}`",
             "Freigabe: **BLOCKIERT** (Report-only, keine Auto-Uebernahme)"]
    if result.get("competitions"):
        lines += ["", "## Wettbewerbe", ""]
        for key, comp in result["competitions"].items():
            primary = (comp.get("candidates") or {}).get(
                result.get("primary_candidate"), comp)
            model = primary.get("model") or {}
            market = primary.get("market_benchmark") or {}
            lines.append(f"- `{key}`: Status `{comp['status']}`, Historie "
                         f"`{comp['n_history']}`, OOS `{comp['n_out_of_sample']}`, "
                         f"Modell-RPS `{model.get('mean_rps', 'n/a')}`, "
                         f"Markt-RPS `{market.get('mean_rps', 'n/a')}`")
        lines += ["", "## Tor-Modell-Folds je Wettbewerb"]
    else:
        lines += ["", "## Folds"]
    lines += ["", "| Testsaison | Train n | Test n | Modell RPS | Naiv RPS | Markt RPS | Modell besser? |",
              "|---:|---:|---:|---:|---:|---:|---|"]

    fold_rows = result.get("folds", [])
    if result.get("competitions"):
        fold_rows = []
        for key, comp in result["competitions"].items():
            primary = (comp.get("candidates") or {}).get(
                result.get("primary_candidate", "current_maher_poisson"), comp)
            for fold in primary.get("folds", comp.get("folds", [])):
                fold_rows.append({**fold, "competition": key})
    for fold in fold_rows:
        market = fold.get("market_benchmark") or {}
        model_beats_naive = fold.get("model_beats_naive_rps")
        if model_beats_naive is None and fold.get("model") and fold.get("naive"):
            model_beats_naive = fold["model"]["mean_rps"] < fold["naive"]["mean_rps"]
        season_label = (f"{fold.get('competition')} {fold['test_season']}"
                        if fold.get("competition") else fold["test_season"])
        lines.append(f"| {season_label} | {fold['train_n']} | {fold['test_n']} | "
                     f"{fold['model']['mean_rps']} | {fold['naive']['mean_rps']} | "
                     f"{market.get('mean_rps', 'n/a')} | {model_beats_naive} |")
    if result.get("primary_candidate") == "closing_residual_blend":
        lines += ["", "## Residual-Auswahl je Testsaison", "",
                  "| Liga | Saison | Training n | Modellanteil | Markt-Temperatur | Remis-Faktor |",
                  "|---|---:|---:|---:|---:|---:|"]
        for key, comp in result.get("competitions", {}).items():
            residual = (comp.get("candidates") or {}).get("closing_residual_blend", {})
            for selection in residual.get("selections", []):
                lines.append(
                    f"| {key} | {selection['season_start']} | {selection['train_n']} | "
                    f"{selection['alpha']:.3f} | {selection['temperature']:.2f} | "
                    f"{selection['draw_multiplier']:.2f} |")
    lines += ["", "## Gesamt (Out-of-sample)", ""]
    for label, key in (("Modell", "model"), ("Naive Basisrate", "naive"),
                       ("Markt-Benchmark", "market_benchmark")):
        score = result.get(key)
        if score:
            lines.append(f"- {label}: RPS `{score['mean_rps']}`, LogLoss "
                         f"`{score['mean_log_loss']}`, Treffer `{score['hit_rate']}` (n={score['n']})")
    lines.append(f"- RPS-Abstand Modell minus Markt: `{result.get('market_rps_gap')}`")
    if result.get("candidates"):
        lines += ["", "## Kandidaten", ""]
        for name, cand in result["candidates"].items():
            score = cand.get("model") or {}
            market = cand.get("market_benchmark") or {}
            gates = cand.get("gates") or {}
            lines.append(f"- `{name}`: Status `{cand.get('status')}`, "
                         f"Modell-RPS `{score.get('mean_rps', 'n/a')}`, "
                         f"Markt-RPS `{market.get('mean_rps', 'n/a')}`, "
                         f"Delta-RPS `{cand.get('market_rps_gap')}`, "
                         f"Closing-Gate `{gates.get('closing_market_outperformance', False)}`")
    lines += ["", "## Gates", ""]
    lines.extend(f"- {key}: `{value}`" for key, value in result.get("gates", {}).items())
    if result.get("diagnostics"):
        lines += ["", "## Pflichtdiagnosen", ""]
        for name, buckets in result["diagnostics"].items():
            lines.append(f"### {name}")
            for bucket, values in buckets.items():
                lines.append(f"- `{bucket}`: n `{values['n']}`, "
                             f"Delta RPS `{values['delta_rps']}`, "
                             f"Delta LogLoss `{values['delta_logloss']}`")
    lines += ["", "_Das Tor-Modell nutzt Marktpreise nie als Trainingsziel. Der explizit "
              "benannte Closing-Residualkandidat verwendet den Closing-Konsens als Eingabe; "
              "seine Korrekturparameter werden ausschliesslich auf frueheren Saisons gewaehlt._", ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def run(report_path: Path | None = None, force_download: bool = False) -> dict:
    loaded = history.fetch_histories(DEFAULT_COMPETITIONS, force=force_download)
    result = walk_forward_by_competition(loaded)
    result["data_source"] = {key: loaded.get(key) for key in
                             ("status", "source", "note")}
    if report_path:
        write_report(result, report_path)
        result["report_path"] = str(report_path)
    return result


if __name__ == "__main__":
    output = config.MEMORY_DIR / "club_backtest_report.md"
    report = run(output)
    print(f"Vereinsmodell: {report['status']}, OOS n={report['n_out_of_sample']}, "
          f"Freigabe={report['release_status']}")

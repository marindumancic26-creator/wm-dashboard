"""Monte-Carlo-Simulation der Spielausgaenge.

Tore beider Teams werden als Poisson-Prozesse simuliert. Parameterunsicherheit:
die lambda-Werte werden pro Lauf aus einer Gamma-Verteilung um den Punktschaetzer
gezogen (CV = MC_PARAM_UNCERTAINTY). Daraus entstehen Unsicherheitsbaender
(5%/95%-Quantile der Ergebnis-Wahrscheinlichkeiten ueber Parameter-Resamples).

Dixon-Coles-Korrektur (rho): statt aus der korrigierten Verteilung neu zu ziehen,
werden die unabhaengigen Poisson-Ziehungen per Importance-Weighting regewichtet
(Gewicht = tau(i,j)). Alle Kennzahlen sind daher gewichtete Mittel. Das ist exakt
(E_DC[f] = E_indep[f*tau]/E_indep[tau]) und bleibt vollstaendig vektorisiert.
"""
from __future__ import annotations

import numpy as np

from src import config


def simulate(lam1: float, lam2: float, runs: int = None, seed: int = 42,
             rho: float | None = None) -> dict:
    runs = runs or config.MC_RUNS
    if rho is None:
        rho = config.DIXON_COLES_RHO
    rng = np.random.default_rng(seed)
    cv = config.MC_PARAM_UNCERTAINTY

    # Gamma-Sampling der Erwartungswerte (shape k = 1/cv^2 -> CV = cv)
    k = 1.0 / cv ** 2
    lam1_s = rng.gamma(k, lam1 / k, runs)
    lam2_s = rng.gamma(k, lam2 / k, runs)
    g1 = rng.poisson(lam1_s)
    g2 = rng.poisson(lam2_s)

    # Dixon-Coles-Importance-Gewichte (nur 4 Niedrigergebnis-Zellen != 1)
    w = np.ones(runs)
    if rho != 0.0:
        m00 = (g1 == 0) & (g2 == 0)
        m01 = (g1 == 0) & (g2 == 1)
        m10 = (g1 == 1) & (g2 == 0)
        m11 = (g1 == 1) & (g2 == 1)
        w[m00] = 1.0 - lam1_s[m00] * lam2_s[m00] * rho
        w[m01] = 1.0 + lam1_s[m01] * rho
        w[m10] = 1.0 + lam2_s[m10] * rho
        w[m11] = 1.0 - rho
        w = np.clip(w, 1e-9, None)
    W = w.sum()

    def wmean(mask) -> float:
        return float((w * mask).sum() / W)

    total = g1 + g2
    p1 = wmean(g1 > g2)
    pd = wmean(g1 == g2)
    p2 = wmean(g1 < g2)

    mg = config.MAX_GOALS
    g1c = np.clip(g1, 0, mg)
    g2c = np.clip(g2, 0, mg)

    # Scoreline-Matrix (gewichtet)
    matrix = np.zeros((mg + 1, mg + 1))
    np.add.at(matrix, (g1c, g2c), w)
    matrix /= W

    # Top-Scorelines
    flat = [((i, j), matrix[i, j]) for i in range(mg + 1) for j in range(mg + 1) if matrix[i, j] > 0]
    flat.sort(key=lambda x: -x[1])
    top_scores = [{"score": f"{i}:{j}", "prob": round(float(p), 4)} for (i, j), p in flat[:10]]

    # Torverteilungen (gewichtet)
    def dist(arr, upto):
        return [round(wmean(arr == i), 4) for i in range(upto)] + [round(wmean(arr >= upto), 4)]

    goals_team1 = dist(g1, 6)   # 0..5, 6+
    goals_team2 = dist(g2, 6)
    total_dist = dist(total, 9)  # 0..8, 9+

    # Over/Under-Linien (gewichtet)
    ou = {}
    for line in (0.5, 1.5, 2.5, 3.5, 4.5):
        ou[str(line)] = {"over": round(wmean(total > line), 4),
                         "under": round(wmean(total < line), 4)}

    # Ereignis-Wahrscheinlichkeiten (gewichtet)
    events = {
        "btts": round(wmean((g1 > 0) & (g2 > 0)), 4),
        "clean_sheet_team1": round(wmean(g2 == 0), 4),
        "clean_sheet_team2": round(wmean(g1 == 0), 4),
        "team1_scores_2plus": round(wmean(g1 >= 2), 4),
        "team2_scores_2plus": round(wmean(g2 >= 2), 4),
        "win_margin_2plus": round(wmean(np.abs(g1.astype(int) - g2.astype(int)) >= 2), 4),
    }

    # Unsicherheitsbaender: gewichtete 1X2 ueber 200 Parameter-Resample-Bloecke
    bands = {}
    nb = 200
    chunk = max(1, runs // nb)
    idx = np.arange(runs)[: nb * chunk].reshape(nb, chunk)
    wb = w[idx]
    den = wb.sum(axis=1)
    for name, cond in (("team1_win", g1 > g2), ("draw", g1 == g2), ("team2_win", g1 < g2)):
        per = (wb * cond[idx]).sum(axis=1) / den
        bands[name] = {"p05": round(float(np.quantile(per, 0.05)), 4),
                       "p95": round(float(np.quantile(per, 0.95)), 4)}

    return {
        "runs": runs,
        "lambda1": lam1, "lambda2": lam2, "dixon_coles_rho": rho,
        "probs": {"team1_win": round(p1, 4), "draw": round(pd, 4), "team2_win": round(p2, 4)},
        "uncertainty": bands,
        "score_matrix": [[round(float(x), 4) for x in row] for row in matrix],
        "top_scorelines": top_scores,
        "goals_team1_dist": goals_team1,
        "goals_team2_dist": goals_team2,
        "total_goals_dist": total_dist,
        "expected_goals": {"team1": round(float((w * g1).sum() / W), 3),
                           "team2": round(float((w * g2).sum() / W), 3),
                           "total": round(float((w * total).sum() / W), 3)},
        "over_under": ou,
        "events": events,
    }

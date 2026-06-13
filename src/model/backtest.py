"""Backtest-Harness: validiert Modellstruktur & Parameter auf echten WM-Daten.

Datengrundlage: StatsBomb-WM-Ergebnisse 2018+2022 (öffentlich). Wir fitten ein
Dixon-Coles-Angriffs-/Abwehr-Modell (atk_i, def_i, Heimvorteil) per MLE-Fixpunkt
(Maher-Verfahren, kein scipy nötig) und evaluieren OUT-OF-SAMPLE per k-fold-CV.

Zweck:
  1. Beweisen, dass die getrennte Angriff/Abwehr-Struktur echte Vorhersagekraft hat
     (besser als naive Basisraten).
  2. Dixon-Coles datenbasiert validieren/tunen: rho-Grid -> bestes Out-of-sample-LogLoss.

WICHTIG: Kein historisches Elo verfügbar -> ELO_PER_GOAL wird hier NICHT getunt
(nur die Funktionsform + rho). Das ist sauber dokumentiert, keine Scheinpräzision.
"""
from __future__ import annotations

import math
import statistics

from src.data_sources import statsbomb_client as sb
from src.model import features

OUTCOMES = ("team1_win", "draw", "team2_win")
RHO_GRID = [0.0, -0.05, -0.10, -0.15, -0.20]


def _outcome(hg, ag):
    return "team1_win" if hg > ag else ("team2_win" if ag > hg else "draw")


def fit_attack_defense(matches: list[dict], iters: int = 80) -> dict:
    """MLE-Fixpunkt für atk/def/home auf Poisson-Basis. matches: home_team/away_team/scores."""
    teams = sorted({m["home_team"] for m in matches} | {m["away_team"] for m in matches})
    atk = {t: 1.0 for t in teams}
    dfn = {t: 1.0 for t in teams}
    n = len(matches)
    base = sum(m["home_score"] + m["away_score"] for m in matches) / (2 * n) if n else 1.3
    home = 1.25

    for _ in range(iters):
        # Angriff
        for t in teams:
            scored = sum(m["home_score"] for m in matches if m["home_team"] == t) + \
                     sum(m["away_score"] for m in matches if m["away_team"] == t)
            exp = sum(base * dfn[m["away_team"]] * home for m in matches if m["home_team"] == t) + \
                  sum(base * dfn[m["home_team"]] for m in matches if m["away_team"] == t)
            if exp > 1e-9:
                atk[t] = scored / exp
        mean_a = statistics.mean(atk.values())
        atk = {t: v / mean_a for t, v in atk.items()}
        # Abwehr
        for t in teams:
            conceded = sum(m["away_score"] for m in matches if m["home_team"] == t) + \
                       sum(m["home_score"] for m in matches if m["away_team"] == t)
            exp = sum(base * atk[m["away_team"]] for m in matches if m["home_team"] == t) + \
                  sum(base * atk[m["home_team"]] * home for m in matches if m["away_team"] == t)
            if exp > 1e-9:
                dfn[t] = conceded / exp
        mean_d = statistics.mean(dfn.values())
        dfn = {t: v / mean_d for t, v in dfn.items()}
        # Heimvorteil
        hg = sum(m["home_score"] for m in matches)
        exp_h = sum(base * atk[m["home_team"]] * dfn[m["away_team"]] for m in matches)
        if exp_h > 1e-9:
            home = hg / exp_h

    return {"attack": atk, "defense": dfn, "home": home, "base": base}


def _predict(fit, h, a, rho):
    atk, dfn, home, base = fit["attack"], fit["defense"], fit["home"], fit["base"]
    lam_h = base * atk.get(h, 1.0) * dfn.get(a, 1.0) * home
    lam_a = base * atk.get(a, 1.0) * dfn.get(h, 1.0)
    return features.poisson_1x2(lam_h, lam_a, rho=rho)


def _brier(p, outcome):
    return sum((p[o] - (1.0 if OUTCOMES[i] == outcome else 0.0)) ** 2
               for i, o in enumerate(("team1_win", "draw", "team2_win")))


def _logloss(p, outcome):
    idx = {"team1_win": 0, "draw": 1, "team2_win": 2}[outcome]
    return -math.log(max(p[idx] if isinstance(p, tuple) else p[outcome], 1e-9))


def kfold_eval(matches: list[dict], rho: float, k: int = 5, seed: int = 1) -> dict:
    import random
    rng = random.Random(seed)
    idx = list(range(len(matches)))
    rng.shuffle(idx)
    folds = [idx[i::k] for i in range(k)]
    briers, lls, hits = [], [], []
    for fold in folds:
        test_i = set(fold)
        train = [matches[i] for i in range(len(matches)) if i not in test_i]
        test = [matches[i] for i in fold]
        fit = fit_attack_defense(train)
        for m in test:
            p = _predict(fit, m["home_team"], m["away_team"], rho)
            pd = {"team1_win": p[0], "draw": p[1], "team2_win": p[2]}
            o = _outcome(m["home_score"], m["away_score"])
            briers.append(_brier(pd, o))
            lls.append(-math.log(max(pd[o], 1e-9)))
            hits.append(int(max(pd, key=pd.get) == o))
    return {"rho": rho, "brier": round(statistics.mean(briers), 4),
            "log_loss": round(statistics.mean(lls), 4),
            "hit_rate": round(statistics.mean(hits), 4), "n": len(briers)}


def baseline(matches: list[dict]) -> dict:
    """Naive Basisraten (empirische Heim/Remis/Auswärts-Häufigkeit)."""
    n = len(matches)
    h = sum(1 for m in matches if m["home_score"] > m["away_score"]) / n
    d = sum(1 for m in matches if m["home_score"] == m["away_score"]) / n
    a = 1 - h - d
    p = {"team1_win": h, "draw": d, "team2_win": a}
    briers, lls = [], []
    for m in matches:
        o = _outcome(m["home_score"], m["away_score"])
        briers.append(_brier(p, o))
        lls.append(-math.log(max(p[o], 1e-9)))
    return {"name": "Basisraten", "probs": {k: round(v, 3) for k, v in p.items()},
            "brier": round(statistics.mean(briers), 4), "log_loss": round(statistics.mean(lls), 4)}


def run(report_path=None) -> dict:
    matches = sb._fetch_wc_matches()
    if not matches:
        return {"status": "unavailable", "note": "Keine StatsBomb-WM-Daten geladen."}

    base = baseline(matches)
    grid = [kfold_eval(matches, rho) for rho in RHO_GRID]
    best = min(grid, key=lambda r: r["log_loss"])

    out = {"status": "ok", "n_matches": len(matches), "baseline": base,
           "rho_grid": grid, "best_rho": best["rho"],
           "beats_baseline": best["log_loss"] < base["log_loss"]}

    if report_path:
        lines = [f"# Backtest-Report — Angriff/Abwehr-Engine + Dixon-Coles", "",
                 f"Datengrundlage: {len(matches)} WM-Spiele (StatsBomb 2018+2022), "
                 f"5-fold-Kreuzvalidierung (out-of-sample).", "",
                 f"**Baseline (Basisraten):** Brier {base['brier']}, LogLoss {base['log_loss']}", "",
                 "| rho | Brier | LogLoss | Hit-Rate | n |", "|---|---|---|---|---|"]
        for r in grid:
            mark = " ⭐" if r["rho"] == best["rho"] else ""
            lines.append(f"| {r['rho']} | {r['brier']} | {r['log_loss']} | "
                         f"{r['hit_rate']*100:.0f}% | {r['n']} |{mark}")
        lines += ["",
                  f"**Bestes rho (Out-of-sample): {best['rho']}** "
                  f"(LogLoss {best['log_loss']}).",
                  f"Engine schlägt Basisraten: {'JA' if out['beats_baseline'] else 'NEIN'} "
                  f"(LogLoss {best['log_loss']} vs. {base['log_loss']}).", "",
                  "_Hinweis: ELO_PER_GOAL wird hier NICHT getunt (kein historisches Elo). "
                  "Validiert sind die getrennte Angriff/Abwehr-Struktur und der rho-Wert._", ""]
        report_path.write_text("\n".join(lines), encoding="utf-8")

    return out


if __name__ == "__main__":
    from src import config
    res = run(report_path=config.MEMORY_DIR / "backtest_report.md")
    print(f"Spiele: {res.get('n_matches')}")
    print(f"Baseline LogLoss: {res['baseline']['log_loss']}")
    for r in res["rho_grid"]:
        print(f"  rho={r['rho']:>5}: Brier {r['brier']} LogLoss {r['log_loss']} Hit {r['hit_rate']}")
    print(f"Bestes rho: {res['best_rho']} | schlägt Baseline: {res['beats_baseline']}")

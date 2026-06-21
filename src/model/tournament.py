"""Turnier-Simulation (Gruppenphase) — Vorwärts-Monte-Carlo mit dem Modell.

Aus den football-data.org-Fixtures (Gruppen, beendete Ergebnisse, Restspiele) wird
die Gruppenphase n-fach simuliert: jedes Restspiel über Poisson-Tore aus den
Modell-λ. Daraus pro Team: P(Gruppensieg), P(Top 2), P(Weiterkommen via Top 2 oder
beste 8 Dritte — WM-2026-Format, 48 Teams → 32er-K.o.).

Die K.o.-Titel-/Tiefenlauf-Odds kommen NICHT von hier (die exakte FIFA-Bracket-
Zuordnung der besten Dritten ist nicht in den Fixtures), sondern aus dem Markt
(Polymarket „World Cup Winner") — die ehrlichste Quelle für Außenseiter-Titelchancen.
Tie-Break vereinfacht: Punkte → Tordifferenz → erzielte Tore (kein direkter Vergleich).
"""
from __future__ import annotations

import numpy as np

from src.model import bracket_wc2026 as bk

ADVANCE_THIRDS = 8   # beste 8 Gruppendritte kommen weiter (WM 2026, 48 Teams)


def build_groups(fixtures: dict) -> dict:
    """{group: {"teams": [...], "matches": [{home,away,status,hg,ag}]}} aus Fixtures."""
    groups: dict[str, dict] = {}
    for f in fixtures.get("fixtures", []):
        g = f.get("group")
        if not g or f.get("stage") != "GROUP_STAGE":
            continue
        gd = groups.setdefault(g, {"teams": set(), "matches": []})
        if f["home"]:
            gd["teams"].add(f["home"])
        if f["away"]:
            gd["teams"].add(f["away"])
        gd["matches"].append({"home": f["home"], "away": f["away"],
                              "status": f.get("status"),
                              "hg": f.get("home_goals"), "ag": f.get("away_goals")})
    for g in groups:
        groups[g]["teams"] = sorted(groups[g]["teams"])
    return groups


def _base_table(group: dict) -> dict:
    """Aktuelle Tabelle (Punkte/Tordiff/Tore) aus beendeten Spielen."""
    tbl = {t: {"pts": 0, "gd": 0, "gf": 0, "pld": 0} for t in group["teams"]}
    for m in group["matches"]:
        if m["status"] != "FINISHED" or m["hg"] is None:
            continue
        h, a, hg, ag = m["home"], m["away"], m["hg"], m["ag"]
        if h not in tbl or a not in tbl:
            continue
        tbl[h]["gf"] += hg; tbl[h]["gd"] += hg - ag; tbl[h]["pld"] += 1
        tbl[a]["gf"] += ag; tbl[a]["gd"] += ag - hg; tbl[a]["pld"] += 1
        if hg > ag:
            tbl[h]["pts"] += 3
        elif ag > hg:
            tbl[a]["pts"] += 3
        else:
            tbl[h]["pts"] += 1; tbl[a]["pts"] += 1
    return tbl


def current_standings(groups: dict) -> dict:
    """Sortierte Ist-Tabellen je Gruppe (für die „aktuelle" Ansicht)."""
    out = {}
    for g, grp in groups.items():
        tbl = _base_table(grp)
        ranked = sorted(tbl.items(), key=lambda kv: (-kv[1]["pts"], -kv[1]["gd"], -kv[1]["gf"]))
        out[g] = [{"team": t, **s} for t, s in ranked]
    return out


def simulate_groups(groups: dict, get_lambdas, n_runs: int = 3000,
                    rho: float = -0.10, seed: int = 7) -> dict:
    """Monte-Carlo der Restspiele. get_lambdas(home, away) -> (lam1, lam2).

    Rückgabe: {"teams": {team: {p_win_group, p_top2, p_advance, p_third, group}},
               "n_runs", "n_remaining"}.
    """
    rng = np.random.default_rng(seed)

    # Restspiele sammeln + λ einmalig berechnen (deterministisch, schnell)
    remaining = []           # (group, home, away)
    lam = []                 # (lam_home, lam_away)
    base = {}                # group -> base table
    for g, grp in groups.items():
        base[g] = _base_table(grp)
        for m in grp["matches"]:
            if m["status"] != "FINISHED" or m["hg"] is None:
                if m["home"] and m["away"]:
                    remaining.append((g, m["home"], m["away"]))
                    lh, la = get_lambdas(m["home"], m["away"])
                    lam.append((max(0.05, lh), max(0.05, la)))

    teams = [t for grp in groups.values() for t in grp["teams"]]
    team_group = {t: g for g, grp in groups.items() for t in grp["teams"]}
    counts = {t: {"win_group": 0, "top2": 0, "advance": 0, "third": 0} for t in teams}

    if not remaining:
        # Gruppenphase vorbei oder keine λ — nur Ist-Tabellen, keine Sim
        return {"teams": {t: {"p_win_group": None, "p_top2": None, "p_advance": None,
                              "p_third": None, "group": team_group[t]} for t in teams},
                "n_runs": 0, "n_remaining": 0}

    lam_h = np.array([x[0] for x in lam])
    lam_a = np.array([x[1] for x in lam])
    R = len(remaining)
    gh = rng.poisson(lam_h, size=(n_runs, R))   # Heimtore je Lauf/Spiel
    ga = rng.poisson(lam_a, size=(n_runs, R))

    for r in range(n_runs):
        # Tabellen für diesen Lauf aus Basis kopieren
        tbl = {g: {t: dict(s) for t, s in base[g].items()} for g in groups}
        for i, (g, h, a) in enumerate(remaining):
            hg, ag = int(gh[r, i]), int(ga[r, i])
            th, ta = tbl[g][h], tbl[g][a]
            th["gf"] += hg; th["gd"] += hg - ag
            ta["gf"] += ag; ta["gd"] += ag - hg
            if hg > ag:
                th["pts"] += 3
            elif ag > hg:
                ta["pts"] += 3
            else:
                th["pts"] += 1; ta["pts"] += 1
        thirds = []
        for g in groups:
            ranked = sorted(tbl[g].items(), key=lambda kv: (-kv[1]["pts"], -kv[1]["gd"], -kv[1]["gf"]))
            counts[ranked[0][0]]["win_group"] += 1
            counts[ranked[0][0]]["top2"] += 1
            counts[ranked[1][0]]["top2"] += 1
            counts[ranked[0][0]]["advance"] += 1
            counts[ranked[1][0]]["advance"] += 1
            if len(ranked) >= 3:
                t3, s3 = ranked[2]
                counts[t3]["third"] += 1
                thirds.append((t3, s3["pts"], s3["gd"], s3["gf"]))
        thirds.sort(key=lambda x: (-x[1], -x[2], -x[3]))
        for t3, *_ in thirds[:ADVANCE_THIRDS]:
            counts[t3]["advance"] += 1

    res = {}
    for t in teams:
        c = counts[t]
        res[t] = {"p_win_group": round(c["win_group"] / n_runs, 4),
                  "p_top2": round(c["top2"] / n_runs, 4),
                  "p_advance": round(c["advance"] / n_runs, 4),
                  "p_third": round(c["third"] / n_runs, 4),
                  "group": team_group[t]}
    return {"teams": res, "n_runs": n_runs, "n_remaining": R}


def _resolve_one_run(groups, base, remaining, glam, rng):
    """Eine Gruppenphasen-Resolution: -> winners, runners, qualifizierte 8 Dritte."""
    tbl = {g: {t: dict(s) for t, s in base[g].items()} for g in groups}
    for (g, h, a) in remaining:
        l1, l2 = glam[(g, h, a)]
        hg, ag = int(rng.poisson(l1)), int(rng.poisson(l2))
        th, ta = tbl[g][h], tbl[g][a]
        th["gf"] += hg; th["gd"] += hg - ag
        ta["gf"] += ag; ta["gd"] += ag - hg
        if hg > ag:
            th["pts"] += 3
        elif ag > hg:
            ta["pts"] += 3
        else:
            th["pts"] += 1; ta["pts"] += 1
    winners, runners, thirds = {}, {}, []
    for g in groups:
        gl = g[-1]   # "GROUP_A" -> "A"
        ranked = sorted(tbl[g].items(), key=lambda kv: (-kv[1]["pts"], -kv[1]["gd"], -kv[1]["gf"]))
        winners[gl] = ranked[0][0]
        runners[gl] = ranked[1][0]
        if len(ranked) >= 3:
            s = ranked[2][1]
            thirds.append((gl, ranked[2][0], s["pts"], s["gd"], s["gf"]))
    thirds.sort(key=lambda x: (-x[2], -x[3], -x[4]))
    qual = thirds[:ADVANCE_THIRDS]
    third_team = {gl: team for gl, team, *_ in qual}
    return winners, runners, third_team


def _sample_ko(t1, t2, lam_fn, rng):
    """Ein K.o.-Spiel: 90 Min, sonst Verlängerung (1/3 λ), sonst Elfmeter (~50/50)."""
    l1, l2 = lam_fn(t1, t2)
    g1, g2 = rng.poisson(l1), rng.poisson(l2)
    if g1 != g2:
        return t1 if g1 > g2 else t2
    e1, e2 = rng.poisson(l1 / 3.0), rng.poisson(l2 / 3.0)
    if e1 != e2:
        return t1 if e1 > e2 else t2
    return t1 if rng.random() < 0.5 else t2


def simulate_full(groups: dict, get_lambdas, n_runs: int = 2000,
                  rho: float = -0.10, seed: int = 11) -> dict:
    """Volle Turnier-Simulation inkl. K.o.-Bracket → P(Runde erreicht)/P(Titel) je Team
    UND ein projizierter Bracket (häufigster Sieger je Match) für die Baum-Anzeige."""
    rng = np.random.default_rng(seed)

    # Gruppen-Restspiele + λ einmalig (deterministisch)
    remaining, base = [], {}
    for g, grp in groups.items():
        base[g] = _base_table(grp)
        for m in grp["matches"]:
            if m["status"] != "FINISHED" or m["hg"] is None:
                if m["home"] and m["away"]:
                    remaining.append((g, m["home"], m["away"]))
    glam = {(g, h, a): get_lambdas(h, a) for (g, h, a) in remaining}

    lam_cache: dict = {}
    def L(t1, t2):
        key = (t1, t2)
        if key not in lam_cache:
            lam_cache[key] = get_lambdas(t1, t2)
        return lam_cache[key]

    teams = [t for grp in groups.values() for t in grp["teams"]]
    reach = {t: {"R16": 0, "QF": 0, "SF": 0, "FINAL": 0, "CHAMPION": 0} for t in teams}
    win_count: dict[int, dict] = {}   # match_id -> {team: count} (häufigster Sieger)

    def bump(mid, team):
        win_count.setdefault(mid, {})
        win_count[mid][team] = win_count[mid].get(team, 0) + 1

    for _ in range(n_runs):
        winners, runners, third_team = _resolve_one_run(groups, base, remaining, glam, rng)
        assign = bk._kuhn_match(bk.THIRD_SLOTS, set(third_team))   # {match_id: group}

        def slot_team(mid, slot):
            typ, val = slot
            if typ == "W":
                return winners.get(val)
            if typ == "RU":
                return runners.get(val)
            return third_team.get(assign.get(mid))   # "3"

        winner_of: dict[int, str] = {}
        for (mid, s1, s2) in bk.R32:
            t1, t2 = slot_team(mid, s1), slot_team(mid, s2)
            if not t1 or not t2:
                continue
            w = _sample_ko(t1, t2, L, rng)
            winner_of[mid] = w
            reach[w]["R16"] += 1
            bump(mid, w)
        for label, rnd, key in (("R16", bk.R16, "QF"), ("QF", bk.QF, "SF"),
                                ("SF", bk.SF, "FINAL"), ("FINAL", bk.FINAL, "CHAMPION")):
            for mid, (f1, f2) in rnd.items():
                t1, t2 = winner_of.get(f1), winner_of.get(f2)
                if not t1 or not t2:
                    continue
                w = _sample_ko(t1, t2, L, rng)
                winner_of[mid] = w
                reach[w][key] += 1
                bump(mid, w)

    champ = {t: round(reach[t]["CHAMPION"] / n_runs, 4) for t in teams if reach[t]["CHAMPION"]}
    rounds = {t: {k: round(v / n_runs, 4) for k, v in reach[t].items()} for t in teams}
    projected = {mid: max(cnt.items(), key=lambda kv: kv[1])[0] for mid, cnt in win_count.items()}
    return {"champion_model": dict(sorted(champ.items(), key=lambda kv: -kv[1])),
            "rounds": rounds, "projected_winner": projected,
            "n_runs": n_runs, "unique_matchups": len(lam_cache)}

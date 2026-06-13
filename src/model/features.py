"""Feature-Engineering: Tor-Erwartungswerte (lambda) pro Team aus drei Sichten.

1. Elo-Modell      : Sieg-Wahrscheinlichkeit aus Elo-Differenz, aufgeteilt auf
                     einen Gesamttor-Baseline (WM-Gruppenphase ~2.6 Tore).
2. StatsBomb-Prior : historische Tore/Gegentore pro Spiel (Open Data, WM 18/22)
                     korrigieren den Elo-Split, sofern Daten vorhanden.
3. Markt-implizit  : aus den normalisierten Polymarket-1X2-Preisen werden die
                     (lambda1, lambda2) per Grid-Search bestimmt, deren
                     Poisson-1X2 die Marktpreise am besten reproduziert.
"""
from __future__ import annotations

import math

from src import config
from src.data_sources import statsbomb_client


# ---------------------------------------------------------------- Poisson-Helfer

def poisson_pmf(lam: float, k: int) -> float:
    return math.exp(-lam) * lam ** k / math.factorial(k)


def dixon_coles_tau(i: int, j: int, lam1: float, lam2: float, rho: float) -> float:
    """Dixon-Coles-Korrekturfaktor tau fuer das Ergebnis (i, j).

    rho < 0 hebt die remislastigen Niedrigergebnisse 0:0 und 1:1 an und senkt
    1:0/0:1 — korrigiert die Remis-Unterschaetzung der unabhaengigen Poisson.
    Auf nicht-negative tau geklemmt (Gueltigkeit bei kleinem |rho| stets gegeben)."""
    if rho == 0.0:
        return 1.0
    if i == 0 and j == 0:
        tau = 1.0 - lam1 * lam2 * rho
    elif i == 0 and j == 1:
        tau = 1.0 + lam1 * rho
    elif i == 1 and j == 0:
        tau = 1.0 + lam2 * rho
    elif i == 1 and j == 1:
        tau = 1.0 - rho
    else:
        tau = 1.0
    return tau if tau > 0.0 else 1e-9


def poisson_1x2(lam1: float, lam2: float, max_goals: int = 10,
                rho: float | None = None) -> tuple[float, float, float]:
    """(P(Team1 gewinnt), P(Remis), P(Team2 gewinnt)) bei Poisson-Toren mit
    optionaler Dixon-Coles-Korrektur (rho; Default aus config)."""
    if rho is None:
        rho = config.DIXON_COLES_RHO
    p1 = pd = p2 = 0.0
    pmf1 = [poisson_pmf(lam1, i) for i in range(max_goals + 1)]
    pmf2 = [poisson_pmf(lam2, j) for j in range(max_goals + 1)]
    for i in range(max_goals + 1):
        for j in range(max_goals + 1):
            p = pmf1[i] * pmf2[j] * dixon_coles_tau(i, j, lam1, lam2, rho)
            if i > j:
                p1 += p
            elif i == j:
                pd += p
            else:
                p2 += p
    s = p1 + pd + p2
    return p1 / s, pd / s, p2 / s


# ---------------------------------------------------------------- Elo-Modell

def elo_win_prob(elo1: float, elo2: float) -> float:
    """Klassische Elo-Erwartung (ohne Heimbonus — neutrale WM-Spielorte;
    Gastgeber-Bonus wird separat addiert)."""
    return 1.0 / (1.0 + 10 ** ((elo2 - elo1) / 400.0))


HOST_BONUS = 60  # Elo-Punkte fuer Gastgeber USA/Mexiko/Kanada im eigenen Land (geschaetzt)
HOSTS = {"United States", "USA", "Mexico", "Canada"}


def model_lambdas(team1: str, team2: str, sb_profiles: dict, elo_data: dict | None = None,
                  form: dict | None = None) -> dict:
    """Elo+StatsBomb-basierte Tor-Erwartungswerte.

    elo_data: Payload von elo_client.get_ratings() (live von eloratings.net);
    ohne Angabe statischer config-Fallback."""
    if elo_data:
        from src.data_sources import elo_client
        e1 = elo_client.rating_for(team1, elo_data)
        e2 = elo_client.rating_for(team2, elo_data)
        elo_status = elo_data.get("status", "estimated")
        elo_as_of = elo_data.get("as_of", config.ELO_SNAPSHOT_DATE)
    else:
        e1 = config.ELO_RATINGS.get(team1, config.ELO_DEFAULT)
        e2 = config.ELO_RATINGS.get(team2, config.ELO_DEFAULT)
        elo_status, elo_as_of = "estimated", config.ELO_SNAPSHOT_DATE
    if team1 in HOSTS:
        e1 += HOST_BONUS
    if team2 in HOSTS:
        e2 += HOST_BONUS

    w = elo_win_prob(e1, e2)  # Erwartungswert Team1 (Sieg=1, Remis=0.5)
    total = config.BASELINE_TOTAL_GOALS

    # Aufteilung des Gesamttor-Baselines proportional zur Elo-Erwartung.
    # Exponent 1.35 staucht extreme Quoten (empirisch plausible Torverhaeltnisse).
    r = (w / (1 - w)) ** 0.7
    lam1 = total * r / (1 + r)
    lam2 = total - lam1

    # StatsBomb-Prior: Angriffs-/Abwehrstaerke relativ zum WM-Schnitt (1.3 Tore/Team)
    sb1 = statsbomb_client.profile_for(team1, sb_profiles)
    sb2 = statsbomb_client.profile_for(team2, sb_profiles)
    sb_used = []
    AVG = 1.3
    def _atk(p):
        # xG (Event-Level, stabiler) bevorzugt: 50/50-Mix mit echten Toren
        if p.get("xg_for_pm") is not None:
            return 0.5 * p["goals_for_pm"] / AVG + 0.5 * p["xg_for_pm"] / AVG
        return p["goals_for_pm"] / AVG

    def _dfn(p):
        if p.get("xg_against_pm") is not None:
            return 0.5 * p["goals_against_pm"] / AVG + 0.5 * p["xg_against_pm"] / AVG
        return p["goals_against_pm"] / AVG

    for me, opp, idx in ((sb1, sb2, 0), (sb2, sb1, 1)):
        if me["status"] != "unavailable" and me["matches"] >= 4:
            atk = _atk(me)
            dfn = _dfn(opp) if (opp["status"] != "unavailable" and opp["matches"] >= 4) else 1.0
            adj = (atk * dfn) ** 0.5  # gedaempfte Korrektur
            adj = max(0.7, min(1.3, adj))
            if idx == 0:
                lam1 *= adj
            else:
                lam2 *= adj
            sb_used.append(me["team"])

    # In-Turnier-Form (FBref): gedaempfte Multiplikatoren, nur wenn Spiele vorliegen
    form_used = {}
    if form and form.get("status") == "live":
        from src.data_sources import fbref_client
        f1 = fbref_client.form_factor(team1, form)
        f2 = fbref_client.form_factor(team2, form)
        if f1:
            lam1 *= f1["attack"]
            lam2 *= f1["concede"]
            form_used["team1"] = f1
        if f2:
            lam2 *= f2["attack"]
            lam1 *= f2["concede"]
            form_used["team2"] = f2

    p1, pd, p2 = poisson_1x2(lam1, lam2)
    return {
        "lambda1": round(lam1, 3), "lambda2": round(lam2, 3),
        "probs": {"team1_win": p1, "draw": pd, "team2_win": p2},
        "elo": {"team1": e1, "team2": e2, "as_of": elo_as_of, "status": elo_status},
        "tournament_form": form_used or None,
        "statsbomb_adjustment_applied_for": sb_used,
        "statsbomb_status": sb_profiles.get("status", "unavailable"),
    }


# ------------------------------------------------ Angriff/Abwehr (Bivariate Poisson)

def team_strength(team: str, sb_profiles: dict, form: dict | None) -> dict:
    """Angriffs- und Abwehr-Multiplikator (~1.0 zentriert) aus StatsBomb-Historie
    (xG bevorzugt) + FBref-Turnierform, jeweils stichproben-geshrunken Richtung 1.0.
    attack>1 = mehr Tore als Schnitt; defense<1 = weniger Gegentore (gute Abwehr)."""
    from src.data_sources import statsbomb_client, fbref_client
    AVG = 1.3
    atk, dfn = [], []  # (gewicht, wert)-Paare

    sb = statsbomb_client.profile_for(team, sb_profiles)
    if sb["status"] != "unavailable" and sb["matches"] >= 4:
        af = (sb.get("xg_for_pm") or sb["goals_for_pm"]) / AVG
        df = (sb.get("xg_against_pm") or sb["goals_against_pm"]) / AVG
        w = 0.7 * sb["matches"] / (sb["matches"] + 6)   # Historie etwas niedriger gewichtet
        atk.append((w, af))
        dfn.append((w, df))

    n_form, form_basis = 0, None
    if form:
        ff = fbref_client.form_factor(team, form)
        if ff:
            w = ff["matches"] / (ff["matches"] + 2)     # aktuelle Form staerker
            atk.append((w, ff["attack"]))
            dfn.append((w, ff["concede"]))
            n_form, form_basis = ff["matches"], ff["basis"]

    def combine(samples):
        if not samples:
            return 1.0, 0.0
        wsum = sum(w for w, _ in samples)
        val = sum(w * v for w, v in samples) / wsum if wsum > 0 else 1.0
        shrink = wsum / (wsum + 1.0)                     # wenig Daten -> Richtung 1.0
        return 1.0 + shrink * (val - 1.0), wsum

    a, wa = combine(atk)
    d, wd = combine(dfn)
    return {"attack": round(max(0.7, min(1.4, a)), 3),
            "defense": round(max(0.7, min(1.4, d)), 3),
            "weight_attack": round(wa, 2), "weight_defense": round(wd, 2),
            "matches": n_form, "basis": form_basis or "elo/sb"}


def attack_defense_lambdas(team1: str, team2: str, sb_profiles: dict,
                           elo_data: dict | None = None, form: dict | None = None,
                           context: dict | None = None) -> dict:
    """Tor-Erwartungswerte aus Elo-Tordifferenz + getrennten Angriffs-/Abwehr-Staerken.

    Schritt 1: Elo-Differenz -> erwartete Tordifferenz GD (statt Win-Prob-Hack).
    Schritt 2: lambda1/2 = (Gesamt ± GD)/2.
    Schritt 3: opponent-adjustierte Angriffs-/Abwehr-Multiplikatoren.
    Schritt 4: Gastgeber-Bonus. Schritt 5: 1X2 analytisch mit Dixon-Coles.
    """
    if elo_data:
        from src.data_sources import elo_client
        e1 = elo_client.rating_for(team1, elo_data)
        e2 = elo_client.rating_for(team2, elo_data)
        elo_status = elo_data.get("status", "estimated")
        elo_as_of = elo_data.get("as_of", config.ELO_SNAPSHOT_DATE)
    else:
        e1 = config.ELO_RATINGS.get(team1, config.ELO_DEFAULT)
        e2 = config.ELO_RATINGS.get(team2, config.ELO_DEFAULT)
        elo_status, elo_as_of = "estimated", config.ELO_SNAPSHOT_DATE
    if team1 in HOSTS:
        e1 += HOST_BONUS
    if team2 in HOSTS:
        e2 += HOST_BONUS

    gd = (e1 - e2) / config.ELO_PER_GOAL
    gd = max(-2.2, min(2.2, gd))
    total = config.BASELINE_TOTAL_GOALS
    lam1 = max(0.15, (total + gd) / 2.0)
    lam2 = max(0.15, total - lam1)

    s1 = team_strength(team1, sb_profiles, form)
    s2 = team_strength(team2, sb_profiles, form)
    mult1 = max(0.6, min(1.6, s1["attack"] * s2["defense"]))
    mult2 = max(0.6, min(1.6, s2["attack"] * s1["defense"]))
    lam1 = lam1 * mult1
    lam2 = lam2 * mult2

    # Spielort-Kontext (Höhe/Wetter): Gesamttor-Multiplikator + Höhen-Boni
    ctx_applied = None
    if context:
        tg = context.get("total_goals_mult", 1.0)
        m1 = context.get("team1_mult", 1.0)
        m2 = context.get("team2_mult", 1.0)
        lam1 *= tg * m1
        lam2 *= tg * m2
        if abs(tg - 1.0) > 1e-6 or m1 != 1.0 or m2 != 1.0:
            ctx_applied = {"total_goals_mult": tg, "team1_mult": m1, "team2_mult": m2,
                           "altitude_m": context.get("altitude_m"),
                           "weather": context.get("weather"),
                           "injury_override": context.get("injury_override"),
                           "notes": context.get("notes", [])}

    lam1 = round(lam1, 3)
    lam2 = round(lam2, 3)
    p1, pd, p2 = poisson_1x2(lam1, lam2)
    used = []
    if s1["weight_attack"] > 0:
        used.append(team1)
    if s2["weight_attack"] > 0:
        used.append(team2)
    return {
        "lambda1": lam1, "lambda2": lam2,
        "probs": {"team1_win": p1, "draw": pd, "team2_win": p2},
        "elo": {"team1": e1, "team2": e2, "as_of": elo_as_of, "status": elo_status},
        "expected_goal_diff": round(gd, 3),
        "strength": {"team1": s1, "team2": s2},
        "tournament_form": ({"team1": s1, "team2": s2} if form else None),
        "statsbomb_adjustment_applied_for": used,
        "statsbomb_status": sb_profiles.get("status", "unavailable"),
        "venue_context": ctx_applied,
        "engine": "attack_defense_bipoisson",
    }


# ---------------------------------------------------------------- Markt-implizit

def market_implied_lambdas(p1_target: float, pd_target: float, p2_target: float) -> dict:
    """Grid-Search: findet (lam1, lam2), deren Poisson-1X2 den Marktpreisen
    am naechsten kommt. Macht Marktpreise fuer Scorelines/Totals nutzbar."""
    best = None
    lam1 = lam2 = 1.3
    grid = [x / 20 for x in range(6, 71)]  # 0.3 .. 3.5
    for l1 in grid:
        for l2 in grid:
            q1, qd, q2 = poisson_1x2(l1, l2, max_goals=8)
            err = (q1 - p1_target) ** 2 + (qd - pd_target) ** 2 + (q2 - p2_target) ** 2
            if best is None or err < best:
                best, lam1, lam2 = err, l1, l2
    # Feinschritt um das Grid-Optimum
    fine = [x / 100 for x in range(-8, 9, 2)]
    bl1, bl2 = lam1, lam2
    for d1 in fine:
        for d2 in fine:
            l1, l2 = max(0.05, bl1 + d1), max(0.05, bl2 + d2)
            q1, qd, q2 = poisson_1x2(l1, l2, max_goals=8)
            err = (q1 - p1_target) ** 2 + (qd - pd_target) ** 2 + (q2 - p2_target) ** 2
            if err < best:
                best, lam1, lam2 = err, l1, l2
    return {"lambda1": round(lam1, 3), "lambda2": round(lam2, 3), "fit_error": round(best, 6)}

"""Sanity-Tests fuer die Kernrechnungen.  Ausfuehren:  python -m tests.test_model"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.model import features, monte_carlo, ensemble
from src.model.whale_scoring import score_wallet


def approx(a, b, tol=1e-6):
    assert abs(a - b) < tol, f"{a} != {b}"


def test_poisson_1x2_sums_to_one():
    p1, pd, p2 = features.poisson_1x2(1.5, 1.1)
    approx(p1 + pd + p2, 1.0)
    assert p1 > p2, "staerkeres Team muss hoehere Siegquote haben"


def test_market_implied_lambda_roundtrip():
    # Bekannte lambdas -> 1X2 -> Solver muss aehnliche lambdas finden
    p1, pd, p2 = features.poisson_1x2(1.8, 0.9)
    sol = features.market_implied_lambdas(p1, pd, p2)
    assert abs(sol["lambda1"] - 1.8) < 0.15, sol
    assert abs(sol["lambda2"] - 0.9) < 0.15, sol


def test_monte_carlo_plausible():
    # rho=0 isoliert den reinen Poisson-Pfad von der Dixon-Coles-Korrektur
    mc = monte_carlo.simulate(1.6, 1.0, runs=30000, seed=7, rho=0.0)
    p = mc["probs"]
    approx(p["team1_win"] + p["draw"] + p["team2_win"], 1.0, 1e-9)
    # MC muss nahe an analytischem Poisson liegen (Parameterunsicherheit verbreitert leicht)
    a1, ad, a2 = features.poisson_1x2(1.6, 1.0, rho=0.0)
    assert abs(p["team1_win"] - a1) < 0.03
    # Verteilungssummen
    assert abs(sum(mc["total_goals_dist"]) - 1.0) < 0.01
    assert abs(sum(mc["goals_team1_dist"]) - 1.0) < 0.01
    matrix_sum = sum(sum(r) for r in mc["score_matrix"])
    assert abs(matrix_sum - 1.0) < 0.01
    # O/U-Konsistenz: Over0.5 = 1 - P(0 Tore)
    approx(mc["over_under"]["0.5"]["over"], 1 - mc["total_goals_dist"][0], 0.01)
    assert mc["over_under"]["2.5"]["over"] + mc["over_under"]["2.5"]["under"] <= 1.0 + 1e-9


def test_ensemble_normalizes_and_handles_missing():
    market = {"probs": {"team1_win": 0.5, "draw": 0.3, "team2_win": 0.2}}
    model = {"probs": {"team1_win": 0.4, "draw": 0.3, "team2_win": 0.3}}
    b = ensemble.blend_probs(market, model, None)
    approx(sum(b["probs"].values()), 1.0, 1e-6)
    assert "whale" not in b["weights_used"]
    # Gewichte renormalisiert auf market+model (aus config, nicht hartkodiert)
    from src.config import ENSEMBLE_WEIGHTS as W
    approx(b["weights_used"]["market"], W["market"] / (W["market"] + W["model"]), 1e-3)


def test_whale_small_sample_not_overweighted():
    # Wallet A: 3 Treffer aus 3 Fussball-Trades (Glueckstreffer)
    lucky = [{"type": "TRADE", "title": "World Cup x", "usdcSize": 1000, "conditionId": f"c{i}",
              "timestamp": 1781280000} for i in range(3)]
    lucky += [{"type": "REDEEM", "title": "World Cup x", "usdcSize": 2000, "conditionId": f"c{i}",
               "timestamp": 1781280000} for i in range(3)]
    # Wallet B: 60 Trades, 60% Treffer, konsistent
    big = [{"type": "TRADE", "title": "World Cup y", "usdcSize": 1000, "conditionId": f"d{i}",
            "timestamp": 1781280000} for i in range(60)]
    big += [{"type": "REDEEM", "title": "World Cup y", "usdcSize": 1500, "conditionId": f"d{i}",
             "timestamp": 1781280000} for i in range(36)]
    a = score_wallet("0xA", lucky)
    b = score_wallet("0xB", big)
    assert a["resolved_hit_rate_heuristic"] == 1.0
    assert b["score"] > a["score"], f"Konsistenz muss schlagen: {b['score']} <= {a['score']}"


def test_devig_removes_overround():
    from src.data_sources.odds_client import _devig
    # Typische 3-Weg-Quoten mit ~5% Overround
    p = _devig({"home": 2.0, "draw": 3.4, "away": 4.2})
    approx(sum(p.values()), 1.0, 1e-9)
    assert p["home"] > p["draw"] > p["away"]


def test_brier_score():
    from src.model.calibration import brier
    perfekt = brier({"team1_win": 1.0, "draw": 0.0, "team2_win": 0.0}, "team1_win")
    approx(perfekt, 0.0)
    gleich = brier({"team1_win": 1/3, "draw": 1/3, "team2_win": 1/3}, "draw")
    approx(gleich, 2/3, 1e-6)
    falsch = brier({"team1_win": 1.0, "draw": 0.0, "team2_win": 0.0}, "team2_win")
    approx(falsch, 2.0)


def test_ensemble_with_books():
    market = {"probs": {"team1_win": 0.5, "draw": 0.3, "team2_win": 0.2}}
    books = {"probs": {"team1_win": 0.55, "draw": 0.28, "team2_win": 0.17}}
    model = {"probs": {"team1_win": 0.4, "draw": 0.3, "team2_win": 0.3}}
    from src.model.ensemble import blend_probs
    b = blend_probs(market, model, None, books=books)
    approx(sum(b["probs"].values()), 1.0, 1e-6)
    assert "books" in b["weights_used"]
    # Blend muss zwischen den Quellen liegen
    assert 0.4 <= b["probs"]["team1_win"] <= 0.55


def test_elo_fallback_static():
    from src.data_sources.elo_client import rating_for
    # leeres Live-Payload -> statischer Fallback greift
    r = rating_for("Brazil", {"ratings": {}})
    assert r == 2030, r
    assert rating_for("Niemandsland", {"ratings": {}}) == 1650


def test_dixon_coles_raises_draws_analytic():
    # Moderater Favorit: DC (rho<0) muss die Remis-Wahrscheinlichkeit anheben
    _, pd_plain, _ = features.poisson_1x2(1.6, 1.0, rho=0.0)
    _, pd_dc, _ = features.poisson_1x2(1.6, 1.0, rho=-0.10)
    assert pd_dc > pd_plain, f"DC muss Remis anheben: {pd_dc} <= {pd_plain}"
    # Effektgroesse plausibel (wenige Prozentpunkte, nicht entgleist)
    assert 0.0 < (pd_dc - pd_plain) < 0.06


def test_mc_dixon_coles_matches_analytic():
    # Importance-gewichtetes MC muss die analytische DC-Verteilung reproduzieren
    a1, ad, a2 = features.poisson_1x2(1.6, 1.0, rho=-0.10)
    mc = monte_carlo.simulate(1.6, 1.0, runs=40000, seed=11, rho=-0.10)
    approx(sum(mc["probs"].values()), 1.0, 1e-9)
    assert abs(mc["probs"]["draw"] - ad) < 0.03, (mc["probs"]["draw"], ad)
    # und mehr Remis als ohne Korrektur
    mc0 = monte_carlo.simulate(1.6, 1.0, runs=40000, seed=11, rho=0.0)
    assert mc["probs"]["draw"] > mc0["probs"]["draw"]


def test_kalshi_probs_normalized_and_flipped():
    from src.data_sources.kalshi_client import probs_for_match
    events = {"status": "live", "events": [{
        "title": "Paraguay vs United States", "event_ticker": "KXWCGAME-TEST",
        "markets": [
            {"yes_sub_title": "Paraguay", "yes_bid": 20, "yes_ask": 24, "volume": 100},
            {"yes_sub_title": "United States", "yes_bid": 44, "yes_ask": 48, "volume": 100},
            {"yes_sub_title": "Tie", "yes_bid": 28, "yes_ask": 32, "volume": 100},
        ]}]}
    # Anfrage in umgekehrter Reihenfolge (unsere team1 = USA) -> muss flippen
    res = probs_for_match("United States", "Paraguay", events)
    assert res is not None
    approx(sum(res["probs"].values()), 1.0, 1e-9)
    assert res["probs"]["team1_win"] > res["probs"]["team2_win"], res["probs"]


def test_form_factor_damped_and_capped():
    from src.data_sources.fbref_client import form_factor
    # Extreme Form (5:0) nach nur 1 Spiel darf max. +25% Angriff geben
    form = {"status": "live", "teams": {"Testland": {"matches": 1, "gf_pm": 5.0, "ga_pm": 0.0}}}
    f = form_factor("Testland", form)
    assert f["attack"] <= 1.25, f
    assert f["concede"] >= 0.75, f
    assert form_factor("Unbekannt", form) is None


def test_fbref_fetch_runs_in_isolated_process(monkeypatch, tmp_path):
    import os
    import subprocess

    from src.data_sources import fbref_client

    captured = {}
    payload = {"status": "live", "teams": {}, "as_of": "2026-06-19T09:00:00"}

    def fake_run(command, **kwargs):
        captured.update(kwargs)
        Path(command[-1]).write_text(json.dumps(payload), encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, stderr="")

    monkeypatch.setattr(fbref_client.config, "DATA_RAW", tmp_path)
    monkeypatch.setattr(fbref_client.subprocess, "run", fake_run)

    assert fbref_client._run_isolated_fetch(timeout=7) == payload
    assert captured["timeout"] == 7
    if os.name == "nt":
        assert captured["creationflags"] & subprocess.CREATE_NEW_PROCESS_GROUP


def test_fbref_worker_timeout_is_nonfatal(monkeypatch, tmp_path):
    import subprocess

    from src.data_sources import fbref_client

    def fake_run(command, **kwargs):
        raise subprocess.TimeoutExpired(command, kwargs["timeout"])

    monkeypatch.setattr(fbref_client.config, "DATA_RAW", tmp_path)
    monkeypatch.setattr(fbref_client.subprocess, "run", fake_run)

    result = fbref_client._run_isolated_fetch(timeout=3)

    assert result["status"] == "unavailable"
    assert result["teams"] == {}
    assert "Timeout nach 3 Sekunden" in result["note"]


def test_venue_altitude_and_weather_off():
    from src.data_sources import venue_client
    ctx = venue_client.get_context("Mexico City", "Mexico", "Brazil")
    assert ctx["altitude_m"] == 2240
    assert ctx["total_goals_mult"] > 1.0          # Höhe hebt Tore leicht
    assert ctx["team1_mult"] > 1.0                # Mexiko höhenadaptiert
    assert ctx["team2_mult"] == 1.0               # Brasilien nicht
    # Unbekannter Ort -> neutral
    flat = venue_client.get_context("Atlantis", "A", "B")
    assert flat["total_goals_mult"] == 1.0 and flat["status"] == "unavailable"


def test_injury_override_weakens_team():
    from src.model import injuries
    base = {"total_goals_mult": 1.0, "team1_mult": 1.0, "team2_mult": 1.0, "notes": []}
    ov = {"team1_mult": 0.85, "team2_mult": 1.0, "total_mult": 0.97, "note": "Stürmer out"}
    res = injuries.apply(base, ov)
    assert res["team1_mult"] < 1.0 and res["total_goals_mult"] < 1.0
    assert res["injury_override"]["note"] == "Stürmer out"
    # Kappung: extremer Override bleibt begrenzt
    extreme = injuries.apply(base, {"team1_mult": 0.1})
    assert extreme["team1_mult"] >= 0.7


def test_portfolio_correlation_cap():
    from src.model.value_betting import portfolio
    bets = [{"slug": "g1", "ev": 0.1, "stake_pct": 1.5, "selection": "A"},
            {"slug": "g1", "ev": 0.08, "stake_pct": 1.5, "selection": "B"},
            {"slug": "g2", "ev": 0.05, "stake_pct": 1.0, "selection": "C"}]
    pf = portfolio(bets)
    g1 = sum(b["stake_pct_final"] for b in pf["plan"] if b["slug"] == "g1")
    assert g1 <= 2.0 + 1e-9          # Korrelations-Cap pro Spiel
    assert pf["per_match_capped"] is True


def test_knockout_advancement():
    from src.model.knockout import advancement_probs
    from src.data_sources.results_client import is_knockout
    # Gleichstarke Teams -> ~50/50 Weiterkommen, summiert zu 1
    r = advancement_probs(1.3, 1.3, 0.40, 0.20, 0.40)
    approx(r["team1_advance"] + r["team2_advance"], 1.0, 1e-6)
    approx(r["team1_advance"], 0.5, 0.02)
    # Stärkeres Team1: Weiterkommen > 90-Min-Sieg (Remis-Anteil geht überwiegend an Favorit)
    r2 = advancement_probs(1.8, 0.9, 0.55, 0.25, 0.20)
    assert r2["team1_advance"] > 0.55
    assert r2["team1_advance"] > r2["team2_advance"]
    # Stage-Erkennung
    assert is_knockout("LAST_16") and is_knockout("FINAL")
    assert not is_knockout("GROUP_STAGE") and not is_knockout(None)


def test_whale_gate_caps_influence():
    from src.model.ensemble import blend_probs
    agree = {"probs": {"team1_win": 0.30, "draw": 0.30, "team2_win": 0.40}}
    whale = {"probs": {"team1_win": 0.95, "draw": 0.03, "team2_win": 0.02},
             "n_wallets_scored": 10, "wallets": [{"confidence": 1.0}]}
    b = blend_probs(agree, dict(agree), whale, books=dict(agree))
    # Ohne Gate würde Whale (0.95) team1_win weit über 0.30 ziehen; mit Gate max +0.08
    assert b["probs"]["team1_win"] <= 0.30 + 0.085
    assert abs(sum(b["probs"].values()) - 1.0) < 1e-6


def test_devig_shin_reduces_favorite_bias():
    from src.data_sources.odds_client import _devig, _devig_shin
    odds = {"home": 1.5, "draw": 4.5, "away": 8.0}
    prop, shin = _devig(odds), _devig_shin(odds)
    approx(sum(shin.values()), 1.0, 1e-6)
    # Favorite-Longshot-Bias-Korrektur: Außenseiter sind überbewertet -> Shin senkt
    # den Außenseiter und hebt den Favoriten leicht ggü. proportionalem Entviggen.
    assert shin["away"] < prop["away"]
    assert shin["home"] > prop["home"]


def test_odds_filtered_best_outlier():
    from src.data_sources.odds_client import _filtered_best
    odds, book = _filtered_best([(1.80, "A"), (1.85, "B"), (1.82, "C"), (3.95, "D")])
    assert odds == 1.85 and book == "B"           # 3.95-Ausreißer verworfen
    o2, _ = _filtered_best([(2.0, "X"), (3.5, "Y")])
    assert o2 == 3.5                              # <3 Quoten -> kein Filter


def test_team_mapping_edge_cases():
    from src import config
    from src.data_sources.polymarket_client import parse_slug
    # Namens-Aliase (Buchmacher/Markt-Schreibweisen -> kanonisch)
    assert config.canonical_team("Curaçao") == "Curacao"
    assert config.canonical_team("IR Iran") == "Iran"
    assert config.canonical_team("Türkiye") == "Turkey"
    assert config.canonical_team("Côte d'Ivoire") == "Ivory Coast"
    assert config.canonical_team("USA") == "United States"
    # Slug-Codes (Polymarket) -> Klarname, inkl. Schweiz=che, Elfenbeinküste=civ
    assert parse_slug("fifwc-che-bra-2026-06-13")["team1"] == "Switzerland"
    assert parse_slug("fifwc-civ-ecu-2026-06-14")["team1"] == "Ivory Coast"
    assert parse_slug("fifwc-kor-ger-2026-06-14")["team1"] == "South Korea"


def test_polymarket_extract_1x2_minimal():
    from src.data_sources.polymarket_client import extract_1x2
    event = {"slug": "fifwc-bra-mar-2026-06-13", "title": "Brazil vs. Morocco",
             "markets": [
                 {"question": "Will Brazil win on 2026-06-13?", "outcomePrices": '["0.55","0.45"]',
                  "conditionId": "c1", "volumeNum": 100},
                 {"question": "Will Morocco win on 2026-06-13?", "outcomePrices": '["0.20","0.80"]',
                  "conditionId": "c2", "volumeNum": 100},
                 {"question": "Will Brazil vs. Morocco end in a draw?", "outcomePrices": '["0.25","0.75"]',
                  "conditionId": "c3", "volumeNum": 100}]}
    res = extract_1x2(event)
    assert res and res["team1"] == "Brazil" and res["team2"] == "Morocco"
    approx(sum(res["probs"].values()), 1.0, 1e-6)
    assert res["probs"]["team1_win"] > res["probs"]["team2_win"]


def test_calibration_timezone_and_leakage():
    import datetime as dt
    from src.model.calibration import _to_utc, _parse_kickoff
    utc = dt.timezone.utc
    # aware UTC-String bleibt korrekt UTC
    assert _to_utc("2026-06-13T01:00:00+00:00") == dt.datetime(2026, 6, 13, 1, 0, tzinfo=utc)
    # Kickoff mit Z-Suffix
    k = _parse_kickoff("2026-06-13T01:00:00Z")
    assert k == dt.datetime(2026, 6, 13, 1, 0, tzinfo=utc)
    # Pre-Kickoff-Snapshot liegt korrekt vor Anstoß (Leakage-Filter)
    assert _to_utc("2026-06-12T22:33:00+00:00") < k
    assert not (_to_utc("2026-06-13T02:00:00+00:00") < k)  # nach Anstoß -> ausgeschlossen


def test_rps_ordinal():
    from src.model.calibration import rps
    perfect = {"team1_win": 1.0, "draw": 0.0, "team2_win": 0.0}
    approx(rps(perfect, "team1_win"), 0.0)
    # Ordinale Distanz: bei Heimsieg ist "alles auf Auswaerts" schlechter als "alles auf Remis"
    away = {"team1_win": 0.0, "draw": 0.0, "team2_win": 1.0}
    draw = {"team1_win": 0.0, "draw": 1.0, "team2_win": 0.0}
    assert rps(away, "team1_win") > rps(draw, "team1_win")
    approx(rps(away, "team1_win"), 1.0)
    approx(rps(draw, "team1_win"), 0.5)
    # Gleichverteilung auf Remis-Ergebnis
    uni = {"team1_win": 1/3, "draw": 1/3, "team2_win": 1/3}
    approx(rps(uni, "draw"), 1/9, 1e-6)


def test_inline_json_escapes_script_breakout():
    from src.pipeline.export_static import _inline_json
    s = _inline_json({"x": "evil</script><img src=x onerror=alert(1)>", "y": "a b c"})
    assert "</script>" not in s           # kein Breakout aus dem <script>-Tag
    assert "\\u003c" in s                 # < wurde escaped
    back = json.loads(s)                  # bleibt gueltiges JSON
    assert back["x"] == "evil</script><img src=x onerror=alert(1)>"
    assert back["y"] == "a b c"           # Leerzeichen unveraendert


def test_log_loss_and_hit():
    from src.model.calibration import log_loss, brier, argmax_outcome
    perfect = {"team1_win": 1.0, "draw": 0.0, "team2_win": 0.0}
    approx(log_loss(perfect, "team1_win"), 0.0, 1e-6)
    uniform = {"team1_win": 1/3, "draw": 1/3, "team2_win": 1/3}
    approx(log_loss(uniform, "draw"), 1.0986, 1e-3)  # ln(3)
    # LogLoss bestraft selbstsichere Fehlprognose härter als Brier (gedeckelt bei 2)
    wrong = {"team1_win": 0.999, "draw": 0.0005, "team2_win": 0.0005}
    assert log_loss(wrong, "team2_win") > 5.0
    assert argmax_outcome(perfect) == "team1_win"


def test_calibration_reliability_gated_and_binned():
    from src.model.calibration import OUTCOMES, _reliability

    events = []
    for i in range(20):
        actual = "team1_win" if i < 10 else "team2_win"
        for outcome in OUTCOMES:
            events.append({"source": "ensemble",
                           "prob": 0.70 if outcome == actual else 0.15,
                           "actual": int(outcome == actual)})

    gated = _reliability(events[:57], 19)
    assert gated["status"] == "too_few"
    assert gated["min_n"] == 20

    live = _reliability(events, 20)
    assert live["status"] == "live"
    bins = live["sources"]["ensemble"]["bins"]
    high = next(b for b in bins if b["lo"] == 0.6)
    low = next(b for b in bins if b["lo"] == 0.0)
    approx(high["avg_pred"], 0.70, 1e-9)
    approx(high["observed"], 1.0, 1e-9)
    assert high["n"] == 20
    approx(low["avg_pred"], 0.15, 1e-9)
    approx(low["observed"], 0.0, 1e-9)
    assert low["n"] == 40


def test_model_version_stable():
    from src import config
    assert config.MODEL_VERSION.startswith("m-") and len(config.MODEL_VERSION) == 10


def test_model_version_rotates_with_elo_per_goal(monkeypatch):
    from src import config
    base = config._model_version()
    monkeypatch.setattr(config, "ELO_PER_GOAL", config.ELO_PER_GOAL + 20.0)
    assert config._model_version() != base


def _tuning_case(i, outcome="team1_win", elo1=1950, elo2=1650):
    return {"slug": f"m{i}", "team1": "A", "team2": "B",
            "forecast_at": f"2026-06-{i + 1:02d}T10:00:00+00:00",
            "outcome": outcome,
            "baseline_total_goals": 2.6,
            "model": {
                "elo": {"team1": elo1, "team2": elo2, "as_of": "snapshot", "status": "snapshot"},
                "strength": {
                    "team1": {"attack": 1.0, "defense": 1.0, "weight_attack": 0.0, "weight_defense": 0.0},
                    "team2": {"attack": 1.0, "defense": 1.0, "weight_attack": 0.0, "weight_defense": 0.0},
                },
                "venue_context": None,
                "statsbomb_status": "snapshot",
            }}


def test_parameter_tuning_prior_gate_under_20():
    from src.model import parameter_tuning
    out = parameter_tuning.suggest_parameter_tuning(
        cases=[_tuning_case(i) for i in range(19)],
        rho_anchor=-0.10,
        run_historical_backtest=False,
    )
    assert out["status"] == "prior"
    assert out["n"] == 19
    assert out["grid"] == {}


def test_parameter_tuning_grid_prefers_stronger_favorite_when_favorite_wins():
    from src.model import parameter_tuning
    out = parameter_tuning.suggest_parameter_tuning(
        cases=[_tuning_case(i) for i in range(20)],
        rho_anchor=-0.10,
        run_historical_backtest=False,
    )
    assert out["status"] == "diagnostic"
    cand = out["best_candidate"]
    assert cand["elo_per_goal"] == min(parameter_tuning.ELO_GRID)
    assert cand["margin_rps_vs_current"] > 0
    assert out["grid"]["rho_sanity"]  # rho wird nur als Sanity-Flaeche berichtet


def test_parameter_tuning_selects_last_pre_kickoff_snapshot():
    from src.model import parameter_tuning
    entries = [
        {"forecast_at": "2026-06-10T08:00:00+00:00", "kickoff_utc": "2026-06-10T12:00:00Z", "id": "early"},
        {"forecast_at": "2026-06-10T11:59:00+00:00", "kickoff_utc": "2026-06-10T12:00:00Z", "id": "last_pre"},
        {"forecast_at": "2026-06-10T12:01:00+00:00", "kickoff_utc": "2026-06-10T12:00:00Z", "id": "post"},
    ]
    assert parameter_tuning._select_last_pre_kickoff(entries)["id"] == "last_pre"


def _proposal_tuning_result():
    return {"status": "proposal",
            "n": 50,
            "current": {"elo_per_goal": 240.0, "rho": -0.10, "baseline_total_goals": 2.6},
            "best_candidate": {"elo_per_goal": 220.0, "rho": -0.10,
                               "margin_rps_vs_current": 0.014,
                               "adoption_ready": True},
            "report_path": "memory/parameter_tuning_report.md",
            "note": "Vorschlag, keine Auto-Uebernahme."}


def test_daily_pipeline_parameter_tuning_survives_exception(monkeypatch):
    from src.pipeline import daily_matchday_run

    def boom():
        raise RuntimeError("synthetischer Fehler")

    monkeypatch.setattr(daily_matchday_run.parameter_tuning, "run", boom)
    log = {"warnings": []}

    assert daily_matchday_run._run_parameter_tuning(log) is None
    assert log["parameter_tuning"]["status"] == "error"
    assert "synthetischer Fehler" in log["parameter_tuning"]["error"]
    assert any("Parameter-Tuning fehlgeschlagen" in w for w in log["warnings"])


def test_daily_pipeline_parameter_tuning_proposal_is_prominent(monkeypatch):
    from src.pipeline import daily_matchday_run
    from src.model.closing_loop import generate_report

    proposal = _proposal_tuning_result()
    monkeypatch.setattr(daily_matchday_run.parameter_tuning, "run", lambda: proposal)
    log = {"warnings": []}

    out = daily_matchday_run._run_parameter_tuning(log)
    assert out == proposal
    warning = log["parameter_tuning"]["proposal_warning"]
    assert "ELO_PER_GOAL-Wechsel empfohlen" in warning
    assert "aktuell 240.0 -> Kandidat 220.0" in warning
    assert "NICHT automatisch angewandt" in warning
    assert any(warning == w for w in log["warnings"])

    calib = {"status": "live",
             "matches": [{"slug": "m1", "result": "1-0", "outcome": "team1_win",
                          "forecast_at": "2026-06-10T10:00:00+00:00",
                          "brier": {"model": 0.1}}],
             "summary": {"model": {"mean_brier": 0.1, "mean_rps": 0.05,
                                    "mean_log_loss": 0.2, "n": 1}},
             "record": {"hits": 1, "misses": 0, "hit_rate": 1.0, "n": 1,
                        "source": "model"}}
    report = generate_report(calib, "2026-06-15T08:00:00", None, proposal)
    assert "Parameter-Tuning (ELO_PER_GOAL)" in report
    assert "ELO_PER_GOAL-Wechsel empfohlen" in report
    assert "aktuell `240.0` -> Kandidat `220.0`" in report
    assert "Nicht automatisch angewandt" in report


def test_daily_pipeline_parameter_tuning_does_not_mutate_config(monkeypatch):
    from src import config
    from src.pipeline import daily_matchday_run

    config_text_before = Path(config.__file__).read_text(encoding="utf-8")
    before = (config.ELO_PER_GOAL, config.DIXON_COLES_RHO,
              config.BASELINE_TOTAL_GOALS, dict(config.ENSEMBLE_WEIGHTS))
    monkeypatch.setattr(daily_matchday_run.parameter_tuning, "run",
                        lambda: _proposal_tuning_result())

    daily_matchday_run._run_parameter_tuning({"warnings": []})

    after = (config.ELO_PER_GOAL, config.DIXON_COLES_RHO,
             config.BASELINE_TOTAL_GOALS, dict(config.ENSEMBLE_WEIGHTS))
    config_text_after = Path(config.__file__).read_text(encoding="utf-8")
    assert after == before
    assert config_text_after == config_text_before


def test_value_betting_sigma_and_conservative():
    from src.model import value_betting as vb
    # sigma steigt mit Bandbreite und Diskrepanz
    s_low = vb.estimate_sigma(band_width=0.05, disagreement=0.02)
    s_high = vb.estimate_sigma(band_width=0.25, disagreement=0.15)
    assert s_high > s_low > 0
    # konservative Grenze liegt unter dem Anker min(Modell, Markt)
    pc = vb.conservative_prob(0.60, 0.55, s_low)
    assert pc < 0.55
    # klarer Value bei großzügiger Quote + genug Büchern
    r = vb._row("1X2", "Sieg A", 3.0, "Pinnacle", 0.55, 0.52, band_width=0.05, n_books=20)
    assert abs(r["breakeven_prob"] - 1/3) < 1e-3
    assert r["is_value"] is True and r["stake_pct"] > 0
    # Liquiditäts-Gate: dieselbe Wette mit zu wenig Büchern -> kein Value, kein Einsatz
    r2 = vb._row("1X2", "Sieg A", 3.0, "X", 0.55, 0.52, band_width=0.05, n_books=2)
    assert r2["is_value"] is False and r2["stake_pct"] == 0.0
    # niedrige Quote -> kein Value
    r3 = vb._row("1X2", "Sieg A", 1.30, "X", 0.55, 0.55, band_width=0.05, n_books=20)
    assert r3["is_value"] is False


def test_value_betting_stake_capped():
    from src.model import value_betting as vb
    # Selbst bei riesigem Edge bleibt der Einsatz unter dem high-Tier-Cap (0.75%)
    r = vb._row("1X2", "Sieg A", 5.0, "X", 0.90, 0.90, band_width=0.50, n_books=20)
    assert r["risk"] == "high"
    assert r["stake_pct"] <= 0.75 + 1e-9


def test_weight_optimizer_treats_market_sources_as_one_block():
    from src import config
    from src.model import weight_optimizer

    calib = {"n_resolved": 100,
             "summary": {
                 "market": {"mean_log_loss": 0.10},
                 "books": {"mean_log_loss": 0.10},
                 "kalshi": {"mean_log_loss": 0.10},
                 "model": {"mean_log_loss": 1.00},
                 "whale": {"mean_log_loss": 1.00},
             }}
    out = weight_optimizer.suggest_weights(calib)
    weights = out["weights"]
    market_block = weights["market"] + weights["books"] + weights["kalshi"]

    assert out["status"] == "data-driven"
    assert "Markt-Block" in out["note"]
    assert market_block < 0.80, weights
    assert weights["model"] > 0.10 and weights["whale"] > 0.10, weights

    equal_skill = {"n_resolved": 100,
                   "summary": {
                       "market": {"mean_log_loss": 0.30},
                       "books": {"mean_log_loss": 0.30},
                       "kalshi": {"mean_log_loss": 0.30},
                       "model": {"mean_log_loss": 0.30},
                   }}
    equal_out = weight_optimizer.suggest_weights(equal_skill)
    equal_weights = equal_out["weights"]
    equal_market_block = equal_weights["market"] + equal_weights["books"] + equal_weights["kalshi"]
    # Bei gleichem Skill zaehlt der Markt-Block wie EINE Stimme (~ Modell). Toleranz 0.08:
    # der kleine Rest-Vorsprung des Blocks kommt aus dem bewusst markt-lastigen config-Prior
    # (Variante A — Prior heilig, De-Korrelation nur in der Daten-Skill-Schaetzung).
    approx(equal_market_block, equal_weights["model"], 0.08)

    small_n = weight_optimizer.suggest_weights(dict(calib, n_resolved=weight_optimizer.MIN_N - 1))
    assert small_n["status"] == "prior"
    assert small_n["weights"] == dict(config.ENSEMBLE_WEIGHTS)


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"OK  {name}")
    print("Alle Tests bestanden.")

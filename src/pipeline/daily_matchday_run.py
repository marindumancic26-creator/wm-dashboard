"""Taegliche Matchday-Pipeline.

Ablauf pro Lauf (manuell: `python -m src.pipeline.daily_matchday_run`):
  1. Polymarket: offene fifwc-Events fuer heute + morgen finden
  2. Pro Spiel: Marktpreise, Trades, Holder snapshotten (data/raw)
  3. StatsBomb-Team-Profile laden (API falls Credentials, sonst Open Data historisch)
  4. Features, Whale-Scoring, Ensemble, Monte Carlo
  5. Export: data/snapshots/<datum>.json (maschinenlesbar)
            data/processed/dashboard_data.json (fuer das Dashboard)
            memory/daily_runs/<datum>.md + memory/matches/<slug>.md (Obsidian)
"""
from __future__ import annotations

import datetime as dt
import json
import sys
import traceback

from src import config
from src.data_sources import elo_client
from src.data_sources import espn_client
from src.data_sources import fbref_client
from src.data_sources import kalshi_client
from src.data_sources import odds_client
from src.data_sources import polymarket_client as pm
from src.data_sources import results_client
from src.data_sources import statsbomb_client as sb
from src.data_sources import venue_client
from src.model import (calibration, closing_loop, data_quality, ensemble, features,
                       injuries, knockout, market_arbitrage, monte_carlo,
                       parameter_tuning, tournament, value_betting,
                       weight_optimizer, whale_scoring)
from src.pipeline import post_world_cup_switch


def _compact_parameter_tuning(result: dict) -> dict:
    cand = result.get("best_candidate") or {}
    current = result.get("current") or {}
    return {"status": result.get("status"),
            "n": result.get("n"),
            "current_elo_per_goal": current.get("elo_per_goal"),
            "candidate_elo_per_goal": cand.get("elo_per_goal"),
            "margin_rps_vs_current": cand.get("margin_rps_vs_current"),
            "report_path": result.get("report_path"),
            "note": result.get("note")}


def _parameter_tuning_warning(result: dict) -> str | None:
    if result.get("status") != "proposal":
        return None
    cand = result.get("best_candidate") or {}
    current = result.get("current") or {}
    return ("WARNUNG PARAMETER-TUNING: ELO_PER_GOAL-Wechsel empfohlen: "
            f"aktuell {current.get('elo_per_goal')} -> Kandidat {cand.get('elo_per_goal')}; "
            f"Walk-forward-RPS-Marge {cand.get('margin_rps_vs_current')}. "
            "NICHT automatisch angewandt.")


def _run_parameter_tuning(log: dict) -> dict | None:
    """Analyse-Report erzeugen; Fehler duerfen den Daily-Run nicht abbrechen."""
    try:
        result = parameter_tuning.run()
        compact = _compact_parameter_tuning(result)
        warning = _parameter_tuning_warning(result)
        if warning:
            compact["proposal_warning"] = warning
            log.setdefault("warnings", []).append(warning)
        log["parameter_tuning"] = compact
        return result
    except Exception as exc:
        msg = f"Parameter-Tuning fehlgeschlagen: {exc}"
        log.setdefault("warnings", []).append(msg)
        log["parameter_tuning"] = {"status": "error", "error": str(exc)}
        return None


def _run_post_world_cup_switch(log: dict, fixtures: dict) -> dict | None:
    """Nach WM-Ende auf Vereinsmodus umschalten; Fehler brechen Daily nicht ab."""
    try:
        result = post_world_cup_switch.check_and_switch(fixtures=fixtures)
        compact = post_world_cup_switch.compact(result)
        log["post_world_cup_switch"] = compact
        if result.get("status") == "switched":
            log.setdefault("warnings", []).append(
                "POST-WM-SWITCH: Vereinsfussball-Modus wurde automatisch aktiviert; "
                "Value/Staking bleibt gesperrt, bis die Gates bestanden sind.")
        return result
    except Exception as exc:
        msg = f"Post-WM-Switch-Pruefung fehlgeschlagen: {exc}"
        log.setdefault("warnings", []).append(msg)
        log["post_world_cup_switch"] = {"status": "error", "error": str(exc)}
        return None


def run(dates: list[str] | None = None, skip_whales: bool = False) -> dict:
    started = dt.datetime.now()
    today = dt.date.today()
    # Vortag einschliessen: Polymarket-Slugs tragen US-Ostkuesten-Daten, spaete
    # Spiele (z.B. 21:00 ET = 03:00 MESZ) liefen sonst faelschlich aus dem Fenster
    dates = dates or [str(today - dt.timedelta(days=1)), str(today),
                      str(today + dt.timedelta(days=1))]
    log = {"started_at": started.isoformat(timespec="seconds"), "dates": dates,
           "matches_ok": [], "matches_failed": [], "warnings": []}

    print(f"[{started:%H:%M:%S}] Daily Run fuer {dates}")

    # --- StatsBomb (einmal pro Lauf) -------------------------------------
    sb_profiles = sb.get_team_profiles()
    log["statsbomb"] = {"mode": sb_profiles.get("mode"), "status": sb_profiles.get("status"),
                        "cache": sb_profiles.get("cache"), "teams": len(sb_profiles.get("teams", {})),
                        "note": sb_profiles.get("source_note")}
    print(f"  StatsBomb: mode={sb_profiles.get('mode')} status={sb_profiles.get('status')} "
          f"teams={len(sb_profiles.get('teams', {}))}")
    if sb_profiles.get("status") == "unavailable":
        log["warnings"].append("StatsBomb nicht erreichbar — Modell nutzt nur Elo-Prior.")

    # --- Elo live (eloratings.net, Fallback: statischer Snapshot) ---------
    elo_data = elo_client.get_ratings()
    log["elo"] = {"status": elo_data["status"], "as_of": elo_data["as_of"],
                  "n_teams": elo_data.get("n_teams"), "source": elo_data["source"]}
    print(f"  Elo: {elo_data['status']} ({elo_data.get('n_teams')} Teams, {elo_data['source']})")
    if elo_data["status"] != "live":
        log["warnings"].append(f"Elo-Fallback aktiv: {elo_data['source']}")

    # --- Buchmacher-Quoten (The Odds API; ohne Key: unavailable) ----------
    all_odds = odds_client.fetch_all_odds()
    log["books"] = {"status": all_odds["status"],
                    "n_events": len(all_odds.get("events", [])),
                    "note": all_odds.get("note"),
                    "requests_remaining": all_odds.get("requests_remaining")}
    print(f"  Buchmacher: {all_odds['status']} ({len(all_odds.get('events', []))} Events)")
    if all_odds["status"] != "live":
        log["warnings"].append(all_odds.get("note", "Buchmacher-Quoten nicht verfuegbar."))

    # --- Kalshi (zweiter Prognosemarkt, kein Key) --------------------------
    kalshi_events = kalshi_client.fetch_events()
    log["kalshi"] = {"status": kalshi_events["status"],
                     "n_events": len(kalshi_events.get("events", [])),
                     "note": kalshi_events.get("note")}
    print(f"  Kalshi: {kalshi_events['status']} ({len(kalshi_events.get('events', []))} Events)")

    # --- ESPN-Status/Aufstellungen (inoffiziell, kein Key) ------------------
    scoreboard = espn_client.fetch_scoreboard(dates[0], dates[-1])
    log["espn"] = {"status": scoreboard["status"],
                   "n_games": len(scoreboard.get("games", [])),
                   "note": scoreboard.get("note")}
    print(f"  ESPN: {scoreboard['status']} ({len(scoreboard.get('games', []))} Spiele)")

    # --- FBref-Turnierform (langsam, 20h-Cache; Fehler nicht fatal) ---------
    form = fbref_client.get_tournament_form()
    log["fbref_form"] = {"status": form["status"],
                         "n_teams": len(form.get("teams", {})),
                         "xg_available": form.get("xg_available", False),
                         "note": form.get("note")}
    print(f"  FBref-Form: {form['status']} ({len(form.get('teams', {}))} Teams mit Spielen, "
          f"xG={'ja' if form.get('xg_available') else 'nein'})")
    if form["status"] != "live":
        log["warnings"].append(form.get("note", "FBref-Form nicht verfuegbar."))

    # --- Polymarket Discovery --------------------------------------------
    try:
        events = pm.discover_match_events(dates)
    except Exception as exc:
        log["warnings"].append(f"Polymarket-Discovery fehlgeschlagen: {exc}")
        events = []
    print(f"  Polymarket: {len(events)} Match-Events gefunden")

    injury_overrides = injuries.load_overrides()
    if injury_overrides:
        log["injury_overrides"] = list(injury_overrides.keys())

    # K.o.-Stage-Info (für Verlängerung/Elfmeter-Weiterkommen); ohne Key leer
    fixtures = results_client.fetch_fixtures()

    match_results = []
    for ev in events:
        slug = ev.get("slug")
        try:
            snap = pm.snapshot_market(slug)
            if not snap:
                raise RuntimeError("1X2-Extraktion fehlgeschlagen")
            market = snap["market"]

            # ESPN-Status/Spielort zuerst — fliesst als Kontext ins Modell
            espn = espn_client.info_for_match(market["team1"], market["team2"], scoreboard)
            lineup = None
            if espn and espn.get("state") in ("pre", "in") and espn.get("espn_id"):
                lineup = espn_client.lineups(espn["espn_id"])
            venue_ctx = venue_client.get_context(
                (espn or {}).get("city"), market["team1"], market["team2"],
                (espn or {}).get("kickoff_utc"))
            # Manuelles Verletzungs-/Aufstellungs-Override (data/processed/adjustments.json)
            inj = injury_overrides.get(slug)
            if inj:
                venue_ctx = injuries.apply(venue_ctx, inj)

            model = features.attack_defense_lambdas(market["team1"], market["team2"],
                                                    sb_profiles, elo_data, form=form,
                                                    context=venue_ctx)

            books = odds_client.probs_for_match(market["team1"], market["team2"],
                                                market["date"], all_odds)
            kalshi = kalshi_client.probs_for_match(market["team1"], market["team2"], kalshi_events)

            whale = None
            if not skip_whales:
                try:
                    whale = whale_scoring.whale_signal(snap)
                except Exception as exc:
                    log["warnings"].append(f"{slug}: Whale-Scoring fehlgeschlagen ({exc})")

            blend = ensemble.blend_probs(market, model, whale, books=books, kalshi=kalshi)
            lams = ensemble.blend_lambdas(market, model, blend.get("weights_used", {}),
                                          books=books, kalshi=kalshi)
            mc = monte_carlo.simulate(lams["lambda1"], lams["lambda2"])

            # K.o.-Phase: Weiterkommen (Verlängerung + Elfmeter) zusätzlich zum 90-Min-1X2
            ko = None
            stage = results_client.stage_for(market["team1"], market["team2"], fixtures)
            if results_client.is_knockout(stage) and blend.get("probs"):
                bp = blend["probs"]
                ko = knockout.advancement_probs(lams["lambda1"], lams["lambda2"],
                                                bp["team1_win"], bp["draw"], bp["team2_win"])
                ko["stage"] = stage

            entry = {
                "slug": slug, "title": market["title"], "date": market["date"],
                "team1": market["team1"], "team2": market["team2"],
                "market": market, "books": books, "kalshi": kalshi,
                "model": model, "whale": whale,
                "match_info": espn, "lineups": lineup, "venue": venue_ctx,
                "ensemble": blend, "lambdas": lams, "monte_carlo": mc, "knockout": ko,
            }
            # Reine Diagnose: heutige Preis-Payloads enthalten noch keine belastbare
            # Tiefe/Kosten/Settlement-Identitaet und duerfen daher keinen Arb ausweisen.
            entry["arbitrage"] = market_arbitrage.audit_legacy_sources(market, kalshi)
            # Echte Buchmacherquoten + EV/Value-Bewertung
            best_prices = odds_client.best_prices_for_match(market["team1"], market["team2"], all_odds)
            entry["value"] = value_betting.evaluate_match(entry, best_prices)
            # Datenqualitaets-Ampel + Einsatz-Gate
            entry["data_quality"] = data_quality.score_match(entry)
            entry["value"] = value_betting.apply_quality_gate(entry["value"], entry["data_quality"])
            # Kompakte 1X2-Bestquoten fuer CLV/ROI-Tracking persistieren
            if best_prices:
                entry["odds_1x2"] = {sel: best_prices["h2h"][sel]["best_odds"]
                                     for sel in ("team1_win", "draw", "team2_win")
                                     if best_prices["h2h"].get(sel)}
            match_results.append(entry)
            log["matches_ok"].append(slug)
            print(f"  OK  {market['title']}: blended={blend['probs']}")
        except Exception as exc:
            log["matches_failed"].append({"slug": slug, "error": str(exc)})
            print(f"  FEHLER {slug}: {exc}")
            traceback.print_exc()

    # --- Value-Bet-Portfolio ueber alle Spiele ----------------------------
    all_value = []
    all_opps = []
    for m in match_results:
        for vb in m.get("value", {}).get("value_bets", []):
            all_value.append({**vb, "match": m["title"], "slug": m["slug"]})
        for op in m.get("value", {}).get("opportunities", []):
            all_opps.append({**op, "match": m["title"], "slug": m["slug"]})
    portfolio = value_betting.portfolio(all_value)
    opp_portfolio = value_betting.opportunity_portfolio(all_opps)
    log["value"] = {"n_value_bets": portfolio["n_value_bets"],
                    "total_stake_pct": portfolio["total_stake_pct"]}
    print(f"  Value-Bets: {portfolio['n_value_bets']} (Gesamteinsatz {portfolio['total_stake_pct']}% Bankroll)")

    # --- Kalibrierung: Prognosen gegen offizielle Ergebnisse aufloesen -----
    results = results_client.fetch_results()
    calib = calibration.evaluate(results)
    weights_suggestion = weight_optimizer.suggest_weights(calib)
    log["weights_suggestion"] = {"status": weights_suggestion["status"],
                                 "n": weights_suggestion.get("n")}
    log["calibration"] = {"status": calib["status"],
                          "n_resolved": calib.get("n_resolved", 0),
                          "note": calib.get("note", "")}
    print(f"  Kalibrierung: {calib['status']} ({calib.get('n_resolved', 0)} aufgeloeste Spiele)")
    if calib["status"] != "live":
        log["warnings"].append(calib.get("note", "Kalibrierung nicht verfuegbar."))

    # --- Turnier-Simulation (Gruppenphase) + Titel-Odds (Markt) -----------
    tourn_payload = None
    try:
        groups = tournament.build_groups(fixtures)
        if groups:
            def _tourn_lambdas(t1, t2):
                m = features.attack_defense_lambdas(t1, t2, sb_profiles, elo_data, form=form)
                return m["lambda1"], m["lambda2"]
            sim = tournament.simulate_groups(groups, _tourn_lambdas, n_runs=2500,
                                             rho=config.DIXON_COLES_RHO)
            bracket = tournament.simulate_full(groups, _tourn_lambdas, n_runs=2000,
                                               rho=config.DIXON_COLES_RHO)
            standings = tournament.current_standings(groups)
            champion = pm.fetch_outright_winner()
            tourn_payload = {"standings": standings, "advance": sim, "bracket": bracket,
                             "champion": champion, "groups": sorted(groups.keys())}
            top = next(iter(bracket["champion_model"].items()), (None, 0))
            print(f"  Turnier: {len(groups)} Gruppen, {sim['n_remaining']} Restspiele, "
                  f"Bracket-Sim Titel-Favorit {top[0]} {top[1]*100:.0f}% (Modell), "
                  f"Markt-Odds {'live' if champion else 'n/a'}")
    except Exception as exc:
        log["warnings"].append(f"Turnier-Simulation fehlgeschlagen: {exc}")

    finished = dt.datetime.now()
    log["finished_at"] = finished.isoformat(timespec="seconds")
    log["duration_s"] = round((finished - started).total_seconds(), 1)

    payload = {
        "generated_at": finished.isoformat(timespec="seconds"),
        "run_log": log,
        "disclaimer": ("Keine Finanz- oder Wettberatung. Prognosemaerkte koennen fehlerhaft, "
                       "illiquide, manipuliert oder unvollstaendig sein. Modellwerte sind Schaetzungen."),
        "config": {"ensemble_weights": config.ENSEMBLE_WEIGHTS, "mc_runs": config.MC_RUNS,
                   "elo_status": elo_data["status"], "elo_as_of": elo_data["as_of"],
                   "model_version": config.MODEL_VERSION, "dixon_coles_rho": config.DIXON_COLES_RHO,
                   "elo_per_goal": config.ELO_PER_GOAL,
                   "baseline_total_goals": config.BASELINE_TOTAL_GOALS},
        "calibration": calib,
        "weights_suggestion": weights_suggestion,
        "parameter_tuning": None,
        "value_portfolio": portfolio,
        "opportunity_portfolio": opp_portfolio,
        "tournament": tourn_payload,
        "matches": match_results,
    }

    # --- Exporte ----------------------------------------------------------
    # pro Lauf eine Datei (nicht pro Tag) — mehrere Laeufe/Tag duerfen sich nicht
    # ueberschreiben, sonst verlieren wir Pre-Kickoff-Staende fuer die Kalibrierung
    snap_file = config.DATA_SNAPSHOTS / f"{started:%Y-%m-%d_%H%M%S}.json"
    # Degradierte Laeufe werden bewusst publiziert: Das Dashboard soll immer
    # einen aktuellen Laufzustand zeigen, auch wenn die Match-Discovery 0 Spiele liefert.
    if not match_results:
        log["degraded"] = True
        log["warnings"].append("DEGRADIERTER LAUF: 0 Spiele geladen - Dashboard wird "
                               "trotzdem aktualisiert, damit der Fehler sichtbar ist.")
        print("  WARNUNG: Degradierter Lauf (0 Spiele) - Dashboard wird trotzdem aktualisiert.")

    # Parameter-Tuning laeuft nur als Analyse/Vorschlag. Es liest die gerade
    # persistierten Pre-Kickoff-Snapshots und darf config.py nie veraendern.
    tuning_result = _run_parameter_tuning(log)
    payload["parameter_tuning"] = tuning_result
    switch_result = _run_post_world_cup_switch(log, fixtures)
    payload["operation_mode"] = post_world_cup_switch.compact(switch_result or {})
    snap_file.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    (config.DATA_PROCESSED / "dashboard_data.json").write_text(
        json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    _write_markdown(payload, today)

    # Deterministischer Closing-Loop-Report (automatische Tages-Lernzusammenfassung)
    closing_loop_path = config.DAILY_RUNS_DIR / f"{today}_closing_loop.md"
    existing_closing_loop = (closing_loop_path.read_text(encoding="utf-8")
                             if closing_loop_path.exists() else None)
    report = closing_loop.generate_report(calib, payload["generated_at"], weights_suggestion,
                                          parameter_tuning_result=tuning_result,
                                          existing_report=existing_closing_loop)
    closing_loop_path.write_text(report, encoding="utf-8")

    # Static-Export fürs Handy/GitHub Pages (self-contained docs/index.html)
    try:
        from src.pipeline import export_static
        export_static.export()
    except Exception as exc:
        log["warnings"].append(f"Static-Export fehlgeschlagen: {exc}")

    print(f"  Export: {snap_file.name}, dashboard_data.json, docs/index.html, "
          f"memory/daily_runs/{today}.md, {today}_closing_loop.md")
    return payload


def _fmt_pct(x):
    return f"{x * 100:.1f}%" if x is not None else "–"


def _write_markdown(payload: dict, today) -> None:
    lines = [f"# Daily Run {today}", "",
             f"- Start: {payload['run_log']['started_at']}  |  Dauer: {payload['run_log']['duration_s']}s",
             f"- StatsBomb: `{payload['run_log']['statsbomb']['mode']}` / {payload['run_log']['statsbomb']['status']}",
             f"- Spiele OK: {len(payload['run_log']['matches_ok'])} | Fehler: {len(payload['run_log']['matches_failed'])}",
             ""]
    for w in payload["run_log"]["warnings"]:
        lines.append(f"> ⚠️ {w}")
    lines.append("")
    calib = payload.get("calibration", {})
    if calib.get("status") == "live" and calib.get("summary"):
        lines += ["## Kalibrierung (Brier, kumulativ)", "",
                  "| Quelle | Ø Brier | n |", "|---|---|---|"]
        for src, s in sorted(calib["summary"].items(), key=lambda kv: kv[1]["mean_brier"]):
            lines.append(f"| {src} | {s['mean_brier']} | {s['n']} |")
        lines.append("")
    for m in payload["matches"]:
        e = m["ensemble"]["probs"]
        mc = m["monte_carlo"]
        lines += [f"## [[{m['slug']}|{m['title']}]] ({m['date']})", "",
                  f"| Quelle | {m['team1']} | Remis | {m['team2']} |", "|---|---|---|---|",
                  f"| Markt | {_fmt_pct(m['market']['probs']['team1_win'])} | {_fmt_pct(m['market']['probs']['draw'])} | {_fmt_pct(m['market']['probs']['team2_win'])} |"]
        if m.get("books"):
            b = m["books"]["probs"]
            lines.append(f"| Buchmacher ({m['books']['basis']}) | {_fmt_pct(b['team1_win'])} | {_fmt_pct(b['draw'])} | {_fmt_pct(b['team2_win'])} |")
        lines += [f"| Modell | {_fmt_pct(m['model']['probs']['team1_win'])} | {_fmt_pct(m['model']['probs']['draw'])} | {_fmt_pct(m['model']['probs']['team2_win'])} |",
                  f"| **Ensemble** | **{_fmt_pct(e['team1_win'])}** | **{_fmt_pct(e['draw'])}** | **{_fmt_pct(e['team2_win'])}** |", "",
                  f"Top-Ergebnis: **{mc['top_scorelines'][0]['score']}** ({_fmt_pct(mc['top_scorelines'][0]['prob'])}), "
                  f"xG {mc['expected_goals']['team1']}:{mc['expected_goals']['team2']}, "
                  f"Over 2.5: {_fmt_pct(mc['over_under']['2.5']['over'])}", ""]
        # Match-Notiz fuer Obsidian
        match_md = [f"# {m['title']}", "", f"Datum: {m['date']}  |  Stand: {payload['generated_at']}",
                    f"Quelle: [Polymarket]({m['market']['url']}) (Volumen ${m['market']['volume_usd']:,.0f})", "",
                    f"Ensemble: {m['team1']} {_fmt_pct(e['team1_win'])} / Remis {_fmt_pct(e['draw'])} / {m['team2']} {_fmt_pct(e['team2_win'])}",
                    f"Erwartete Tore: {mc['expected_goals']['team1']} : {mc['expected_goals']['team2']}", "",
                    "Top-Scorelines:", ""]
        for s in mc["top_scorelines"][:5]:
            match_md.append(f"- {s['score']} — {_fmt_pct(s['prob'])}")
        if m.get("whale"):
            match_md += ["", f"Whale-Signal ({m['whale']['n_wallets_scored']} Wallets, heuristisch): "
                         + (", ".join(f"{k} {_fmt_pct(v)}" for k, v in (m['whale']['probs'] or {}).items()) or "n/a")]
        (config.MATCHES_DIR / f"{m['slug']}.md").write_text("\n".join(match_md), encoding="utf-8")

    (config.DAILY_RUNS_DIR / f"{today}.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    skip = "--skip-whales" in sys.argv
    dates = [a for a in sys.argv[1:] if not a.startswith("--")] or None
    run(dates=dates, skip_whales=skip)

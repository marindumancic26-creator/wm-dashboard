"""Deterministischer Closing-Loop-Report (kein Claude noetig).

Erzeugt aus der Kalibrierungs-Auswertung einen taeglichen Markdown-Bericht:
Prognose vs. Ergebnis je aufgeloestem Spiel, Brier pro Quelle, rollierende
Bestenliste und automatische Warnflags (z.B. hohe Whale-Varianz). Den narrativen
Hermes-Teil (Reasoning, Gewichtungsentscheidungen) liefert Claude on demand.
"""
from __future__ import annotations

import statistics

SOURCES = ("market", "books", "kalshi", "model", "whale", "ensemble")
SOURCE_LABEL = {"market": "Polymarkt", "books": "Buchmacher", "kalshi": "Kalshi",
                "model": "Modell", "whale": "Whale", "ensemble": "Ensemble"}
HERMES_HEADING = "## Hermes-Analyse"


def _fmt(x):
    return f"{x:.3f}" if x is not None else "–"


def _extract_hermes_section(existing_report: str | None) -> list[str]:
    """Bestehenden Hermes-Block beim deterministischen Neuschreiben erhalten."""
    if not existing_report:
        return []
    report_lines = existing_report.splitlines()
    start = next((i for i, line in enumerate(report_lines)
                  if line.strip() == HERMES_HEADING), None)
    if start is None:
        return []
    end = len(report_lines)
    for i in range(start + 1, len(report_lines)):
        if report_lines[i].startswith("## ") and report_lines[i].strip() != HERMES_HEADING:
            end = i
            break
    section = report_lines[start:end]
    while section and not section[-1].strip():
        section.pop()
    return section


def _finish(lines: list[str], hermes_section: list[str]) -> str:
    if hermes_section:
        lines += hermes_section + [""]
    return "\n".join(lines)


def _parameter_tuning_section(parameter_tuning_result: dict | None) -> list[str]:
    if not parameter_tuning_result:
        return []
    status = parameter_tuning_result.get("status")
    n = parameter_tuning_result.get("n")
    lines = ["## Parameter-Tuning (ELO_PER_GOAL)", ""]
    if status == "proposal":
        current = parameter_tuning_result.get("current") or {}
        cand = parameter_tuning_result.get("best_candidate") or {}
        lines.append("**WARNUNG: ELO_PER_GOAL-Wechsel empfohlen:** "
                     f"aktuell `{current.get('elo_per_goal')}` -> "
                     f"Kandidat `{cand.get('elo_per_goal')}`; "
                     f"Walk-forward-RPS-Marge `{cand.get('margin_rps_vs_current')}`. "
                     "**Nicht automatisch angewandt.**")
    else:
        note = parameter_tuning_result.get("note") or "Kein uebernahme-reifer Vorschlag."
        lines.append(f"- Status `{status}` (n={n}): {note}")
    lines.append("")
    return lines


def generate_report(calib: dict, generated_at: str, weights_suggestion: dict | None = None,
                    parameter_tuning_result: dict | None = None,
                    existing_report: str | None = None) -> str:
    """calib = Rueckgabe von calibration.evaluate(). Gibt Markdown zurueck."""
    hermes_section = _extract_hermes_section(existing_report)
    hermes_note = ("Narrative Hermes-Analyse: siehe Abschnitt unten."
                   if hermes_section else "Narrative Hermes-Analyse: auf Anfrage.")
    lines = [f"# Closing-Loop-Report — {generated_at[:10]}", "",
             f"Stand: {generated_at} · automatisch erzeugt (deterministisch, ohne Claude).",
             hermes_note, ""]

    if calib.get("status") != "live":
        lines.append(f"> Kalibrierung nicht verfügbar: {calib.get('note', '')}")
        return _finish(lines, hermes_section)

    matches = calib.get("matches", [])
    if not matches:
        lines.append("> Noch keine aufgelösten Spiele mit sauberer Pre-Kickoff-Prognose.")
        return _finish(lines, hermes_section)

    # --- Trefferbilanz (richtig/falsch der Headline-Prognose) -----------
    rec = calib.get("record")
    if rec:
        lines += ["## Trefferbilanz (Headline-Prognose)", "",
                  f"**✅ {rec['hits']} richtig · ❌ {rec['misses']} falsch** "
                  f"— Trefferquote {rec['hit_rate']*100:.0f}% über n={rec['n']} Spiele "
                  f"({SOURCE_LABEL.get(rec['source'], rec['source'])}).", ""]

    # --- Pro Spiel -------------------------------------------------------
    lines += [f"## Aufgelöste Spiele ({len(matches)})", ""]
    for m in matches:
        briers = m["brier"]
        best = min(briers.items(), key=lambda kv: kv[1]) if briers else (None, None)
        worst = max(briers.items(), key=lambda kv: kv[1]) if briers else (None, None)
        lines += [f"### {m['slug']} — Ergebnis {m['result']} ({m['outcome']})",
                  f"Prognose-Stand: {m.get('forecast_at', '?')}", "",
                  "| Quelle | Brier |", "|---|---|"]
        for src in SOURCES:
            if src in briers:
                mark = " ✅" if src == best[0] else (" ❌" if src == worst[0] else "")
                lines.append(f"| {SOURCE_LABEL.get(src, src)} | {_fmt(briers[src])}{mark} |")
        lines.append("")

    # --- Rollierende Bestenliste (Brier / LogLoss / Hit-Rate) -----------
    summary = calib.get("summary", {})
    lines += ["## Rollierende Bestenliste (alle aufgelösten Spiele)", "",
              "| Rang | Quelle | Ø Brier | Ø RPS | Ø LogLoss | Hit-Rate | R/F | n |",
              "|---|---|---|---|---|---|---|---|"]
    # nach RPS sortieren (Fussball-Standard); RPS==0.0 ist gueltig (perfekt) und darf NICHT
    # als falsy auf den Brier zurueckfallen -> explizit auf None pruefen.
    def _rank_key(kv):
        rps = kv[1].get("mean_rps")
        return rps if rps is not None else kv[1]["mean_brier"]
    ranking = sorted(summary.items(), key=_rank_key)
    for rank, (src, s) in enumerate(ranking, 1):
        lines.append(f"| {rank} | {SOURCE_LABEL.get(src, src)} | {_fmt(s['mean_brier'])} "
                     f"| {_fmt(s.get('mean_rps'))} | {_fmt(s.get('mean_log_loss'))} "
                     f"| {s.get('hit_rate', 0)*100:.0f}% | {s.get('hits', 0)}/{s.get('misses', 0)} "
                     f"| {s['n']} |")
    lines += ["", "_RPS = Ranked Probability Score (ordinal, Fußball-Standard). "
                  "Brier 0.667 / RPS 0.333 / LogLoss 1.099 ≈ Zufall. Niedriger ist besser._", ""]

    # --- Wett-Kennzahlen: ROI + CLV -------------------------------------
    bet = calib.get("betting", {})
    if bet.get("n_bets"):
        lines += ["## Wett-Kennzahlen (Referenz-Policy)", "",
                  f"_{bet.get('policy', '')}_", "",
                  f"- Wetten: {bet['n_bets']} · Trefferquote {bet.get('hit_rate', 0)*100:.0f}% · "
                  f"**ROI {bet.get('roi', 0)*100:+.1f}%**"]
        if "avg_clv_odds" in bet:
            lines.append(f"- Ø CLV (Quoten): {bet['avg_clv_odds']*100:+.2f}% · "
                         f"Markt bewegte sich zur Modell-Lehne: {bet.get('beat_close_rate', 0)*100:.0f}% "
                         f"(n={bet.get('n_clv', 0)})")
        else:
            lines.append("- CLV: noch nicht messbar (Snapshots zu eng beieinander — "
                         "aussagekräftig, sobald der Daily-Run Tage im Voraus läuft).")
        lines.append("")

    # --- Gewichts-Empfehlung (datenbasiert) -----------------------------
    if weights_suggestion:
        ws = weights_suggestion
        lines += ["## Gewichts-Empfehlung", ""]
        if ws["status"] == "prior":
            lines.append(f"- {ws['note']}")
        else:
            cur = ws["prior"]
            lines += [f"_{ws['note']}_", "",
                      "| Quelle | aktuell | empfohlen |", "|---|---|---|"]
            for s, w in ws["weights"].items():
                lines.append(f"| {SOURCE_LABEL.get(s, s)} | {cur.get(s, 0)} | {w} |")
        lines.append("")

    # --- Parameter-Tuning: nur Vorschlag, keine Auto-Uebernahme ----------
    lines += _parameter_tuning_section(parameter_tuning_result)

    # --- Automatische Warnflags -----------------------------------------
    per_source: dict[str, list] = {}
    for m in matches:
        for src, b in m["brier"].items():
            per_source.setdefault(src, []).append(b)
    flags = []
    n = len(matches)
    wv = per_source.get("whale", [])
    if len(wv) >= 2 and (max(wv) - min(wv)) > 1.0:
        flags.append(f"⚠️ **Whale hochvariant** (Spannweite {_fmt(min(wv))}–{_fmt(max(wv))} "
                     f"über {len(wv)} Spiele) → defensive Gewichtung beibehalten, NICHT erhöhen.")
    mv = per_source.get("model", [])
    if mv and statistics.mean(mv) > 0.55:
        flags.append(f"⚠️ **Modell schwach kalibriert** (Ø {_fmt(statistics.mean(mv))} > 0.55) "
                     f"→ Elo-/Gastgeber-Annahmen prüfen, sobald n≥5.")
    ev = per_source.get("ensemble", [])
    mk = per_source.get("market", [])
    if ev and mk:
        if statistics.mean(ev) <= statistics.mean(mk):
            flags.append(f"✅ Ensemble schlägt/erreicht Markt "
                         f"(Ø {_fmt(statistics.mean(ev))} vs. {_fmt(statistics.mean(mk))}).")
        else:
            flags.append(f"⚠️ Ensemble schlechter als reiner Markt "
                         f"(Ø {_fmt(statistics.mean(ev))} vs. {_fmt(statistics.mean(mk))}) "
                         f"→ Gewichtung überdenken, sobald n≥5.")
    if n < 5:
        flags.append(f"ℹ️ Erst {n} Spiele aufgelöst — keine Gewichtsänderungen vor n≥5 "
                     f"(Schutz vor Überanpassung an Einzelspiele).")

    lines += ["## Automatische Flags", ""]
    lines += [f"- {f}" for f in flags] if flags else ["- Keine Auffälligkeiten."]
    lines.append("")
    return _finish(lines, hermes_section)

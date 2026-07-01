"""Deterministischer Hermes-Fallback aus dem letzten Dashboard-Snapshot.

Der geplante Hermes-Lauf nutzt primaer Codex. Falls Codex haengt oder ein
ungueltiges Format liefert, erzeugt dieses Skript eine konservative Analyse,
damit der Daily-Lernpfad trotzdem abgeschlossen und gepusht wird.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def _score(summary: dict, source: str, metric: str, default: float = 0.0) -> float:
    return float(summary.get(source, {}).get(metric, default))


def build() -> dict:
    data = json.loads(Path("data/processed/dashboard_data.json").read_text(encoding="utf-8"))
    run = data.get("run_log", {})
    calib = data.get("calibration", {})
    summary = calib.get("summary", {})
    betting = calib.get("betting", {}) or {}
    weights = data.get("weights_suggestion") or run.get("weights_suggestion") or {}
    param = data.get("parameter_tuning") or run.get("parameter_tuning") or {}

    n = int(calib.get("n_resolved") or summary.get("ensemble", {}).get("n") or 0)
    ok = len(run.get("matches_ok", []))
    failed = len(run.get("matches_failed", []))
    value = run.get("value", {}) or {}
    fbref = run.get("fbref_form", {}) or {}
    ensemble = summary.get("ensemble", {})
    market = summary.get("market", {})
    kalshi = summary.get("kalshi", {})
    model = summary.get("model", {})
    whale = summary.get("whale", {})

    best_name = min(
        (name for name in ("market", "books", "kalshi", "model", "whale", "ensemble")
         if name in summary),
        key=lambda name: _score(summary, name, "mean_brier", 99.0),
        default="ensemble",
    )
    best = summary.get(best_name, {})
    roi = float(betting.get("roi_pct", 0.0) or 0.0)
    clv = float(betting.get("avg_clv_pct", 0.0) or 0.0)
    bets = int(betting.get("n_bets", 0) or 0)
    hit_rate = float(ensemble.get("hit_rate", 0.0) or 0.0) * 100.0
    ws = weights.get("suggested") or weights.get("weights") or {}
    ws_text = ", ".join(f"{k} {float(v):.3f}" for k, v in ws.items()) or "kein Vorschlag"
    param_note = param.get("note") or param.get("status") or "kein Parameter-Hinweis"

    narrative = (
        f"Der heutige Fallback-Hermes nutzt den deterministischen Snapshot {data.get('generated_at')}. "
        f"Der Daily-Lauf verarbeitete {ok} Spiele mit {failed} Fehlern; Value-Bets stehen bei "
        f"{value.get('n_value_bets', 0)} und Gesamtstake {value.get('total_stake_pct', 0.0)}%. "
        f"FBref-Form steht auf {fbref.get('status', 'unbekannt')}; alle Modell- und Staking-Parameter "
        "bleiben unveraendert.\n\n"
        f"Rollierend sind {n} Spiele aufgeloest. Beste Quelle nach Brier ist {best_name} mit "
        f"Brier/RPS/LogLoss {best.get('mean_brier')}/{best.get('mean_rps')}/{best.get('mean_log_loss')}. "
        f"Das Ensemble liegt bei {ensemble.get('mean_brier')}/{ensemble.get('mean_rps')}/"
        f"{ensemble.get('mean_log_loss')} und {hit_rate:.1f}% Trefferquote. Markt und Kalshi liegen bei "
        f"Brier {market.get('mean_brier')} bzw. {kalshi.get('mean_brier')}.\n\n"
        f"Das reine Modell bleibt mit Brier {model.get('mean_brier')} hinter dem Marktblock, Whale bleibt "
        f"mit LogLoss {whale.get('mean_log_loss')} hochvariant. Daraus folgt keine automatische Gewichts-, "
        "Parameter- oder Staking-Aenderung.\n\n"
        f"Die Referenz-Policy steht bei {bets} Wetten, ROI {roi:+.2f}% und durchschnittlichem CLV "
        f"{clv:+.2f}%. Das ist ein Beobachtungssignal, aber kein Freibrief, solange Ensemble-vs.-Markt "
        "nicht stabil positiv ist.\n\n"
        f"`weights_suggestion` wird nur notiert: {ws_text}. Parameter-Tuning bleibt Report-only "
        f"({param_note})."
    )
    learning = "\n".join([
        f"- [Beobachtung] {best_name} fuehrt rollierend bei n={n} mit Brier/RPS/LogLoss "
        f"{best.get('mean_brier')}/{best.get('mean_rps')}/{best.get('mean_log_loss')}; "
        f"Ensemble liegt bei {ensemble.get('mean_brier')}/{ensemble.get('mean_rps')}/"
        f"{ensemble.get('mean_log_loss')}.",
        f"- [Beobachtung] Daily verarbeitete {ok} Spiele mit {failed} Fehlern; Value-Bets "
        f"{value.get('n_value_bets', 0)}, Gesamtstake {value.get('total_stake_pct', 0.0)}%, "
        f"FBref-Status {fbref.get('status', 'unbekannt')}.",
        f"- [Hypothese] ROI {roi:+.2f}% und CLV {clv:+.2f}% sind noch kein stabiler Preis-Edge, "
        "solange Modell und Whale schlechter kalibriert sind als der Marktblock.",
        f"- [Aktion] `weights_suggestion` nur notieren ({ws_text}); keine Auto-Uebernahme von "
        "Modell-, Gewichts- oder Staking-Parametern.",
    ])
    return {"narrative": narrative, "learning": learning}


def main() -> int:
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    payload = build()
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if target:
        target.write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

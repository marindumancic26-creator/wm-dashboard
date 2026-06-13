"""Datenbasierte Ensemble-Gewichtsempfehlung aus der Kalibrierung.

Quant-Logik: Gewichte sollen die nachgewiesene Out-of-sample-Güte je Quelle
widerspiegeln, NICHT Bauchgefühl. Methode = Log-Opinion-Pooling-Schätzung:
  skill_i = exp(-β · mean_log_loss_i)   (besser kalibriert -> höheres Gewicht)
  w_i ∝ skill_i, dann **Shrinkage** Richtung Prior mit α = n/(n+K).

Bei kleiner Stichprobe (n < MIN_N) wird der Prior beibehalten — Schutz vor
Überanpassung. Die Empfehlung wird NICHT automatisch angewandt; sie erscheint im
Report/Dashboard, der Mensch entscheidet (und ab genug Daten kann der Prior in
config.ENSEMBLE_WEIGHTS nachgezogen werden).

WICHTIG (dokumentierte Schwäche): market/books/kalshi sind stark KORRELIERT (alle
'der Markt'). Reines Inverse-Loss-Weighting übergewichtet diesen Block. Daher als
Empfehlung mit Vorsicht behandeln; eine Block-Behandlung ist ein offener Punkt.
"""
from __future__ import annotations

import math

from src import config

SOURCES = ("market", "books", "kalshi", "model", "whale")
MIN_N = 8        # ab so vielen aufgelösten Spielen datenbasiert
SHRINK_K = 15    # Shrinkage-Konstante (n/(n+K) Richtung Prior)
BETA = 2.0       # Sensitivität Skill ~ LogLoss


def _prior() -> dict:
    p = {s: config.ENSEMBLE_WEIGHTS.get(s, 0.0) for s in SOURCES}
    z = sum(p.values()) or 1.0
    return {s: v / z for s, v in p.items()}


def suggest_weights(calib: dict) -> dict:
    prior = _prior()
    n = calib.get("n_resolved", 0)
    summary = calib.get("summary", {})
    avail = [s for s in SOURCES if s in summary and summary[s].get("mean_log_loss") is not None]

    if n < MIN_N or len(avail) < 2:
        return {"status": "prior", "n": n, "min_n": MIN_N,
                "weights": dict(config.ENSEMBLE_WEIGHTS), "prior": dict(config.ENSEMBLE_WEIGHTS),
                "note": f"n={n} < {MIN_N}: Prior beibehalten (kein Overfitting an Einzelspiele)."}

    skill = {s: math.exp(-BETA * summary[s]["mean_log_loss"]) for s in avail}
    z = sum(skill.values()) or 1.0
    raw = {s: skill[s] / z for s in avail}

    alpha = n / (n + SHRINK_K)
    sug = {}
    for s in SOURCES:
        r = raw.get(s, prior[s])
        sug[s] = alpha * r + (1 - alpha) * prior[s]
    zz = sum(sug.values()) or 1.0
    sug = {s: round(v / zz, 3) for s, v in sug.items()}

    return {"status": "data-driven", "n": n, "alpha": round(alpha, 2),
            "weights": sug, "prior": dict(config.ENSEMBLE_WEIGHTS),
            "note": (f"Inverse-LogLoss-Empfehlung, geshrunken (α={alpha:.2f}). "
                     "Markt/Bücher/Kalshi korreliert → Block mit Vorsicht. Nicht auto-angewandt.")}

"""Datenbasierte Ensemble-Gewichtsempfehlung aus der Kalibrierung.

Quant-Logik: Gewichte sollen die nachgewiesene Out-of-sample-Guete je Quelle
widerspiegeln, NICHT Bauchgefuehl. Methode = Log-Opinion-Pooling-Schaetzung:
  skill_i = exp(-beta * mean_log_loss_i)   (besser kalibriert -> hoeheres Gewicht)
  w_i proportional zu skill_i, dann Shrinkage Richtung Prior mit alpha = n/(n+K).

Bei kleiner Stichprobe (n < MIN_N) wird der Prior beibehalten - Schutz vor
Ueberanpassung. Die Empfehlung wird NICHT automatisch angewandt; sie erscheint im
Report/Dashboard, der Mensch entscheidet (und ab genug Daten kann der Prior in
config.ENSEMBLE_WEIGHTS nachgezogen werden).

WICHTIG: market/books/kalshi sind stark KORRELIERT (alle "der Markt"). Sie werden
daher als ein Marktblock gewertet, dessen Gewicht intern nach Einzel-Skill auf die
vorhandenen Block-Mitglieder verteilt wird.
"""
from __future__ import annotations

import math

from src import config

SOURCES = ("market", "books", "kalshi", "model", "whale")
MARKET_BLOCK = ("market", "books", "kalshi")
MIN_N = 8        # ab so vielen aufgeloesten Spielen datenbasiert
SHRINK_K = 15    # Shrinkage-Konstante (n/(n+K) Richtung Prior)
BETA = 2.0       # Sensitivitaet Skill ~ LogLoss


def _prior() -> dict:
    p = {s: config.ENSEMBLE_WEIGHTS.get(s, 0.0) for s in SOURCES}
    z = sum(p.values()) or 1.0
    return {s: v / z for s, v in p.items()}


def _skill(log_loss: float) -> float:
    return math.exp(-BETA * log_loss)


def _effective_prior(prior: dict, voices: tuple[str, ...]) -> dict:
    prior_eff = {}
    if "market_block" in voices:
        # Der Block-Prior ist config-basiert, aber de-korreliert: drei Marktquellen
        # duerfen nicht schon im Prior wie drei unabhaengige Stimmen zaehlen.
        prior_eff["market_block"] = sum(prior[s] for s in MARKET_BLOCK) / len(MARKET_BLOCK)
    for s in ("model", "whale"):
        if s in voices:
            prior_eff[s] = prior[s]
    z = sum(prior_eff.values()) or 1.0
    return {s: v / z for s, v in prior_eff.items()}


def _raw_block_weights(summary: dict, avail: list[str], prior: dict, alpha: float) -> dict:
    source_skill = {s: _skill(summary[s]["mean_log_loss"]) for s in avail}

    effective = {}
    block_members = [s for s in MARKET_BLOCK if s in source_skill]
    if block_members:
        block_log_loss = sum(summary[s]["mean_log_loss"] for s in block_members) / len(block_members)
        effective["market_block"] = _skill(block_log_loss)
    for s in ("model", "whale"):
        if s in source_skill:
            effective[s] = source_skill[s]

    z_eff = sum(effective.values()) or 1.0
    raw_effective = {s: v / z_eff for s, v in effective.items()}
    prior_effective = _effective_prior(prior, tuple(raw_effective))
    effective_weights = {s: alpha * raw_effective[s] + (1 - alpha) * prior_effective[s]
                         for s in raw_effective}

    raw = {}
    if block_members:
        z_block = sum(source_skill[s] for s in block_members) or 1.0
        for s in block_members:
            raw[s] = effective_weights["market_block"] * source_skill[s] / z_block
    for s in ("model", "whale"):
        if s in effective_weights:
            raw[s] = effective_weights[s]
    return raw


def suggest_weights(calib: dict) -> dict:
    prior = _prior()
    n = calib.get("n_resolved", 0)
    summary = calib.get("summary", {})
    avail = [s for s in SOURCES if s in summary and summary[s].get("mean_log_loss") is not None]

    effective_voice_count = int(any(s in avail for s in MARKET_BLOCK))
    effective_voice_count += sum(1 for s in ("model", "whale") if s in avail)

    if n < MIN_N or effective_voice_count < 2:
        return {"status": "prior", "n": n, "min_n": MIN_N,
                "weights": dict(config.ENSEMBLE_WEIGHTS), "prior": dict(config.ENSEMBLE_WEIGHTS),
                "note": f"n={n} < {MIN_N}: Prior beibehalten (kein Overfitting an Einzelspiele)."}

    alpha = n / (n + SHRINK_K)
    sug = _raw_block_weights(summary, avail, prior, alpha)
    zz = sum(sug.values()) or 1.0
    sug = {s: round(v / zz, 3) for s, v in sug.items()}

    return {"status": "data-driven", "n": n, "alpha": round(alpha, 2),
            "weights": sug, "prior": dict(config.ENSEMBLE_WEIGHTS),
            "note": (f"Inverse-LogLoss-Empfehlung, geshrunken (alpha={alpha:.2f}). "
                     "Markt/Books/Kalshi korreliert -> Markt-Block als eine effektive Stimme. "
                     "Nicht auto-angewandt.")}

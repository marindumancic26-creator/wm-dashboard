"""Gemeinsamer, streng diagnostischer Club-Modellpfad.

Die bewährten Backtest-Funktionen werden wiederverwendet. Dieses Modul kann
keine Produktionsfreigabe erteilen und wird nicht als Site-Prognose angezeigt.
"""
from __future__ import annotations

import datetime as dt

from src.model import club_backtest


def diagnostic_forecast(history: list[dict], home: str, away: str, as_of: dt.datetime,
                        *, rho: float = -0.10, half_life_days: int = 365) -> dict:
    if as_of.tzinfo is None:
        raise ValueError("as_of braucht eine Zeitzone")
    # Ohne belegte Resultatverfügbarkeit werden auch Spiele desselben Datums ausgeschlossen.
    day = as_of.astimezone(dt.timezone.utc).date()
    train = []
    for row in history:
        try:
            played = dt.date.fromisoformat(str(row["date"])[:10])
            if played >= day:
                continue
            if row.get("result_available_at"):
                available = dt.datetime.fromisoformat(row["result_available_at"].replace("Z", "+00:00"))
                if available.tzinfo is None or available >= as_of:
                    continue
            if min(row["home_score"], row["away_score"]) < 0:
                continue
            train.append(row)
        except (ValueError, KeyError, TypeError):
            continue
    base = {"prediction_allowed": False, "value_allowed": False,
            "n_train": len(train), "as_of": as_of.isoformat(), "model_version": "club-dc-diagnostic-v1"}
    if len(train) < club_backtest.MIN_TRAIN_MATCHES:
        return {**base, "status": "insufficient_data"}
    teams = {m["home_team"] for m in train} | {m["away_team"] for m in train}
    if home not in teams or away not in teams:
        return {**base, "status": "unknown_team"}
    fit = club_backtest._decayed_fit(train, day.isoformat(), half_life_days)
    probs, lam_h, lam_a = club_backtest._predict_from_fit(fit, home, away, rho)
    return {**base, "status": "diagnostic", "diagnostic_probs": probs,
            "lambda_home": lam_h, "lambda_away": lam_a,
            "note": "Keine Freigabe; bestehende Walk-forward- und Lockbox-Gates gelten unverändert."}

"""K.o.-Weiterkommen: Verlängerung + Elfmeterschießen.

In der K.o.-Phase prognostizieren Modell und Polymarket-Match-Markt das 90-Minuten-1X2.
„Wer kommt weiter" braucht zusätzlich Verlängerung (30 min) und ggf. Elfmeterschießen:

  P(Team1 weiter) = P(Sieg in 90) + P(Remis in 90) · P(Team1 gewinnt den Rest)
  P(Team1 gewinnt den Rest) = P(Sieg in Verlängerung) + P(Remis in Verläng.) · P(Pens)

Annahmen (klar gelabelt):
  - Verlängerung = 1/3 der 90-Minuten-Tor-Erwartung (30/90), gleiche Stärkeverhältnisse.
  - Elfmeterschießen ≈ 50/50. Studien zeigen ein nahezu zufälliges Ergebnis; ein kleiner
    Vorteil (Erstschütze/Favorit) ist nicht robust belegt -> bewusst 0.5 (konfigurierbar).
Nur für K.o.-Spiele relevant; in der Gruppenphase wird diese Funktion nicht aufgerufen.
"""
from __future__ import annotations

from src.model import features

PENALTY_PROB = 0.5  # near-random; bewusst neutral


def advancement_probs(lam1: float, lam2: float, p1_90: float, pd_90: float, p2_90: float,
                      penalty_prob: float = PENALTY_PROB, rho: float | None = None) -> dict:
    """Weiterkommen-Wahrscheinlichkeiten aus 90-Minuten-1X2 + Verlängerung + Elfmeter."""
    # Verlängerung: 30 min -> Tor-Erwartung ~1/3 der 90-Minuten-Lambdas
    et1, etd, et2 = features.poisson_1x2(lam1 / 3.0, lam2 / 3.0, rho=rho)
    p1_rest = et1 + etd * penalty_prob
    p2_rest = et2 + etd * (1.0 - penalty_prob)
    adv1 = p1_90 + pd_90 * p1_rest
    adv2 = p2_90 + pd_90 * p2_rest
    s = adv1 + adv2 or 1.0
    return {
        "team1_advance": round(adv1 / s, 4),
        "team2_advance": round(adv2 / s, 4),
        "extra_time_1x2": {"team1": round(et1, 4), "draw": round(etd, 4), "team2": round(et2, 4)},
        "penalty_prob_team1": penalty_prob,
        "note": "90-Min-1X2 + Verlängerung (1/3 Tor-Erwartung) + Elfmeter (~50/50, geschätzt).",
    }

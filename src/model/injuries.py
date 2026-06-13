"""Manuelles Verletzungs-/Aufstellungs-Override.

ESPN liefert Aufstellungen erst ~1h vor Anpfiff und ohne Spieler-Stärkewerte — eine
automatische Modellierung wäre Scheinpräzision. Stattdessen ein transparentes manuelles
Override: in data/processed/adjustments.json trägt der Nutzer (oder Claude on demand)
bekannte Ausfälle als λ-Multiplikatoren ein. Beispiel:

  {
    "fifwc-bra-mar-2026-06-13": {
      "team1_mult": 0.90, "team2_mult": 1.0, "total_mult": 0.97,
      "note": "Brasilien ohne Stürmer X (verletzt)", "source": "manuell 13.06."
    }
  }

team1_mult < 1 schwächt Team 1 (weniger erwartete Tore). Gekappt in injuries_apply().
"""
from __future__ import annotations

import json

from src import config

_FILE = config.DATA_PROCESSED / "adjustments.json"


def load_overrides() -> dict:
    if _FILE.exists():
        try:
            return json.loads(_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def apply(ctx: dict, ov: dict) -> dict:
    """Faltet die Override-Multiplikatoren in den Spielort-Kontext (gekappt)."""
    ctx = dict(ctx)
    t1 = max(0.7, min(1.3, float(ov.get("team1_mult", 1.0))))
    t2 = max(0.7, min(1.3, float(ov.get("team2_mult", 1.0))))
    tm = max(0.8, min(1.2, float(ov.get("total_mult", 1.0))))
    ctx["team1_mult"] = ctx.get("team1_mult", 1.0) * t1
    ctx["team2_mult"] = ctx.get("team2_mult", 1.0) * t2
    ctx["total_goals_mult"] = round(max(0.85, min(1.15,
                                    ctx.get("total_goals_mult", 1.0) * tm)), 4)
    ctx.setdefault("notes", []).append("Override: " + ov.get("note", ""))
    ctx["injury_override"] = {"team1_mult": t1, "team2_mult": t2, "total_mult": tm,
                              "note": ov.get("note", ""), "source": ov.get("source", "manuell")}
    return ctx

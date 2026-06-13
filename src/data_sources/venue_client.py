"""Spielort-Kontext: Höhe (statisch) + Wetter (OpenWeather, optional).

Höhe ist ein schwacher, aber belegbarer Faktor: hohe Lagen (Mexiko-Stadt 2240 m)
ermüden nicht-akklimatisierte Teams und erhöhen tendenziell die Torvarianz; Teams aus
Höhen-Nationen profitieren leicht. Wetter (starker Wind/Regen) dämpft Tore leicht.

Alle Effekte sind klein und gekappt — als 'estimated' gelabelt, kein Overclaim.
Ohne OpenWeather-Key läuft Wetter als 'unavailable'.
"""
from __future__ import annotations

import datetime as dt

import requests

from src import config

# WC-2026-Spielorte: Stadt-Stichwort -> (Höhe m, lat, lon)
VENUES = {
    "mexico city": (2240, 19.30, -99.15), "guadalajara": (1566, 20.68, -103.46),
    "monterrey": (540, 25.67, -100.31), "guadalupe": (540, 25.67, -100.24),
    "atlanta": (320, 33.75, -84.40),
    "kansas city": (270, 39.05, -94.48), "dallas": (180, 32.75, -97.09),
    "arlington": (180, 32.75, -97.09), "houston": (15, 29.68, -95.41),
    "los angeles": (30, 33.95, -118.34), "inglewood": (30, 33.95, -118.34),
    "miami": (2, 25.96, -80.24), "east rutherford": (2, 40.81, -74.07),
    "new york": (2, 40.81, -74.07), "philadelphia": (3, 39.90, -75.17),
    "santa clara": (3, 37.40, -121.97), "san francisco": (3, 37.40, -121.97),
    "seattle": (5, 47.59, -122.33), "toronto": (76, 43.63, -79.42),
    "vancouver": (0, 49.28, -123.11), "boston": (30, 42.09, -71.26),
    "foxborough": (30, 42.09, -71.26),
}

# Nationen mit Höhen-Heimstärke (leichte Akklimatisierungs-Boni bei Höhenspielen)
ALTITUDE_NATIONS = {"Mexico", "Bolivia", "Ecuador", "Colombia", "Peru", "Iran"}


def _lookup(city: str):
    if not city:
        return None
    c = city.lower().strip()
    for key, v in VENUES.items():
        if key in c or c in key:
            return v
    return None


def get_context(city: str, team1: str, team2: str, kickoff_utc: str | None = None) -> dict:
    """Höhen- + (optional) Wetter-Kontext + abgeleitete Modell-Adjustierungen.

    Rückgabe enthält:
      total_goals_mult : Multiplikator auf Gesamttor-Baseline [0.9..1.08]
      team1_alt_bonus / team2_alt_bonus : kleiner λ-Multiplikator für Höhen-Nationen
    """
    out = {"city": city, "altitude_m": None, "weather": None,
           "total_goals_mult": 1.0, "team1_mult": 1.0, "team2_mult": 1.0,
           "status": "estimated", "notes": []}
    v = _lookup(city)
    if not v:
        out["status"] = "unavailable"
        out["notes"].append("Spielort nicht zugeordnet" if city else "kein Spielort (ESPN)")
        return out
    alt, lat, lon = v
    out["altitude_m"] = alt

    # Höhen-Effekt: erst ab ~1500 m spürbar, gekappt
    if alt > 1500:
        bump = min(0.06, (alt - 1500) / 20000.0)  # 2240 m -> +3.7%
        out["total_goals_mult"] *= (1.0 + bump)
        out["notes"].append(f"Höhe {alt} m → +{bump*100:.1f}% Tore (geschätzt)")
        # Akklimatisierungs-Bonus für Höhen-Nationen
        if config.canonical_team(team1) in ALTITUDE_NATIONS:
            out["team1_mult"] = 1.06
            out["notes"].append(f"{team1} höhenadaptiert (+6% λ)")
        if config.canonical_team(team2) in ALTITUDE_NATIONS:
            out["team2_mult"] = 1.06
            out["notes"].append(f"{team2} höhenadaptiert (+6% λ)")

    # Wetter (optional)
    if config.OPENWEATHER_KEY:
        w = _fetch_weather(lat, lon, kickoff_utc)
        if w:
            out["weather"] = w
            out["status"] = "live"
            # Starker Wind/Regen dämpft Tore leicht
            mult = 1.0
            if w.get("wind_kmh", 0) > 35:
                mult *= 0.97
                out["notes"].append("starker Wind → leicht weniger Tore")
            if w.get("rain", False):
                mult *= 0.98
                out["notes"].append("Regen → leicht weniger Tore")
            out["total_goals_mult"] *= mult
    else:
        out["notes"].append("Wetter: kein OpenWeather-Key")

    out["total_goals_mult"] = round(max(0.9, min(1.08, out["total_goals_mult"])), 4)
    return out


def _fetch_weather(lat: float, lon: float, kickoff_utc: str | None) -> dict | None:
    """Aktuelle/Forecast-Bedingungen via OpenWeather (free current weather)."""
    try:
        r = requests.get("https://api.openweathermap.org/data/2.5/weather",
                         params={"lat": lat, "lon": lon, "appid": config.OPENWEATHER_KEY,
                                 "units": "metric"}, timeout=15)
        r.raise_for_status()
        d = r.json()
        return {"temp_c": d.get("main", {}).get("temp"),
                "wind_kmh": round((d.get("wind", {}).get("speed") or 0) * 3.6, 1),
                "rain": "rain" in d, "desc": (d.get("weather") or [{}])[0].get("description"),
                "fetched_at": dt.datetime.now().isoformat(timespec="seconds")}
    except Exception:
        return None

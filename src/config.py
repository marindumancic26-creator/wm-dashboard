"""Zentrale Konfiguration: Pfade, Modellgewichte, Team-Referenzdaten."""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_SNAPSHOTS = PROJECT_ROOT / "data" / "snapshots"
MEMORY_DIR = PROJECT_ROOT / "memory"
DAILY_RUNS_DIR = MEMORY_DIR / "daily_runs"
MATCHES_DIR = MEMORY_DIR / "matches"

for p in (DATA_RAW, DATA_PROCESSED, DATA_SNAPSHOTS, DAILY_RUNS_DIR, MATCHES_DIR):
    p.mkdir(parents=True, exist_ok=True)

# StatsBomb API-Credentials (kostenpflichtig). Wenn nicht gesetzt -> Open-Data-Fallback.
STATSBOMB_USER = os.environ.get("SB_USERNAME") or os.environ.get("STATSBOMB_USERNAME")
STATSBOMB_PASS = os.environ.get("SB_PASSWORD") or os.environ.get("STATSBOMB_PASSWORD")
STATSBOMB_API_AVAILABLE = bool(STATSBOMB_USER and STATSBOMB_PASS)

# API-Keys: Umgebungsvariable hat Vorrang, sonst api_keys.json im Projektroot
# (Format: {"odds_api": "...", "football_data": "..."}). Beide Dienste haben
# kostenlose Tiers: the-odds-api.com, football-data.org.
def _load_key(env_name: str, json_key: str):
    val = os.environ.get(env_name)
    if val:
        return val
    f = PROJECT_ROOT / "api_keys.json"
    if f.exists():
        try:
            import json as _json
            return _json.loads(f.read_text(encoding="utf-8")).get(json_key)
        except Exception:
            return None
    return None

ODDS_API_KEY = _load_key("ODDS_API_KEY", "odds_api")
FOOTBALL_DATA_KEY = _load_key("FOOTBALL_DATA_API_KEY", "football_data")
OPENWEATHER_KEY = _load_key("OPENWEATHER_API_KEY", "openweather")  # optional, free tier
ODDS_API_BASE = "https://api.the-odds-api.com/v4"
FOOTBALL_DATA_BASE = "https://api.football-data.org/v4"

# Ensemble-Default-Gewichte. Buchmacher (Pinnacle & Co.) gelten als schaerfste
# Quelle; ohne Odds-API-Key wird "books" automatisch renormalisiert weggelassen.
ENSEMBLE_WEIGHTS = {"market": 0.30, "books": 0.25, "kalshi": 0.10, "model": 0.20, "whale": 0.15}

# Monte-Carlo
MC_RUNS = 20000
MC_PARAM_UNCERTAINTY = 0.12  # relative Streuung der Tor-Erwartungswerte (Gamma-Sampling)
MAX_GOALS = 8                # Abschneidegrenze fuer Scoreline-Matrix

# Dixon-Coles-Korrektur fuer niedrige Ergebnisse: hebt 0:0/1:1 an, senkt 1:0/0:1.
# rho < 0 korrigiert die bekannte Remis-Unterschaetzung der unabhaengigen Poisson.
# Standard-Literaturwert ~ -0.10; bei rho=0 faellt die Korrektur weg (reine Poisson).
DIXON_COLES_RHO = -0.10

# Elo-Punkte je Tor Supremacy: GD_erwartet = (Elo1-Elo2)/ELO_PER_GOAL.
# Ersetzt den (w/(1-w))^0.7-Hack durch ein direktes Tordifferenz-Modell.
# 240 gegen den Markt kalibriert (tests/tune_elo.py, Slate 13.06.): minimiert
# L1-Abweichung Modell-vs-Markt. Klein kalibriert -> bei mehr Spielen nachjustieren.
ELO_PER_GOAL = 240.0

# Durchschnittliche Tore pro WM-Gruppenspiel (WM 1998-2022, FIFA-Statistik; statisch, geschaetzt)
BASELINE_TOTAL_GOALS = 2.6

# Lokaler Klon von github.com/statsbomb/open-data (optional, fuer Event-Level-xG).
# Liegt bewusst AUSSERHALB von OneDrive (Sync-Last). Override per Umgebungsvariable.
OPEN_DATA_DIR = Path(os.environ.get("STATSBOMB_OPEN_DATA_DIR",
                                    r"C:\Users\marin\statsbomb-open-data")) / "data"

# Polymarket
GAMMA_API = "https://gamma-api.polymarket.com"
DATA_API = "https://data-api.polymarket.com"
MATCH_SLUG_PREFIX = "fifwc-"

# Whale-Scoring: Shrinkage-Konstante — Wallet braucht ~ K abgeschlossene Trades,
# um halbes Vertrauen zu erhalten (verhindert Uebergewichtung kleiner Stichproben).
WHALE_SHRINKAGE_K = 25
WHALE_TOP_HOLDERS = 12
WHALE_RECENT_TRADES = 200

# Elo-Ratings (Quelle: eloratings.net, statischer Snapshot ~Anfang Juni 2026,
# teilweise geschaetzt/gerundet — Status: "estimated"). Wird nur als Prior genutzt;
# Marktpreise korrigieren systematische Fehler dieses Snapshots.
ELO_SNAPSHOT_DATE = "2026-06-01"
ELO_RATINGS = {
    "Argentina": 2150, "France": 2090, "Spain": 2105, "England": 2055, "Brazil": 2030,
    "Portugal": 2010, "Netherlands": 1990, "Belgium": 1935, "Germany": 1945, "Croatia": 1900,
    "Italy": 1915, "Uruguay": 1925, "Colombia": 1930, "Morocco": 1885, "Japan": 1880,
    "United States": 1790, "USA": 1790, "Mexico": 1810, "Canada": 1770, "Switzerland": 1865,
    "Denmark": 1850, "Ecuador": 1870, "Senegal": 1830, "Iran": 1800, "South Korea": 1780,
    "Australia": 1760, "Austria": 1820, "Turkey": 1800, "Türkiye": 1800, "Ukraine": 1790,
    "Poland": 1780, "Serbia": 1770, "Wales": 1720, "Scotland": 1750, "Norway": 1850,
    "Sweden": 1760, "Peru": 1760, "Chile": 1740, "Paraguay": 1770, "Venezuela": 1720,
    "Bosnia and Herzegovina": 1700, "Bosnia-Herzegovina": 1700, "Algeria": 1780,
    "Egypt": 1740, "Nigeria": 1750, "Ghana": 1690, "Cameroon": 1720, "Tunisia": 1720,
    "Ivory Coast": 1760, "Costa Rica": 1660, "Panama": 1680, "Jamaica": 1640,
    "Saudi Arabia": 1660, "Qatar": 1640, "Uzbekistan": 1680, "Jordan": 1650,
    "Iraq": 1640, "UAE": 1620, "New Zealand": 1590, "Honduras": 1610,
    "Haiti": 1540, "Curacao": 1560, "Cape Verde": 1620, "South Africa": 1680,
}
ELO_DEFAULT = 1650  # Fallback fuer Teams ohne Eintrag

# Kanonische Teamnamen: Polymarket/Buchmacher/FIFA-Schreibweisen -> unsere Namen
NAME_ALIASES = {
    "Türkiye": "Turkey", "Turkiye": "Turkey",
    "Korea Republic": "South Korea", "Republic of Korea": "South Korea",
    "Côte d'Ivoire": "Ivory Coast", "Cote d'Ivoire": "Ivory Coast",
    "Bosnia-Herzegovina": "Bosnia and Herzegovina",
    "USA": "United States", "IR Iran": "Iran", "Czechia": "Czech Republic",
    "Curaçao": "Curacao", "UAE": "UAE", "United Arab Emirates": "UAE",
}

def canonical_team(name: str) -> str:
    if not name:                       # None/leer aus einer Datenquelle -> nicht crashen
        return ""
    return NAME_ALIASES.get(name.strip(), name.strip())


_KNOWN_TEAMS_LOWER: set | None = None

def known_team_names_lower() -> set:
    """Menge aller bekannten kanonischen Teamnamen (lowercase) — aus ELO_RATINGS-Keys
    (kanonisiert) und den Polymarket-Codes. Dient dem Substring-Matching als Sicherung:
    zwei VERSCHIEDENE bekannte Teams duerfen sich nie per Teilzeichenkette treffen."""
    global _KNOWN_TEAMS_LOWER
    if _KNOWN_TEAMS_LOWER is None:
        names = {canonical_team(k) for k in ELO_RATINGS} | set(TEAM_CODES.values())
        _KNOWN_TEAMS_LOWER = {n.lower() for n in names}
    return _KNOWN_TEAMS_LOWER

# Polymarket-Team-Codes (Slug-Kuerzel -> Klarname), fuer Slug-Parsing
TEAM_CODES = {
    "usa": "United States", "par": "Paraguay", "can": "Canada", "bih": "Bosnia and Herzegovina",
    "qat": "Qatar", "sui": "Switzerland", "che": "Switzerland", "bra": "Brazil", "mar": "Morocco",
    "hai": "Haiti", "sco": "Scotland", "aus": "Australia", "tur": "Turkey",
    "mex": "Mexico", "kor": "South Korea", "arg": "Argentina", "fra": "France",
    "esp": "Spain", "eng": "England", "ger": "Germany", "por": "Portugal",
    "ned": "Netherlands", "bel": "Belgium", "cro": "Croatia", "ita": "Italy",
    "uru": "Uruguay", "col": "Colombia", "jpn": "Japan", "sen": "Senegal",
    "irn": "Iran", "ecu": "Ecuador", "den": "Denmark", "nor": "Norway",
    "aut": "Austria", "ukr": "Ukraine", "pol": "Poland", "alg": "Algeria",
    "egy": "Egypt", "nga": "Nigeria", "civ": "Ivory Coast", "tun": "Tunisia",
    "ksa": "Saudi Arabia", "uzb": "Uzbekistan", "jor": "Jordan", "rsa": "South Africa",
    "pan": "Panama", "crc": "Costa Rica", "jam": "Jamaica", "nzl": "New Zealand",
    "cuw": "Curacao", "cpv": "Cape Verde", "hon": "Honduras", "uae": "UAE",
    "nld": "Netherlands", "swe": "Sweden", "deu": "Germany", "prt": "Portugal",
}

# Modell-Version: Fingerprint der entscheidenden Parameter. Aendert sich der
# Fingerprint, ist die Kalibrierung quellenuebergreifend nicht mehr 1:1 vergleichbar.
import hashlib as _hashlib

def _model_version() -> str:
    fp = f"ens={ENSEMBLE_WEIGHTS}|dc={DIXON_COLES_RHO}|base={BASELINE_TOTAL_GOALS}|cv={MC_PARAM_UNCERTAINTY}"
    h = _hashlib.sha1(fp.encode()).hexdigest()[:8]
    return f"m-{h}"

MODEL_VERSION = _model_version()

"""Tunt ELO_PER_GOAL gegen den Markt (bester Wahrheits-Proxy) auf dem aktuellen Slate."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import config
from src.data_sources import statsbomb_client as sb, elo_client
from src.model import features

data = json.loads((config.DATA_PROCESSED / "dashboard_data.json").read_text(encoding="utf-8"))
profiles = sb.get_team_profiles()
elo = elo_client.get_ratings()
games = [(m["team1"], m["team2"], m["market"]["probs"]) for m in data["matches"] if m.get("market")]

for c in (120, 150, 180, 210, 240, 280, 320):
    config.ELO_PER_GOAL = float(c)
    err = 0.0
    for t1, t2, mkt in games:
        mdl = features.attack_defense_lambdas(t1, t2, profiles, elo, form=None)["probs"]
        err += sum(abs(mdl[k] - mkt[k]) for k in ("team1_win", "draw", "team2_win"))
    print(f"ELO_PER_GOAL={c:>4}: mittl. L1-Fehler/Spiel = {err/len(games):.4f}")

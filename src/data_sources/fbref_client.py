"""FBref-Turnierform via soccerdata (Cloudflare-Umgehung per Headless-Browser).

Liefert die IN-TURNIER-Form der WM 2026: Tore fuer/gegen pro gespieltem Spiel,
plus xG sobald FBref die Spalten fuer dieses Turnier fuellt (Stand 13.06.2026:
noch keine xG-Spalten -> tor-basiert, automatisches Upgrade).

Teuer (~30-60 s Browser-Start) -> Cache 20 h, Fehler niemals fatal.
"""
from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

from src import config

_CACHE = config.DATA_RAW / "fbref_form.json"
_CACHE_TTL = 20 * 3600
_FETCH_TIMEOUT = 180


def _unavailable(note: str) -> dict:
    return {"status": "unavailable", "teams": {}, "note": note}


def _fetch_live_payload() -> dict:
    """FBref im Worker laden; darf niemals direkt im Daily-Prozess laufen."""
    try:
        import soccerdata as sd
        fb = sd.FBref(leagues="INT-World Cup", seasons="2026")
        df = fb.read_schedule().reset_index()
    except Exception as exc:
        return _unavailable(f"FBref/soccerdata-Fehler: {exc}")

    has_xg = "home_xg" in df.columns and "away_xg" in df.columns
    agg: dict[str, dict] = {}
    for _, row in df.iterrows():
        score = row.get("score")
        if score is None or (isinstance(score, float)) or not str(score).strip() or str(score) == "<NA>":
            continue
        # Score-Format "2–1" (en-dash) oder "2-1"
        s = str(score).replace("–", "-").replace("—", "-")
        parts = s.split("-")
        if len(parts) != 2 or not parts[0].strip().isdigit():
            continue
        hg, ag = int(parts[0]), int(parts[1])
        home = config.canonical_team(str(row["home_team"]))
        away = config.canonical_team(str(row["away_team"]))
        for team, gf, ga, xg, xga in (
            (home, hg, ag, row.get("home_xg") if has_xg else None, row.get("away_xg") if has_xg else None),
            (away, ag, hg, row.get("away_xg") if has_xg else None, row.get("home_xg") if has_xg else None),
        ):
            a = agg.setdefault(team, {"matches": 0, "gf": 0, "ga": 0, "xg": 0.0, "xga": 0.0, "n_xg": 0})
            a["matches"] += 1
            a["gf"] += gf
            a["ga"] += ga
            try:
                if xg is not None and str(xg) != "<NA>":
                    a["xg"] += float(xg)
                    a["xga"] += float(xga)
                    a["n_xg"] += 1
            except Exception:
                pass

    teams = {}
    for t, a in agg.items():
        n = a["matches"]
        entry = {"matches": n, "gf_pm": round(a["gf"] / n, 3), "ga_pm": round(a["ga"] / n, 3)}
        if a["n_xg"]:
            entry["xg_pm"] = round(a["xg"] / a["n_xg"], 3)
            entry["xga_pm"] = round(a["xga"] / a["n_xg"], 3)
        teams[t] = entry

    payload = {"status": "live", "teams": teams,
               "xg_available": has_xg and any("xg_pm" in v for v in teams.values()),
               "note": "In-Turnier-Form WM 2026 (FBref); xG sobald von FBref gefuellt.",
               "as_of": dt.datetime.now().isoformat(timespec="seconds")}
    return payload


def _run_isolated_fetch(timeout: int = _FETCH_TIMEOUT) -> dict:
    """soccerdata mit eigener Prozessgruppe ausfuehren.

    Chromium-/soccerdata-Abbrueche koennen unter Windows Ctrl+C an ihre
    Prozessgruppe senden. Die Isolation verhindert, dass dabei der Daily-Runner
    und damit Export, Commit und Push beendet werden.
    """
    config.DATA_RAW.mkdir(parents=True, exist_ok=True)
    fd, output_name = tempfile.mkstemp(prefix="fbref_worker_", suffix=".json",
                                       dir=config.DATA_RAW)
    os.close(fd)
    output_path = Path(output_name)
    output_path.unlink(missing_ok=True)
    command = [sys.executable, "-m", "src.data_sources.fbref_client",
               "--worker", str(output_path)]
    kwargs = {
        "cwd": str(config.PROJECT_ROOT),
        "timeout": timeout,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.PIPE,
        "text": True,
        "check": False,
    }
    if os.name == "nt":
        kwargs["creationflags"] = (subprocess.CREATE_NEW_PROCESS_GROUP |
                                   subprocess.CREATE_NO_WINDOW)
    try:
        completed = subprocess.run(command, **kwargs)
        if output_path.exists():
            return json.loads(output_path.read_text(encoding="utf-8"))
        detail = (completed.stderr or "").strip().splitlines()
        suffix = f": {detail[-1]}" if detail else ""
        return _unavailable(
            f"FBref-Worker beendet (Exit {completed.returncode}){suffix}")
    except subprocess.TimeoutExpired:
        return _unavailable(f"FBref-Worker Timeout nach {timeout} Sekunden")
    except Exception as exc:
        return _unavailable(f"FBref-Worker-Fehler: {exc}")
    finally:
        output_path.unlink(missing_ok=True)


def get_tournament_form(force: bool = False) -> dict:
    """{"status", "teams": {name: {matches, gf_pm, ga_pm[, xg_pm, xga_pm]}}, ...}"""
    if not force and _CACHE.exists() and (time.time() - _CACHE.stat().st_mtime) < _CACHE_TTL:
        try:
            return json.loads(_CACHE.read_text(encoding="utf-8"))
        except Exception:
            pass
    payload = _run_isolated_fetch()
    if payload.get("status") == "live":
        _CACHE.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    return payload


def _worker(output_path: str) -> int:
    payload = _fetch_live_payload()
    Path(output_path).write_text(
        json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


def form_factor(team: str, form: dict) -> dict | None:
    """Gedaempfter Angriffs-/Abwehr-Faktor aus der Turnierform.
    Gewicht n/(n+3): 1 Spiel zaehlt 25 %, 3 Spiele 50 %. Kappung ±25 %."""
    t = form.get("teams", {}).get(config.canonical_team(team))
    if not t or t["matches"] < 1:
        return None
    AVG = 1.3
    atk_raw = (t.get("xg_pm") or t["gf_pm"]) / AVG
    dfn_raw = (t.get("xga_pm") or t["ga_pm"]) / AVG
    w = t["matches"] / (t["matches"] + 3)
    atk = 1.0 + w * (max(0.5, min(2.0, atk_raw)) - 1.0)
    dfn = 1.0 + w * (max(0.5, min(2.0, dfn_raw)) - 1.0)
    return {"attack": round(max(0.75, min(1.25, atk)), 3),
            "concede": round(max(0.75, min(1.25, dfn)), 3),
            "matches": t["matches"], "basis": "xg" if t.get("xg_pm") else "goals"}


if __name__ == "__main__" and len(sys.argv) == 3 and sys.argv[1] == "--worker":
    raise SystemExit(_worker(sys.argv[2]))

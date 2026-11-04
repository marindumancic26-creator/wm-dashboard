"""Budgetierter Club-Lauf für Sites; erzeugt keine produktiven WM-Dateien.

Secrets kommen aus der Umgebung oder einmalig über stdin, nie aus CLI-Argumenten.
Ein Slot wird vor Providerzugriff dauerhaft beansprucht. Ein unsicherer Abruf wird
nicht wiederholt; der reservierte Verbrauch bleibt konservativ verbucht.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import sys
import time
from urllib.parse import urlparse

import requests

from src.pipeline.club_sites_policy import (
    BERLIN, COMPETITIONS, budget_capacity, eligible_competitions, next_update, scheduled_slot,
)


class SiteStore:
    def __init__(self, url: str, secret: str, bypass: str):
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.hostname or not parsed.hostname.endswith(".chatgpt.site"):
            raise ValueError("Sites-Ziel muss eine HTTPS-chatgpt.site-Adresse sein")
        if not secret or not bypass:
            raise ValueError("Sites-Maschinenzugang fehlt")
        self.url = url.rstrip("/")
        self.headers = {"Authorization": f"Bearer {secret}",
                        "OAI-Sites-Authorization": f"Bearer {bypass}",
                        "Content-Type": "application/json"}

    def request(self, method, path, payload=None):
        response = requests.request(method, self.url + path, headers=self.headers,
                                    json=payload, timeout=60, allow_redirects=False)
        if response.status_code != 200:
            raise RuntimeError(f"Sites-Aufruf fehlgeschlagen (HTTP {response.status_code})")
        return response.json()

    def claim(self, slot):
        return self.request("POST", "/api/internal/state", {"operation": "claim", "slot": slot})["claimed"]

    def observe(self, quota):
        return self.request("POST", "/api/internal/state", {"operation": "observe", **quota})

    def reserve(self, slot, competition):
        return self.request("POST", "/api/internal/reservations", {"slot": slot, "competition": competition})

    def state(self):
        return self.request("GET", "/api/internal/state")

    def upload(self, payload):
        for attempt in range(3):
            try:
                return self.request("POST", "/api/internal/runs", payload)
            except (requests.RequestException, RuntimeError):
                if attempt == 2:
                    raise RuntimeError("Run-Upload fehlgeschlagen; lokaler Pending-Stand bleibt erhalten") from None
                time.sleep(attempt + 1)


def collect(fixture_payload: dict, now: dt.datetime, odds, store,
            slot_override: str | None = None) -> dict | None:
    from src.competition_registry import COMPETITIONS as registry
    from src.data_sources.club_odds_client import find_event, normalize_event

    slot = slot_override or scheduled_slot(now)
    if not slot or not store.claim(slot):
        return None
    captured = now.astimezone(dt.timezone.utc).isoformat(timespec="seconds")
    sources, raw_fixtures, matches = {}, [], []
    for key in COMPETITIONS:
        source = fixture_payload.get("competitions", {}).get(key) or {}
        status = source.get("status", "unavailable")
        sources[key] = {"status": status if status in ("live", "stale", "degraded") else "unavailable",
                        "source": source.get("source") or "football_data", "fetched_at": captured}
        if source.get("status") != "live":
            sources[key]["note"] = "Spielplanquelle derzeit nicht vollständig verfügbar."
        for f in source.get("fixtures", []):
            if not f.get("provider_match_id") or not f.get("kickoff_utc"):
                continue
            raw_fixtures.append({**f, "competition": key})
            matches.append({
                "id": f.get("match_id") or f"provider:{key}:{f['provider_match_id']}",
                "competition": key, "kickoff_utc": f["kickoff_utc"],
                "home": f.get("home", {}).get("name") or "", "away": f.get("away", {}).get("name") or "",
                "fixture_status": f.get("status") or "scheduled",
                "identity_status": f.get("identity_status", "pending"),
                "fixture_fetched_at": source.get("source_captured_at") or captured,
                "quotes": [], "market_probs": None, "model": None,
                "prediction_allowed": False, "value_allowed": False,
                "odds_status": "not_due", "blockers": f.get("blockers", []),
            })

    observed = odds.probe()
    quota = {"status": "unknown", "remaining": None, "used": None}
    remaining = None
    if observed:
        state = store.observe(observed)
        remaining = state["quota"]["remaining"]
        quota = {"status": "verified", "remaining": remaining, "used": state["quota"]["used"]}
    eligible = eligible_competitions(raw_fixtures, now)
    capacity = budget_capacity(remaining, now)
    raw_odds = {}
    for index, key in enumerate(eligible):
        these = [m for m in matches if m["competition"] == key]
        if index >= capacity:
            for m in these:
                m["odds_status"] = "budget_limited"
            continue
        reservation = store.reserve(slot, key)
        if not reservation.get("reserved"):
            for m in these:
                m["odds_status"] = "budget_limited"
            continue
        response = odds.fetch(registry.get(key).odds_keys[0])
        raw_odds[key] = response.get("events", [])
        # Ohne gültige Header stoppt jeder weitere kostenpflichtige Abruf.
        if response.get("quota"):
            state = store.observe(response["quota"])
            quota = {"status": "verified", "remaining": state["quota"]["remaining"],
                     "used": state["quota"]["used"]}
        else:
            quota = {"status": "unknown", "remaining": None, "used": None}
            capacity = index + 1
        for m in these:
            original = next(f for f in raw_fixtures if
                            (f.get("match_id") or f"provider:{key}:{f['provider_match_id']}") == m["id"])
            event = find_event(original, response.get("events", []))
            m["odds_status"] = "unavailable" if response["status"] != "live" else "missing"
            if event:
                m.update(normalize_event(event, captured))
                m["odds_status"] = "live" if m["quotes"] else "missing"
    if quota["remaining"] == 0:
        quota["status"] = "exhausted"
    return {"schema_version": 1, "run_id": f"club-{slot}", "slot": slot,
            "generated_at": captured, "next_update_at": next_update(now),
            "matches": matches, "sources": sources, "quota": quota,
            "gates": {"prediction_allowed": False, "value_allowed": False},
            "raw": {"fixtures": fixture_payload, "odds": raw_odds}}


def main():
    parser = argparse.ArgumentParser(description="Private Sites-Club-Pipeline")
    parser.add_argument("--stdin-config", action="store_true")
    parser.add_argument("--bootstrap", action="store_true", help="Einmaliger initialer Datenstand")
    parser.add_argument("--dry-run", action="store_true", help="Nur Spielpläne; keine Quoten oder Uploads")
    args = parser.parse_args()
    if args.stdin_config:
        supplied = json.loads(sys.stdin.readline())
        for key in ("ODDS_API_KEY", "FOOTBALL_DATA_API_KEY", "FOOTBALL_SITE_URL", "FOOTBALL_IMPORT_SECRET", "FOOTBALL_SITE_BYPASS"):
            if supplied.get(key):
                os.environ[key] = supplied[key]
    # Config lädt die Umgebung beim Import; deshalb erst nach stdin-Konfiguration.
    from src.pipeline import club_shadow_run
    from src.data_sources.club_odds_client import ClubOddsClient
    now = dt.datetime.now(dt.timezone.utc)
    slot = scheduled_slot(now)
    if not slot and not args.bootstrap and not args.dry_run:
        print(json.dumps({"status": "outside_slot"}))
        return
    if args.bootstrap:
        slot = f"bootstrap-{now:%Y%m%dT%H%M%S}"
    pending = Path("data/processed/club_sites_pending.json")
    store = None if args.dry_run else SiteStore(os.environ.get("FOOTBALL_SITE_URL", ""),
        os.environ.get("FOOTBALL_IMPORT_SECRET", ""), os.environ.get("FOOTBALL_SITE_BYPASS", ""))
    if pending.exists() and store:
        old = json.loads(pending.read_text(encoding="utf-8"))
        store.upload(old)
        pending.unlink()
    payload = club_shadow_run.run_all(days=7, today=now.astimezone(BERLIN).date(),
        output_path=Path("data/processed/club_sites_fixtures.json"), competition_keys=COMPETITIONS)
    if args.dry_run:
        print(json.dumps({"status": payload["status"], "fixtures": payload["n_fixtures"],
                          "competitions": {k: v["status"] for k, v in payload["competitions"].items()}}))
        return
    run = collect(payload, now, ClubOddsClient(os.environ.get("ODDS_API_KEY", "")), store, slot)
    if run is None:
        print(json.dumps({"status": "slot_already_claimed"}))
        return
    pending.parent.mkdir(parents=True, exist_ok=True)
    pending.write_text(json.dumps(run, ensure_ascii=False), encoding="utf-8")
    result = store.upload(run)
    pending.unlink()
    print(json.dumps({"status": "uploaded", "run_id": run["run_id"],
                      "matches": len(run["matches"]), "quota": run["quota"], "duplicate": result.get("duplicate")}))


if __name__ == "__main__":
    try:
        main()
    except (requests.RequestException, RuntimeError, ValueError, KeyError):
        print("Club-Sites-Lauf fehlgeschlagen. Zugang, Providerstatus und Pending-Datei prüfen.", file=sys.stderr)
        sys.exit(1)

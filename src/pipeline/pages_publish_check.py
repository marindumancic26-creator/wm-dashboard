"""Prueft, ob GitHub Pages den neuesten Static-Export veroeffentlicht hat.

Der Daily-Run kann erfolgreich pushen, waehrend GitHub Pages spaeter im Deploy
scheitert. Dieses Modul vergleicht deshalb den lokalen `docs/index.html`-Stand
mit der oeffentlichen Pages-Seite und liefert ein kleines, maschinenlesbares
Statusobjekt fuer den Watchdog.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

from src import config

DEFAULT_PAGES_URL = "https://marindumancic26-creator.github.io/wm-dashboard/"
GENERATED_AT_RE = re.compile(r'"generated_at"\s*:\s*"([^"]+)"')


def extract_generated_at(html: str) -> str | None:
    match = GENERATED_AT_RE.search(html or "")
    return match.group(1) if match else None


def read_local_generated_at(path: Path | None = None) -> str | None:
    local_path = path or (config.PROJECT_ROOT / "docs" / "index.html")
    if not local_path.exists():
        return None
    return extract_generated_at(local_path.read_text(encoding="utf-8", errors="replace"))


def fetch_remote_generated_at(url: str = DEFAULT_PAGES_URL, timeout: int = 20) -> tuple[str | None, str | None]:
    try:
        cache_buster = "&" if "?" in url else "?"
        req = urllib.request.Request(
            f"{url}{cache_buster}pages_check=1",
            headers={"User-Agent": "wm-dashboard-pages-watchdog"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        return extract_generated_at(html), None
    except (OSError, urllib.error.URLError, urllib.error.HTTPError) as exc:
        return None, str(exc)


def _parse_generated_at(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        parsed = dt.datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def classify(local_generated_at: str | None, remote_generated_at: str | None,
             remote_error: str | None = None) -> dict:
    if not local_generated_at:
        status = "missing_local"
        note = "Lokaler Static-Export docs/index.html enthaelt kein generated_at."
    elif remote_error:
        status = "unreachable"
        note = f"GitHub Pages nicht abrufbar: {remote_error}"
    elif not remote_generated_at:
        status = "missing_remote"
        note = "Oeffentliche Pages-Seite enthaelt kein generated_at."
    else:
        local_dt = _parse_generated_at(local_generated_at)
        remote_dt = _parse_generated_at(remote_generated_at)
        if not local_dt or not remote_dt:
            status = "invalid_timestamp"
            note = "generated_at konnte nicht als ISO-Zeitstempel geparst werden."
        elif remote_dt < local_dt:
            status = "stale"
            note = "GitHub Pages ist aelter als der lokale Static-Export."
        else:
            status = "fresh"
            note = "GitHub Pages ist aktuell."
    return {
        "status": status,
        "local_generated_at": local_generated_at,
        "remote_generated_at": remote_generated_at,
        "remote_error": remote_error,
        "note": note,
    }


def check(url: str = DEFAULT_PAGES_URL, local_path: Path | None = None, timeout: int = 20) -> dict:
    local_generated_at = read_local_generated_at(local_path)
    remote_generated_at, remote_error = fetch_remote_generated_at(url, timeout)
    return classify(local_generated_at, remote_generated_at, remote_error)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=DEFAULT_PAGES_URL)
    parser.add_argument("--local-path", type=Path, default=config.PROJECT_ROOT / "docs" / "index.html")
    parser.add_argument("--timeout", type=int, default=20)
    args = parser.parse_args(argv)
    result = check(args.url, args.local_path, args.timeout)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

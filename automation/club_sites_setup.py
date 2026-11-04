"""GitHub-Voraussetzungen prüfen und beauftragte Secrets sicher via stdin setzen.

Nie Tokens ausgeben. Vorhandene Git-Credential-Manager-Anmeldung wird verwendet,
ohne eine neue interaktive Anmeldung zu starten. Keine Sichtbarkeits-/Billingänderung.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

import requests

REPO = "marindumancic26-creator/wm-dashboard"
BASE = f"https://api.github.com/repos/{REPO}"


def github_token():
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        return token
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "never"}
    try:
        result = subprocess.run(["git", "credential", "fill"], input="protocol=https\nhost=github.com\n\n",
            text=True, capture_output=True, env=env, timeout=20)
        if result.returncode:
            return None
        return dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line).get("password")
    except (subprocess.SubprocessError, OSError):
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("inspect", "configure", "activate"))
    parser.add_argument("--key-file", type=Path)
    args = parser.parse_args()
    token = github_token()
    if not token:
        print(json.dumps({"github_access": False, "reason": "Keine nichtinteraktive GitHub-Anmeldung verfügbar"}))
        return
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    response = requests.get(BASE, headers=headers, timeout=25)
    if response.status_code != 200:
        print(json.dumps({"github_access": False, "http_status": response.status_code}))
        return
    repo = response.json()
    permission = requests.get(f"{BASE}/actions/permissions", headers=headers, timeout=25)
    print(json.dumps({"github_access": True, "private": repo["private"],
        "default_branch": repo["default_branch"], "actions_permission_status": permission.status_code,
        "actions_enabled": permission.json().get("enabled") if permission.status_code == 200 else None}))
    if args.mode == "inspect":
        return
    env = {**os.environ, "GH_TOKEN": token}
    if args.mode == "activate":
        # Public standard Linux runners are included; private billing must be checked separately.
        if repo["private"] or permission.status_code != 200 or not permission.json().get("enabled"):
            print(json.dumps({"activated": False, "reason": "Kostenlose Actions-Ausführung nicht bestätigt"}))
            return
        result = subprocess.run(["gh", "variable", "set", "FOOTBALL_SITES_ENABLED", "--repo", REPO, "--body", "true"],
            capture_output=True, text=True, env=env, timeout=30)
        print(json.dumps({"activated": result.returncode == 0}))
        return
    supplied = json.loads(sys.stdin.readline())
    keys = json.loads(args.key_file.read_text(encoding="utf-8-sig")) if args.key_file else {}
    values = {"FOOTBALL_SITE_URL": supplied["site_url"], "FOOTBALL_SITE_BYPASS": supplied["site_bypass"],
              "FOOTBALL_IMPORT_SECRET": supplied["import_secret"],
              "ODDS_API_KEY": keys.get("odds_api") or os.environ.get("ODDS_API_KEY"),
              "FOOTBALL_DATA_API_KEY": keys.get("football_data") or os.environ.get("FOOTBALL_DATA_API_KEY")}
    for key, value in values.items():
        if not value:
            print(json.dumps({"key": key, "configured": False, "reason": "Wert fehlt"}))
            continue
        result = subprocess.run(["gh", "secret", "set", key, "--repo", REPO], input=value,
            text=True, capture_output=True, env=env, timeout=40)
        print(json.dumps({"key": key, "configured": result.returncode == 0}))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, requests.RequestException, subprocess.SubprocessError):
        print(json.dumps({"ok": False, "reason": "Einrichtung fehlgeschlagen; keine Secrets ausgegeben"}))
        sys.exit(1)

"""Prueft den GitHub-Pages-Betriebszustand beobachtend.

Der Pages-Watchdog vergleicht bereits lokalen und oeffentlichen Static-Export.
Dieses Modul schaut eine Ebene hoeher: laufen die erwarteten GitHub-Actions
weiterhin sauber und taucht der alte Branch-Deploy-Pfad nicht wieder auf?
Es schreibt keine GitHub- oder Projektkonfiguration und ist bewusst read-only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from src import config
from src.pipeline import pages_publish_check

REPO_OWNER = "marindumancic26-creator"
REPO_NAME = "wm-dashboard"
GITHUB_API = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"
PAGES_URL = pages_publish_check.DEFAULT_PAGES_URL
EXPECTED_PAGES_WORKFLOW = "pages"
EXPECTED_TESTS_WORKFLOW = "tests"
LEGACY_PAGES_WORKFLOW = "pages build and deployment"
# Letzter bekannter Branch-Deploy-Lauf aus der Umstellungsminute auf GitHub
# Actions. Alles danach waere ein neuer Rueckfall auf den alten Pages-Pfad.
LEGACY_WORKFLOW_CUTOFF = "2026-07-05T10:46:00+02:00"


def _parse_time(value: str | None) -> dt.datetime | None:
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


def _latest_run(workflow_runs: list[dict[str, Any]], workflow_name: str) -> dict[str, Any] | None:
    matching = [r for r in workflow_runs if r.get("name") == workflow_name]
    if not matching:
        return None
    return sorted(matching, key=lambda r: _parse_time(r.get("created_at")) or dt.datetime.min.replace(
        tzinfo=dt.timezone.utc), reverse=True)[0]


def _workflow_check(workflow_runs: list[dict[str, Any]], workflow_name: str) -> dict[str, Any]:
    run = _latest_run(workflow_runs, workflow_name)
    if not run:
        return {
            "status": "warning",
            "workflow": workflow_name,
            "note": f"Workflow {workflow_name!r} wurde in der GitHub-API nicht gefunden.",
        }
    status = run.get("status")
    conclusion = run.get("conclusion")
    if status == "completed" and conclusion == "success":
        check_status = "ok"
        note = f"Workflow {workflow_name!r} ist gruen."
    elif status in {"queued", "in_progress", "waiting", "requested", "pending"}:
        check_status = "warning"
        note = f"Workflow {workflow_name!r} laeuft noch ({status})."
    else:
        check_status = "error"
        note = f"Workflow {workflow_name!r} ist nicht gruen: status={status}, conclusion={conclusion}."
    return {
        "status": check_status,
        "workflow": workflow_name,
        "run_id": run.get("id"),
        "run_number": run.get("run_number"),
        "head_sha": run.get("head_sha"),
        "created_at": run.get("created_at"),
        "html_url": run.get("html_url"),
        "github_status": status,
        "conclusion": conclusion,
        "note": note,
    }


def _legacy_workflow_check(workflow_runs: list[dict[str, Any]],
                           cutoff: str = LEGACY_WORKFLOW_CUTOFF) -> dict[str, Any]:
    cutoff_dt = _parse_time(cutoff)
    legacy_runs = [r for r in workflow_runs if r.get("name") == LEGACY_PAGES_WORKFLOW]
    if cutoff_dt:
        legacy_runs = [r for r in legacy_runs
                       if (_parse_time(r.get("created_at")) or dt.datetime.min.replace(
                           tzinfo=dt.timezone.utc)) > cutoff_dt]
    if not legacy_runs:
        return {
            "status": "ok",
            "workflow": LEGACY_PAGES_WORKFLOW,
            "note": "Alter Branch-Deploy-Pfad ist seit dem Cutoff nicht neu aufgetaucht.",
        }
    latest = sorted(legacy_runs, key=lambda r: _parse_time(r.get("created_at")) or dt.datetime.min.replace(
        tzinfo=dt.timezone.utc), reverse=True)[0]
    return {
        "status": "error",
        "workflow": LEGACY_PAGES_WORKFLOW,
        "run_id": latest.get("id"),
        "run_number": latest.get("run_number"),
        "head_sha": latest.get("head_sha"),
        "created_at": latest.get("created_at"),
        "html_url": latest.get("html_url"),
        "github_status": latest.get("status"),
        "conclusion": latest.get("conclusion"),
        "note": "Alter Branch-Deploy-Pfad wurde wieder aktiv; Pages-Source pruefen.",
    }


def _pages_public_check(pages_result: dict[str, Any]) -> dict[str, Any]:
    status = "ok" if pages_result.get("status") == "fresh" else "error"
    return {
        "status": status,
        "local_generated_at": pages_result.get("local_generated_at"),
        "remote_generated_at": pages_result.get("remote_generated_at"),
        "remote_error": pages_result.get("remote_error"),
        "note": pages_result.get("note"),
    }


def _pages_settings_check(settings: dict[str, Any] | None,
                          settings_error: str | None = None) -> dict[str, Any]:
    if settings_error:
        return {
            "status": "warning",
            "note": f"Pages-Settings nicht direkt pruefbar: {settings_error}",
        }
    if settings is None:
        return {
            "status": "warning",
            "note": "Pages-Settings ohne GitHub-Token nicht direkt pruefbar.",
        }
    build_type = settings.get("build_type")
    if build_type == "workflow":
        return {
            "status": "ok",
            "build_type": build_type,
            "note": "GitHub Pages nutzt GitHub Actions als Source.",
        }
    return {
        "status": "error",
        "build_type": build_type,
        "source": settings.get("source"),
        "note": "GitHub Pages scheint nicht auf GitHub Actions konfiguriert zu sein.",
    }


def classify_health(pages_result: dict[str, Any],
                    workflow_runs: list[dict[str, Any]],
                    settings: dict[str, Any] | None = None,
                    settings_error: str | None = None,
                    cutoff: str = LEGACY_WORKFLOW_CUTOFF) -> dict[str, Any]:
    checks = {
        "pages_public": _pages_public_check(pages_result),
        "workflow_pages": _workflow_check(workflow_runs, EXPECTED_PAGES_WORKFLOW),
        "workflow_tests": _workflow_check(workflow_runs, EXPECTED_TESTS_WORKFLOW),
        "legacy_branch_deploy": _legacy_workflow_check(workflow_runs, cutoff),
        "pages_settings": _pages_settings_check(settings, settings_error),
    }
    statuses = [c["status"] for c in checks.values()]
    if "error" in statuses:
        status = "error"
    elif "warning" in statuses:
        status = "warning"
    else:
        status = "ok"

    notes = [c["note"] for c in checks.values() if c.get("status") != "ok"]
    if not notes:
        notes = ["GitHub Pages, Actions und oeffentlicher Stand sind konsistent."]
    return {
        "status": status,
        "checked_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "repo": f"{REPO_OWNER}/{REPO_NAME}",
        "pages_url": PAGES_URL,
        "checks": checks,
        "note": " | ".join(notes),
    }


def _github_get_json(path: str, token: str | None = None, timeout: int = 20) -> tuple[Any | None, str | None]:
    req = urllib.request.Request(
        f"{GITHUB_API}{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "wm-dashboard-github-pages-health",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8")), None
    except (OSError, urllib.error.URLError, urllib.error.HTTPError) as exc:
        return None, str(exc)


def fetch_workflow_runs(token: str | None = None, timeout: int = 20) -> tuple[list[dict[str, Any]], str | None]:
    payload, error = _github_get_json("/actions/runs?branch=main&per_page=30", token, timeout)
    if error:
        return [], error
    return list((payload or {}).get("workflow_runs", [])), None


def fetch_pages_settings(token: str | None = None, timeout: int = 20) -> tuple[dict[str, Any] | None, str | None]:
    if not token:
        return None, None
    payload, error = _github_get_json("/pages", token, timeout)
    if error:
        return None, error
    return dict(payload or {}), None


def run(timeout: int = 20, output_path: Path | None = None) -> dict[str, Any]:
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    pages_result = pages_publish_check.check(timeout=timeout)
    workflow_runs, runs_error = fetch_workflow_runs(token, timeout)
    settings, settings_error = fetch_pages_settings(token, timeout)

    result = classify_health(
        pages_result=pages_result,
        workflow_runs=workflow_runs,
        settings=settings,
        settings_error=settings_error,
    )
    if runs_error:
        result["checks"]["github_actions_api"] = {
            "status": "warning",
            "note": f"GitHub-Actions-API nicht direkt pruefbar: {runs_error}",
        }
        if result["status"] == "ok":
            result["status"] = "warning"
        result["note"] = result["note"] + f" | GitHub-Actions-API nicht direkt pruefbar: {runs_error}"

    target = output_path or (config.DATA_SNAPSHOTS / "github_pages_health_last.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--output", type=Path, default=config.DATA_SNAPSHOTS / "github_pages_health_last.json")
    args = parser.parse_args(argv)
    result = run(timeout=args.timeout, output_path=args.output)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

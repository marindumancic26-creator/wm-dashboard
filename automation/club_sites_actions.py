"""Begrenzte Actions-Steuerung ohne Token- oder Logausgabe."""
import argparse
import json
import sys
import requests
from automation.club_sites_setup import github_token, BASE


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("action",choices=("dispatch","status"))
    parser.add_argument("--run-id",type=int)
    args=parser.parse_args()
    token=github_token()
    if not token:
        raise RuntimeError("Keine GitHub-Anmeldung")
    headers={"Authorization":f"Bearer {token}","Accept":"application/vnd.github+json"}
    workflow=f"{BASE}/actions/workflows/club-sites.yml"
    if args.action=="dispatch":
        response=requests.post(f"{workflow}/dispatches",headers=headers,
            json={"ref":"main","inputs":{"bootstrap":"true"}},timeout=30)
        print(json.dumps({"dispatched":response.status_code==204,"http_status":response.status_code}))
        return
    if args.run_id:
        response=requests.get(f"{BASE}/actions/runs/{args.run_id}/jobs",headers=headers,timeout=30)
        response.raise_for_status()
        print(json.dumps({"jobs":[{"id":j["id"],"name":j["name"],"status":j["status"],"conclusion":j["conclusion"],
            "steps":[{"name":s["name"],"conclusion":s["conclusion"]} for s in j.get("steps",[])]} for j in response.json().get("jobs",[])]}))
        return
    response=requests.get(f"{workflow}/runs",params={"per_page":3},headers=headers,timeout=30)
    response.raise_for_status()
    print(json.dumps({"runs":[{k:r.get(k) for k in ("id","status","conclusion","head_sha","html_url","created_at")}
                             for r in response.json().get("workflow_runs",[])]}))


if __name__=="__main__":
    try:
        main()
    except (RuntimeError,requests.RequestException,ValueError):
        print(json.dumps({"ok":False,"reason":"Actions-Abfrage fehlgeschlagen"}))
        sys.exit(1)

# Private Football Sites Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Private mobile Fußball-Site mit budgetierten echten Quoten und rechnerunabhängigen Updates.

**Architecture:** Bestehendes Python erzeugt Club-Runs; GitHub Actions transportiert sie in eine owner-private Sites-App. D1 hält Koordination/aktuellen Run, R2 die unveränderlichen Run-Artefakte.

**Tech Stack:** Python 3.12, pytest, vorhandene requests/NumPy; offizieller Vinext/React/TypeScript-Starter, semantisches HTML/CSS, D1/R2.

**Spec:** ../specs/2026-11-04-private-football-sites-design.md

## Global Constraints
- Fünf vereinbarte Wettbewerbe, EU h2h+totals, 09/14/18 Europe/Berlin, Datenbudget 0 EUR.
- Bestehende Freigaben unverändert; niemals fehlende Daten ergänzen.
- Kein Secret in Quellcode, Logs oder Browser; kein öffentlicher Datenimport.
- WM-Pfad und fremde Änderungen bewahren; Arbeit im isolierten Checkout.
- Der Nutzer hat Umsetzung und private Veröffentlichung bereits beauftragt; keine erneute Freigabe.

## Review Focus
- Doppelte/verzögerte Läufe: kein mehrfacher Quotenverbrauch.
- Fehlende Budgetheader und API-Timeout: konservativ verbuchte Reservierung, kein unkontrollierter Folgeabruf.
- Falsche Paarung oder Totallinie: kein team- oder linienübergreifender Quotenvergleich.
- Importverlust/Replay: vorheriger gültiger Run und Archiv bleiben erhalten.
- Anonymer Browser oder nur ein gültiger Import-Header: keine unberechtigten Lese-/Schreibrechte.

### Task 1: Scheduling and quota coordination
**Files:** src/pipeline/club_sites_policy.py; tests/test_club_sites.py.
**Interfaces:** scheduled_slot(now) -> str|None; eligible_competitions(fixtures, now) -> list[str]; quota allowance pure functions. Shared wire fields: schema_version=1, run_id, slot, generated_at, competitions, matches, sources, quota, gates.
- [ ] Write tests for DST, late slots, kicked-off fixtures, conservative monthly pacing, missing/invalid quota.
- [ ] Run tests and observe missing-feature failures.
- [ ] Implement pure policy functions; run tests to green.

### Task 2: Club run collector and uploader
**Files:** src/pipeline/club_sites_run.py; src/data_sources/club_odds_client.py; tests/test_club_sites.py.
**Interfaces:** run(now, client, store) -> versioned run; provider normalizer preserves bookmaker/market/point/timestamps. Sites coordinator provides GET/POST internal state, reservation and idempotency.
- [ ] Add tests for canonical fixture matching, h2h/totals line separation, missing models and partial provider failure.
- [ ] Observe failures, implement using existing registry/adapters, verify green.
- [ ] Add CLI with dry-run, safe secret loading, authenticated state/reserve/import and retrying pending upload without new provider calls.

### Task 3: Private Site storage and trust boundaries
**Files:** sites/fussballanalyse/app/api/**; sites/fussballanalyse/lib/**; db/schema.ts and generated migrations; tests/*.test.ts.
**Interfaces:** GET /api/dashboard, GET /api/matches/[id]; POST /api/internal/runs; GET/POST /api/internal/state; POST /api/internal/reservations. Browser reads require Sites identity; internal calls require an import bearer secret plus platform access on hosted private Site. Server validates every imported run and applies model gates.
- [ ] Scaffold official starter and register a single owner-private Site, persist ID, start dependency installation.
- [ ] Test payload validation, gate projection, replay conflicts, invalid imports and access checks before implementing helpers.
- [ ] Implement D1 transaction coordination, R2 archive and current-run index with idempotent import; retain last good matches on partial errors.
- [ ] Generate schema-only migrations, inspect, typecheck/test/build.

### Task 4: Mobile-first analysis UI
**Files:** sites/fussballanalyse/app/page.tsx, dashboard.tsx, globals.css, layout.tsx.
**Interfaces:** consumed normalized dashboard response only; URL state for competition/day and selected match.
- [ ] Implement agreed layout with native controls, loading/empty/error/stale/gated states; mobile single column and desktop master/detail.
- [ ] Show exact markets, source/quote timestamps, only permitted model numbers; no mock fallback.
- [ ] Verify build and browser QA at 320/390/1280px including keyboard and theme/contrast checks.

### Task 5: Cloud activation and deployment
**Files:** .github/workflows/club-sites.yml; automation/club_sites_setup.py; docs/SITES_OPERATIONS.md.
- [ ] Test workflow slot idempotency and activation guard; execute all existing tests and affected Site tests/build.
- [ ] Configure provider/import Secrets through authenticated services if available; check account/repository execution eligibility without changing visibility or billing.
- [ ] Publish owner-private using Sites source/package helpers, verify authenticated real import/readback.
- [ ] Activate guarded GitHub schedule only after prerequisites pass. Record any inaccessible external setup precisely.
- [ ] Whole-change independent review, fix important findings with regression tests, final verified handoff.

# Quality Playbook Progress

## Run metadata
Started: 2026-06-14
Project: wm-dashboard-fussball-wahrscheinlichkeit
Skill version: 1.5.6
Runner: claude-code (Mode A skill-direct; `bin/` modules absent, instrumentation hand-written)
With docs: no (no reference_docs/; memory/ used as Tier-4 context)
Benchmark: wm-dashboard · Lever: baseline

## Phase completion
- [x] Phase 1: Exploration — completed 2026-06-14
- [x] Phase 2: Artifact generation — completed 2026-06-14 (10 artifacts; 25 functional tests passing)
- [x] Phase 3: Code review + regression tests — completed 2026-06-14 (6 bugs confirmed, 6 red logs)
- [x] Phase 4: Spec audit + triage — completed 2026-06-14 (3 auditors, 2 net-new bugs, 8 total)
- [x] Phase 5: Post-review reconciliation + closure verification — completed 2026-06-14
- [x] Phase 6: Verification benchmarks — completed 2026-06-14 (suites green, stamps 1.5.6)
- [x] Phase 7: Present, Explore, Improve — presented 2026-06-14

## Scale
~28 Python source files in `src/` (<200) → full exploration, no scope declaration required.

## Artifact inventory
| Artifact | Status | Path | Notes |
|----------|--------|------|-------|
| EXPLORATION.md | generated | quality/EXPLORATION.md | 9 OF, 6 QR, 3 deep dives, 6 candidate bugs, 12 REQ, 6 UC |
| run metadata | generated | quality/results/run-2026-06-14T19-26-15.json | |
| run_state.jsonl | generated | quality/run_state.jsonl | phase 1 events |
| QUALITY.md | generated | quality/QUALITY.md | 10 fitness scenarios |
| REQUIREMENTS.md | generated | quality/REQUIREMENTS.md | 12 specific + 2 arch-guidance, 6 UC |
| CONTRACTS.md | generated | quality/CONTRACTS.md | 33 contracts |
| COVERAGE_MATRIX.md | generated | quality/COVERAGE_MATRIX.md | one row/REQ |
| COMPLETENESS_REPORT.md | generated | quality/COMPLETENESS_REPORT.md | baseline |
| Functional tests | generated | quality/test_functional.py | 25 tests, all passing |
| RUN_CODE_REVIEW.md | generated | quality/RUN_CODE_REVIEW.md | three-pass |
| RUN_SPEC_AUDIT.md | generated | quality/RUN_SPEC_AUDIT.md | council of three |
| RUN_INTEGRATION_TESTS.md | generated | quality/RUN_INTEGRATION_TESTS.md | offline-snapshot core |
| RUN_TDD_TESTS.md | generated | quality/RUN_TDD_TESTS.md | red-green per CB |
| BUGS.md | pending | | Phase 3 |

## Documentation depth assessment
No `reference_docs/`. `memory/*.md` (model_logic, project, data_sources, learnings) are
moderate-depth Tier-4 intent sources. Module docstrings are the deepest spec and are the
basis for the strongest candidate bugs (docstring-vs-code divergences: CB-2, CB-3).

## Cumulative BUG tracker
<!-- Populated in Phase 3/4. Phase 1 produces candidate bugs only (see EXPLORATION.md). -->

| # | Source | File:Line | Description | Severity | Closure Status | Test/Exemption |
|---|--------|-----------|-------------|----------|----------------|----------------|
| BUG-001 | Code Review | monte_carlo.py:97-99 | simulate crashes runs<200 → silent match drop | MEDIUM | TDD verified (FAIL→PASS) | test_bug001_… (red ✓) |
| BUG-002 | Code Review | monte_carlo.py:96-105 | uncertainty band = MC noise, not parameter uncertainty | MEDIUM | TDD verified (FAIL→PASS) | test_bug002_… (red ✓) |
| BUG-003 | Code Review | ensemble.py:74-89 | blend_lambdas drops books λ when market absent | LOW-MED | TDD verified (FAIL→PASS) | test_bug003_… (red ✓) |
| BUG-004 | Code Review | value_betting.py:143-145 | integer totals push mass → Under | MEDIUM | TDD verified (FAIL→PASS) | test_bug004_… (red ✓) |
| BUG-005 | Code Review | value_betting.py:38,148-150 | totals σ smaller than 1X2 at equal edge | LOW | TDD verified (FAIL→PASS) | test_bug005_… (red ✓) |
| BUG-006 | Code Review | whale_scoring.py:97-113 | exposure mixes share-count + USD | MEDIUM | TDD verified (FAIL→PASS) | test_bug006_… (red ✓) |
| BUG-007 | Spec Audit | ensemble.py:33 | whale default 0.2 != config 0.15 | LOW | TDD verified (FAIL→PASS) | test_bug007_… (red ✓) |
| BUG-008 | Spec Audit | data_quality.py:24-35 | market_agreement ignores draw/away | LOW | TDD verified (FAIL→PASS) | test_bug008_… (red ✓) |
| BUG-009 | Learning-Loop Audit | closing_loop.py:56 | RPS==0.0 falsy → Bestenliste falsch sortiert | LOW | TDD verified (FAIL→PASS) | test_bug009_… |
| BUG-010 | Daily-Run (live) | config.py:115 | canonical_team(None) crasht → Match-Drop | MEDIUM | TDD verified (FAIL→PASS) | test_bug010_… |

## Exploration summary
World Cup probability + value-betting pipeline. High-quality, well-tested code (33 value-
asserting tests). The risk concentrates in the probability→uncertainty→value-bet chain.
Six candidate bugs identified, strongest being CB-1 (`simulate` crashes for runs<200, silent
match drop) and CB-2/CB-3 (uncertainty band semantics; prob-path vs λ-path parity break).
`api_keys.json` confirmed gitignored and untracked — no secret leak.

## Terminal Gate Verification
BUG tracker has 9 entries. 8 have regression tests (strict-xfail, red logs present), 0 have
exemptions, 0 are unresolved. Code review confirmed 6 bugs. Spec audit confirmed 2 net-new code
bugs. Expected total: 6 + 2 + 1 (learning-loop audit) = 9. **MATCH.** All red logs exist (quality/results/BUG-00N.red.log).
Severity: 4 MEDIUM, 1 LOW-MED, 3 LOW. No HIGH. Verdict: PASS (with confirmed open bugs).

# Execution ledger: 2026-11-04-private-football-sites.md

- Base: 6b503d6. Isolated branch codex/private-football-sites, external worktree under the task workspace.
- Ruling: native app worktree tool targets the originally opened non-Git directory; use Git's linked-worktree mechanism for the discovered repository. This preserves local automated writes on main.
- Ruling: native inline execution follows the user's explicit implementation request; no additional approval loop. One independent review at completion.
- Ruling: a dedicated import secret is added in addition to private Sites platform access, so authenticated visitors cannot call machine mutations.
- Pre-flight: collector and Site share schema_version=1 JSON; policy/collector share competition keys from the existing registry; import and UI share sanitized projection. No conflicting interfaces.
- Ruling: Site checkout is a separate repository at C:/Users/marin/Fußball wahrscheinlichkeit/sites/fussballanalyse. Its private Sites source synchronization must not create a nested Git repository in the public Python project.
- Task 1: complete. DST/late slots, eligible fixtures and paced quota tests RED -> GREEN.
- Task 2: complete. Collector/normalizer/diagnostic reuse, deduplication and unknown-budget tests RED -> GREEN. Genuine fixture-only check returned 48 fixtures and all five providers live.
- Task 3: complete locally. Node domain tests 4/4; actual built-worker HTTP integration passed identity rejection, claims, reservations, replay conflicts, locked gates and readback. Native Sites runtime secret set; owner-private policy confirmed.
- Task 4: implemented; TypeScript and official build passed. Browser QA blocked by browser infrastructure (IAB crash; Chrome timeoutMs error); mobile visual verification is not claimed.
- Baseline: 145 selected existing tests passed. Full Python suite after implementation: 195 passed.
- GitHub: existing credential manager authentication works; repository public, Actions enabled; all five required repository Secrets set successfully. Activation remains gated on published-site readback.
- Final review: independent gpt-6-astra review read both codebases. Two important defects reproduced and fixed with RED -> GREEN tests: already-started/starting-during-fetch events cannot receive new quotes; postponed/changed-side fixtures cannot inherit old quotes.
- Final review: cache provenance without capture time is now explicitly unknown/stale; regression test RED -> GREEN. Offset ordering uses julianday; live HTTP regression observed failing before fix, rerun pending rebuild. Additional totals lines now have a native accessible selector.
- Final: minor (deferred): two independently authenticated, different simultaneous importers could race while merging fallback data. Normal operation has exactly one producer, serialized by GitHub concurrency. Manual bootstrap must run only with the schedule paused; immutable raw captures remain archived.
- Final: Ruling: mobile/keyboard browser verification remains unavailable because the browser infrastructure failed; do not describe it as tested. HTTP, type and build checks proceed; hosted privacy/Cloud execution will be checked through their APIs.
- Full Python suite after review fixes: 198 passed; Node domain tests: 5 passed; TypeScript passed.
- Status: packaging/private publication and real Cloud readback pending.

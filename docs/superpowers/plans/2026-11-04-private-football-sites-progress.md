# Execution ledger: 2026-11-04-private-football-sites.md

- Base: 6b503d6. Isolated branch codex/private-football-sites, external worktree under the task workspace.
- Ruling: native app worktree tool targets the originally opened non-Git directory; use Git's linked-worktree mechanism for the discovered repository. This preserves local automated writes on main.
- Ruling: native inline execution follows the user's explicit implementation request; no additional approval loop. One independent review at completion.
- Ruling: a dedicated import secret is added in addition to private Sites platform access, so authenticated visitors cannot call machine mutations.
- Pre-flight: collector and Site share schema_version=1 JSON; policy/collector share competition keys from the existing registry; import and UI share sanitized projection. No conflicting interfaces.
- Status: plan/spec saved; implementation pending.

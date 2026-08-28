# PROCESS.md — temporal-discipline ledger

Append-only record of what was frozen when, and the SHA-256 digests that make
freeze claims verifiable independent of the co-located `.sha256` files (per
`PLAN.md` invariant #1/#2). Every entry is dated and, once committed, never
edited — corrections are new entries.

## Log

### 2026-08-28 — Phase 0 complete
- Archived `eval/generate.py`, `eval/BUSINESS_RULES.md`, `eval/data/pilot/`
  to `archive/ledgerguard-pretest/` (untouched, as generated/run).
  `results/pretest/` and `trajectories/pretest/` left in place (disclosure
  requirement — not reshuffled retroactively).
- Purged stale "micro1 Frontier Engineering Challenge / HackerEarth" framing
  from README.md and HANDOFF_PROMPT.md (this repo's actual event is the
  micro1 Agentic Workflows Hackathon per `CLAUDE.md`/`PROBLEM.md`).
- CHANGELOG.md rewritten with the real Stage-table structure and the
  LedgerGuard removed-experiment entry (real numbers, not placeholders).

### 2026-08-28 — Phase 1 build: live-fire finding on the Arm-B sandbox
While building `eval/sandbox_guard.py` (the PreToolUse path-containment hook
for Arm B, PLAN.md invariant #1), a live smoke test surfaced a real gap
**before** it could reach the frozen corpus: with only `allowed_tools=["Read",
"Grep","Glob"]` set (no `disallowed_tools`), a real agent session
successfully invoked `Bash({'command': 'pwd; ls'})` — `allowed_tools` is a
*pre-approval allowlist*, not a hard restriction; unlisted tools still ran
under the default (unset) permission mode. Our PreToolUse hook only inspects
`file_path`/`path`/`pattern` keys, so a live Bash call would have bypassed it
entirely (`cat`, `find`, arbitrary shell). **Fix:** `disallowed_tools=["Bash",
"Write","Edit","MultiEdit","NotebookEdit","WebFetch","WebSearch","Task",
"ToolSearch"]` added explicitly to Arm B's options — re-verified live: the
same prompt that previously ran Bash now correctly reports no Bash tool is
available. `eval/test_sandbox_guard.py` (7 unit cases) covers the hook's own
path logic; this finding is about the SDK's tool-gating semantics, which no
unit test of the hook alone would have caught — logged here as the reason
`disallowed_tools` is load-bearing, not redundant, in the final Arm-B config.

*(Phase 1 gate verdict, Phase 2 freeze digests, and all subsequent entries
are appended here as each phase completes — never backfilled from memory.)*

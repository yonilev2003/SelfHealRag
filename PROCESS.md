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

*(Phase 1 gate verdict, Phase 2 freeze digests, and all subsequent entries
are appended here as each phase completes — never backfilled from memory.)*

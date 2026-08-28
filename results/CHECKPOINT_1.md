# CHECKPOINT #1 — Phase 1 pre-test gate (soft checkpoint, per PLAN.md)

**Verdict: STOP_TRIVIAL** (rule 1 fired: B-mini == 6/6 AND A0-mini == 6/6)

## Gate results (run 1, mini corpus: 8 docs / 12 chunks / 6 probes)

| Arm | Score | Staleness (3 probes) | Cost | Wall-clock |
|---|---|---|---|---|
| A0 (text-only, whole mini-corpus inline) | **6/6** | 3/3 | $0.049 | 15.5s |
| A (static BM25, k=3) | 5/6 | 2/3 | $0.025 | 18.7s |
| B (generalist agent, sandboxed, Read/Grep/Glob) | **6/6** | 3/3 | $0.225 | 41.0s |

**Budget projection (scaled to real 248-chunk corpus):** $6.18, 25.9 min —
well inside the 40-min/$15 gate. Not the blocker here.

## Per-probe detail

The only failure across all 18 (arm × probe) runs: **Arm A on mini-01**
("What is the current VPN session timeout, in hours?") — BM25 top-3 retrieved
the "policy supersedes January" *announcement* chunk (`it-vpn-v2-c01`) but
missed the adjacent chunk holding the actual number (`it-vpn-v2-c02`),
answering "unknown". The near-identical rephrasing (mini-02) retrieved
correctly. Every other arm×probe combination — including both A0 and B on
every probe, and A on 5/6 — was exactly correct, citing the right chunk.

## Reading this honestly

This is **not the same shape of result as the LedgerGuard kill**. There, the
fair baseline aced the task *at the actual target scale* (800–3,000 orders),
cheaply and fast — strong, scale-matched evidence the task was intrinsically
solvable without orchestration. Here, the mini pilot is **deliberately ~20×
smaller** than the real corpus (12 chunks vs. the planned 248) specifically
to make the pilot cheap — and at that scale, both A0 (sees the *entire*
corpus every time) and B (a careful agent reading 8 short docs) have no room
to fail: there's nothing to lose track of. The one crack that did appear —
Arm A's retrieval-miss, on a rephrasing where the value-bearing chunk didn't
lexically resemble the question closely enough to win the k=3 window — is
exactly the `retrieval_miss` failure category the design already anticipates
(PLAN.md Phase 4 taxonomy), just observed on a 1/6 sample too small to clear
the ≥2/3 threshold.

**Per PLAN.md's own rule, this is a hard STOP-and-consult, not an automatic
hardening retry** — rule 1 fires before rule 3 is even evaluated, by design,
specifically so a real signal isn't rationalized past. Rule 3's coded
`harden()` recipe (a few extra distractor chunks in the *same* 12-chunk
corpus) also doesn't actually address what this result points at: the pilot
needs more **scale** — more chunks, more near-duplicate/implicit-supersession
traps competing for attention — to be an informative test of whether A0/B
degrade the way the real 248-chunk, 40-probe corpus is designed to make them
degrade. That's a real gap in how Phase 1 was specified, caught live.

## Recommendation

Scale the pilot up materially (aim for roughly a quarter of the real corpus —
~60 chunks, proportionally more near-dup/implicit-trap density) and run the
gate once more before deciding. Treat this scaled re-run as the one
hardening attempt CLAUDE.md's hard gate allows (a genuine fix to the
diagnosed weakness — scale, not just decoy count — rather than the originally
coded recipe) — if A0 or B still hit a clean ceiling at that scale, that
*would* be real evidence to reconsider the concept, matching LedgerGuard's
fate; if cracks widen as scale grows, that's the signal PROCEED needs.

This report exists precisely so that "STOP" doesn't automatically read as
"the concept is dead" without a human seeing the actual per-probe evidence.

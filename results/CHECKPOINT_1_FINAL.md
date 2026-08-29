# CHECKPOINT #1 — FINAL (2nd gate run) — HARD STOP, consulting per CLAUDE.md

**Verdict: STOP_2ND_ATTEMPT.** Per CLAUDE.md's hard gate ("more than 2 fix
attempts... stop immediately, show the actual error log, consult before
continuing") and PLAN.md's own rule 4, this is a genuine stop — not a third
pilot redesign.

## The actual data (both runs, side by side)

| Arm | Run 1 (12 chunks) | Run 2 (60 chunks, +2 decoy supersession pairs, +20 noise docs) |
|---|---|---|
| A0 — text-only, whole corpus inline | 6/6 | **6/6** |
| A — static BM25, k=3 | 5/6 | **5/6** (identical failure) |
| B — sandboxed generalist agent, Read/Grep/Glob | 6/6 | **6/6** |

Scaling the corpus 5× (12 → 60 chunks), adding two more concurrent
"policy got revised" episodes on unrelated entities (support SLA response
time, data retention period — one explicit, one implicit, exactly mirroring
the two probed pairs) and 20 distractor department docs did not crack a
**single additional case**. Arm A's one miss is the exact same probe, same
wrong chunk, same wrong answer, in both runs.

## Reading this honestly — this is different from run 1's read

Run 1's checkpoint argued the mini pilot might simply be too small to be
informative. That argument predicted scaling would surface more cracks if
the concept's premise holds. **It didn't happen.** Doubling down a second
time with a bigger, harder pilot and getting the identical result is now
real evidence, not an artifact of pilot size — the same shape of finding
that killed LedgerGuard: **claude-sonnet-5, given either full context (A0)
or basic file-reading tools (B — the PDF's own "one general purpose agent
with basic tools" baseline), is already very good at "find the current
version of a policy fact amid distractors and revision noise"** in the size
range tested (12–60 chunks; the real corpus was planned at 248). Only the
weakest arm — static retrieval with no agency at all (A) — shows any crack,
and only on 1 of 18 probe-runs across both gates.

## What this does and doesn't tell us

- **Does tell us:** a system that is *just* RAG-with-verification over a
  corpus in this size class, whose only failure mode is "does retrieval
  surface the right chunk," has a real but narrow target — Arm A's single
  failure is genuine and structurally interesting (retrieval_miss on
  vocabulary mismatch), but a whole orchestrated audit-diagnose-fix-reverify
  pipeline is a lot of engineering to close a gap this narrow, and B already
  closes it for ~20× the cost of A with zero orchestration.
- **Doesn't tell us:** whether the gap reopens at the REAL planned scale
  (248 chunks, 40 probes, deliberately adversarial near-dup/implicit/3-hop
  traps) — 60 chunks is still ~4× smaller than that, and B's cost/latency
  scales with corpus size in a way that might make it impractical (not
  just imperfect) well before it becomes inaccurate. A third pilot scale-up
  could still find that inflection point — but CLAUDE.md's gate says two
  failed attempts is the line, and I'd be inventing a new mechanism to
  extend past it a third time on my own judgment, which is exactly what
  the gate exists to prevent.

## What I am NOT doing

Not silently declaring SelfHeal RAG dead and picking a new concept. Not
running a third pilot iteration. Not proceeding to Phase 2 on the existing
evidence. This needs your call.

## Options, as I see them (not exhaustive)

1. **Abandon SelfHeal RAG**, same fate as LedgerGuard — go back to the
   ranked candidate list (Sentinel Loop, Corpus Doctor, or Self-Healing RAG
   Engine — the other top-scoring self-healing-RAG variants from the design
   workflow — or a fresh scan) and pre-test the next candidate the same way
   before committing.
2. **One more, materially different pilot** — not just "bigger," but
   targeting the gap this pilot couldn't see: e.g. run B/A0 against
   something closer to the REAL 248-chunk/40-probe scale directly (skip the
   mini stage, spend more of the budget) since a 4× jump showed nothing —
   maybe only a ~20× jump would; or design probes that specifically defeat
   full-context reading (e.g. facts that require aggregating across many
   scattered chunks, not just picking the freshest one).
3. **Keep SelfHeal RAG but retarget the load-bearing capability** — the
   data suggests single-shot retrieval-and-verify isn't where the real gap
   is; the self-improvement LOOP and CROSS-SESSION memory (a fact learned/
   corrected in one session persisting correctly into a later one) were
   always the more structurally distinctive claims in the original dossier
   (constraints doctrine reason (c)) — pilot *that* mechanism specifically
   instead of single-shot QA accuracy.
4. **Something else you specify.**

I'd lean toward option 3 if forced to pick — it's the part of the original
design that was never actually tested by this pilot (the pilot only ever
tested single-shot QA, never a cross-session correction persisting) — but
this is genuinely your call given real hours are at stake.

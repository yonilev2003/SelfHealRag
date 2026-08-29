# Phase 1 — final verdict: PROCEED (retargeted)

## Full arc

1. **Gate run 1** (12 chunks): STOP_TRIVIAL — A0/B both 6/6.
2. **Gate run 2** (60 chunks, 2 decoy supersession pairs, 20 noise docs):
   STOP_2ND_ATTEMPT — identical result. Per CLAUDE.md's hard gate, stopped
   and consulted rather than inventing a third same-hypothesis attempt.
3. **User consulted** (`results/CHECKPOINT_1_FINAL.md`); deferred to my
   judgment among the four options laid out.
4. **Decision:** retarget, don't abandon and don't repeat. Both gate
   failures tested the SAME hypothesis — single-shot QA accuracy over a
   policy corpus — and that hypothesis is confounded by raw model
   capability: no amount of corpus difficulty tuning proves much when
   claude-sonnet-5 with basic tools is simply strong at this task shape
   (the same lesson LedgerGuard already taught). The concept's actual
   distinguishing structural claims — cross-session memory (constraints
   doctrine reason c) and independent verification beating self-consistency
   (reason d/f) — were never tested by either gate.
5. **Focused pretest of the untested mechanism**
   (`eval/pretest-selfheal/run_memory_experiment.py`,
   `results/pretest-selfheal/memory_experiment.json`): three independent
   fresh-context calls over the same 60-chunk corpus, one entity
   (`eng.oncall_stipend_usd`) whose shipped corpus value ($200) is
   *realistically stale* — a raise to $250 was approved out-of-band and
   never reached the handbook doc, exactly the condition a real SMB's docs
   are in.

   | Call | Given | Predicted | Correct? |
   |---|---|---|---|
   | Session 1 | corpus only | $200 | Reads the corpus correctly — but the corpus itself is wrong vs. outside ground truth |
   | Session 2 | corpus + memory note (fresh context, no shared transcript with session 1) | **$250** | Correct — *only* because of the note; nothing in the corpus says $250 |
   | Session 2 control | corpus only (fresh context) | $200 | Reproduces session 1 exactly — isolates the memory note as the cause |

   **`categorical_gap_demonstrated: true`.**

## Why this is airtight in a way the QA gates weren't

Single-shot QA accuracy is *empirically* hard to fail against — you can
keep tuning corpus difficulty and Sonnet-5-with-tools keeps clearing the
bar (2/2 gates). Cross-session memory is *categorically* impossible for a
single-shot call to fake: the correcting fact ($250) exists nowhere in the
corpus. No amount of model capability, retrieval sophistication, or
prompt engineering closes that gap without an actual persistence
mechanism between two independent invocations. This is the clean, binary
ablation the constraints doctrine calls for (memory ON vs. OFF, identical
input otherwise) — and it already exists as real evidence, not a claim.

## What changes in PLAN.md (retargeting, not a rebuild)

The architecture (audit → diagnose → fix → reverify, frozen dev/test split,
fair A0/A/A2/B/C baselines) stays. What changes:

1. **Primary capability claim** shifts from "closes a QA-accuracy gap
   baselines can't" to "persists diagnosed corrections across sessions in a
   way no single-shot config — however strong the model — can replicate."
   The `verifier` component's role expands: it's not just a supersession-
   chain checker, it's what *discovers* the corpus/reality gap that
   `tuner`/memory then persists.
2. **A meaningful share of Phase-2 eval facts must be memory-only
   corrections** (realistic staleness: the corpus is simply out of date on
   some facts, with the correction living only in a diagnosed-and-persisted
   memory record, never re-derivable from the corpus text) — not just
   in-corpus supersession pairs (which both gates proved single-shot
   baselines already handle). This is the new adversarial case class,
   alongside — not replacing — the original supersession/near-dup/multi-hop
   taxonomy.
3. **New required ablation:** memory ON vs. OFF on the memory-only facts,
   identical test cases — this is now a primary-metric-moving row, not a
   stretch goal, because it's where the real, unconfoundable delta lives.
4. **Hero case candidate:** a memory-only correction (like the on-call
   stipend case), not a supersession pair — it's the one case class where
   baselines are *structurally* guaranteed to fail, making it the honest
   "hard case that reveals something real" the kickoff doc asks for.

Full PLAN.md edits follow this checkpoint; Phase 2 begins immediately after.

# Honest review findings — not yet actioned

Recorded 2026-08-29 during V3 video work, per explicit user instruction:
preserve this critique durably without acting on it now. The user wants to
address these separately, after the V3 video closes out. This file is not
linked from README/SUBMISSION/CHANGELOG on purpose — it is a private
punch-list, not part of the pitch.

Nothing below is a rubric violation by itself. These are places where the
project's actual strength is smaller than its presentation makes it sound,
or where a sharp judge would push back. Read alongside `results/*.json` and
`data/probes/test_split.locked.json` before deciding what (if anything) to
change — some of these may be non-issues once re-examined with fresh eyes.

## The good (for context, not the point of this file)
- The core categorical claim (0/3 → 3/3 on `memory_correction`, direct
  ablation, memory ON/OFF with everything else held constant) is real,
  reproducible, and honestly reported alongside the raw aggregate where
  SelfHeal does *not* win (11/16, below A0's 13/16).
- The Phase-4 "test-disjoint entities" bug and its fix is a genuine,
  well-evidenced agentic-engineering story — not manufactured for the demo.
- The killed LedgerGuard concept (archived, not hidden) is a rare, credible
  "we tried something and our own fair baseline killed it" disclosure.

## The bad / the ugly

1. **n=3.** `memory_correction` is 3 cases out of a 16-case frozen test. A
   0/3 → 3/3 flip is dramatic-sounding but is 3 data points. A sharp judge
   will ask for a confidence interval or a larger held-out category before
   accepting "categorical" as strong evidence rather than "n too small to
   generalize." Worth deciding: state the confidence interval explicitly
   next to the claim, or generate more `memory_correction` cases before the
   deadline (if time allows), or leave as-is but be ready to defend it live.

2. **Entity resolution and label matching look pre-solved.** The correction
   signals in `data/correction_signals.json` and the entity index in
   `advanced/verifier.py`/`build_index.py` appear to already know which
   canonical entity a query maps to (static labels, not learned or fuzzy
   resolution). In a real company handbook with messier, overlapping, or
   ambiguous entity names, the hard part — reliably resolving "the weekly
   on-call stipend for engineers" to the *correct* correction-signal entry
   among many candidates — may be doing less real work than the demo
   implies. This is the single most judge-defensible weak point: it's the
   kind of thing that looks solved in a curated 81-chunk corpus and much
   less solved at real scale.

3. **README Section 3 reads like it's claiming staleness *detection*,** when
   what's actually built is closer to a correction-signal *lookup* keyed off
   already-known entity IDs. Worth a precise re-read of that section's
   wording against what the code actually does — if the phrasing overclaims
   relative to the mechanism, tighten it. (Not touching README now, per
   explicit instruction — this is a flag for the later pass.)

4. **3 of 4 "load-bearing" components show zero ablation impact.** Per the
   ablations summary, most of the pipeline's moving pieces (beyond the one
   memory-channel change that actually moved the number) show no measurable
   effect on held-out results. That's honestly disclosed as the video's own
   hot take ("every other ablation we tried showed zero difference"), which
   is good — but it also means the system is architecturally simpler than
   its component count suggests. A judge could reasonably ask "why keep the
   other 3 components if they don't move the metric?" Have an answer ready:
   most plausibly, they exist for correctness/robustness reasons not
   captured by this specific 16-case test, not because they're decorative —
   but that argument isn't yet made anywhere in the writeup.

5. **The agentic-process-vs-shipped-runtime gap.** The Agent Solution &
   Engineering criterion (30%, the heaviest) is scored on the *process* —
   `.claude/workflows/`, `PROCESS.md`, trajectory disclosure, the judge-panel
   and adversarial-verify steps that were actually run. That process is
   real and well-evidenced. But there's a gap between "the engineering
   process used agents extensively and honestly" and "the shipped
   `advanced/` runtime is itself a sophisticated multi-agent system" — the
   shipped system is a fairly linear retrieve→generate→verify→heal
   pipeline, not an agent orchestrating agents at runtime. Worth being
   precise, if asked, about which claim is being made: the *build process*
   was agentic and rigorously verified; the *shipped artifact* is a focused
   pipeline with one well-evidenced capability (self-healing memory), not a
   general-purpose autonomous agent. Conflating the two in a pitch would be
   the kind of overclaim a judge could catch.

## Suggested next pass (not started)

When this gets addressed (after V3 video ships): re-read README.md Section
3 and CHANGELOG.md's hot take with items 2–5 above in hand, decide per-item
whether to (a) tighten wording, (b) add a caveat/limitation note, or (c)
leave as-is with a prepared verbal answer for Q&A. Do not weaken the true,
verified claims (0/3→3/3 ablation, entity-disjoint split, killed
LedgerGuard) — the goal is precision, not modesty.

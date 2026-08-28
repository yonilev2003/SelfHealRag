# PLAN.md — SelfHeal RAG: master build plan (execution runbook)

**Status:** approved concept (user gate passed 2026-08-28). This document is the
runbook for the execution phase, written to be executed mechanically by a
**claude-sonnet-5**-driven session. Judgment-heavy review moments are marked
`FABLE CHECKPOINT` — stop there, the user switches the session to Fable for the
benchmark/review, then back to Sonnet to continue.

**Concept in one sentence:** a working RAG pipeline over a versioned company
policy corpus that audits itself, diagnoses each failure into a structural
category, applies one targeted persistent fix per round, keeps only fixes that
measurably help on a dev split — and proves the result generalizes on a frozen,
pre-registered test split it never saw, against three fair baselines.

**Decision provenance:** 3 selection workflows (44 ideas, ~100 Sonnet agents),
rubric-blind scoring (SelfHeal-RAG: 88.3 mean, highest of all candidates),
4 adversarial grillers, and an empirical pre-test that killed the previous
front-runner (LedgerGuard) when its fair baseline aced it. All grill fixes are
folded in below. Sellability (8.8/10) tracked separately, never added to score.

---

## 0. Non-negotiable invariants (read before every phase)

1. **Oracle isolation.** `data/fact_registry.json` and everything derived from
   it is readable ONLY by `eval/` grading code. No `advanced/` or `baseline/`
   module may import or open it. The verifier's entity index is built by
   `advanced/build_index.py` parsing **raw corpus markdown only** (chunk
   headers: `chunk_id`, `effective_date`, body text incl. any "supersedes"
   language) — never the registry. `make verify-no-leak` greps `advanced/` and
   `baseline/` for `fact_registry|test_split` and fails CI on a hit, and
   re-hashes the locked test split.
2. **Temporal discipline (pre-registration).** Corpus → probes → 24/16
   dev/test split → SHA-256 lock are all committed BEFORE any retriever/
   verifier/tuner code is written. Commit order is the proof; note it in
   PROCESS.md.
3. **Structural novelty in test.** ≥2 trap patterns appear ONLY in the test
   split (a 3-hop supersession chain; an implicit supersession with no
   "supersedes" keyword, only dates). Dev never contains them. Stated in
   PROCESS.md at freeze time.
4. **Primary metric — locked now.** Grounded Answer Accuracy on the frozen 16
   test cases: joint exact-match of (normalized value, exact chunk_id).
   Normalization: strip `$ ₪ ,` + whitespace, casefold; numeric → float
   equality. Secondary breakdowns: value-only, citation-only, per-taxonomy,
   cost/latency, human-time estimate. Grader: `eval/grade_test.py`, stdlib
   only, <60 lines, match logic inline, imports nothing from `advanced/`.
5. **Fairness artifacts.** One shared prompt template file for all arms; same
   model (claude-sonnet-5), same output schema, same chunk formatting.
   Resource differences per arm are enumerated in README (per kickoff p.2).
6. **Budget gates.** Day-1 pilot measures $/call and sec/call; projected full
   eval must be < 40 API-minutes and < ~$15 before proceeding. Cache generator
   outputs keyed by (config_hash, case_id) so ablations reuse identical calls.
7. **Hard gates (CLAUDE.md).** >2 failed fix attempts on the same error →
   stop, show the raw log, consult the user. Deploy-like commands → guarded.
8. **Every claim ← a committed artifact.** Numbers only from
   `results/*.json|csv`. Concede plainly where a baseline ties or wins.
9. **Model policy.** All product agents and any workflow subagents:
   `claude-sonnet-5`. `FABLE CHECKPOINT`s: session switched to Fable by the
   user for review; no build steps run on Fable.

## 1. Repo layout (target state)

```
data/corpus/*.md                  ~35 synthetic Acme Corp policy docs (HR/IT/Finance)
data/fact_registry.json           ORACLE — planted at authoring time (eval-only)
data/probes/all_probes.json       40 probes (10 atomic / 15 contradiction / 10 near-dup / 5 multi-hop)
data/probes/dev_split.json        24 cases
data/probes/test_split.locked.json + .sha256   16 cases, frozen
baseline/prompt_template.md       shared fairness artifact
baseline/run_A_static_rag.py      Arm A: BM25 k=3 → one generation call
baseline/run_A2_agentic.py        Arm A2: same + genuine self-correction (one extra
                                  self-directed BM25 re-query turn before finalizing)
baseline/run_B_generalist.py      Arm B: single generalist agent, Read/Grep/Bash over
                                  the corpus dir (the expensive skyline; LedgerGuard protocol)
advanced/build_index.py           entity index from RAW corpus text only
advanced/retriever.py             BM25Okapi; knobs: k, hybrid_date_boost on/off
advanced/generator.py             temp-0 generation, shared template, JSON out
advanced/verifier.py              DETERMINISTIC (LLM-free): entity lookup → supersession
                                  chain-head from parsed headers → override + reason
advanced/diagnose.py              per-failure taxonomy classification vs dev labels
advanced/tuner.py                 one knob-flip per round, keep/revert by dev delta;
                                  writes advanced/audit_memory.json + selfheal_changelog.md
advanced/run_case.py              one case through the tuned pipeline (flags: --no-verifier etc.)
eval/generate_corpus.py, generate_probes.py, split_and_lock.py
eval/grade_test.py                stdlib grader (invariant #4)
eval/taxonomy.py                  failure classifier (unit-tested against grade_test)
eval/run_eval.py                  orchestrates arms × cases; writes results/
prompts/*.md                      every instruction that shapes each agent (kickoff F1)
results/                          per-case CSV/JSON per arm + receipts
trajectories/                     stream-json per agent incl. pretest evidence
PROCESS.md                        temporal-discipline ledger (what was frozen when)
```

## 2. Phases

### Phase 0 — Housekeeping (~20 min)
Archive the LedgerGuard exploration honestly: move `eval/generate.py`,
`eval/BUSINESS_RULES.md` → `archive/ledgerguard-pretest/` with its README
paragraph; keep `results/pretest/` + `trajectories/pretest/` (evidence for the
changelog's "removed experiment" and the hot take). Update README/PROBLEM
pointers. Commit.

### Phase 1 — PRE-TEST GATE (~1.5 h) — mirrors the protocol that killed LedgerGuard
Draft mini-corpus: 8 docs (~60 chunks) incl. 2 supersession pairs + 1 near-dup
trap. 6 draft probes (NOT reused later). Run:
- Arm B (generalist agent, Read/Grep/Bash, no retriever) on all 6;
- Arm A (static RAG k=3) on all 6;
- text-only single prompt on all 6.
**Decision rule (pre-registered):**
- A fails ≥2/6 staleness probes AND B ≤ 5/6 → proceed (expected; B strong-but-
  imperfect and ~20× cost is the honest skyline story).
- A aces it (≥5/6) → harden corpus difficulty (non-adjacent supersession,
  more distractors) and re-run gate once.
- B == 6/6 in seconds at trivial cost → **stop, report to user** (concept-level
  risk), do not proceed on inertia.
Log everything to `results/pretest-selfheal/`.
**FABLE CHECKPOINT #1:** user reviews gate verdict + Day-1 budget pilot numbers.

### Phase 2 — Corpus, probes, freeze (~4 h)
`generate_corpus.py` (seeded): ~35 docs, ~250 chunks, planted facts with
version chains (explicit + implicit), near-dup distractors, multi-hop pairs;
registry written at authoring time. `generate_probes.py`: 40 probes with
Claude-assisted paraphrasing (trajectory captured), leak-sanity filter (no
probe quotes registry text verbatim). `split_and_lock.py` (seed 42, stratified
24/16, test-only trap patterns per invariant #3), SHA-256 lock, PROCESS.md
entry, commit. **No solution code exists yet at this commit.**

### Phase 3 — Arms (~6 h)
Order: shared template → A → A2 (genuine agentic re-query) → B (LedgerGuard
protocol) → C components (`build_index` → `retriever` → `generator` →
`verifier` → `diagnose` → `tuner`). Unit checks: taxonomy-vs-grader agreement
on a shared sample; verifier zero-false-override target on atomic-fact dev
cases. Every agent prompt lives in `prompts/`.

### Phase 4 — Self-improvement dev loop (~3 h)
Round protocol: clean 24-case dev run → classify failures → plurality taxonomy
→ ONE knob/patch (action space: k, hybrid_date_boost, glossary/synonym entry,
query-rewrite rule, verifier on) → keep iff dev accuracy strictly improves,
else revert (logged). Stop: 2 consecutive no-improvement rounds or 8 rounds.
Output: `selfheal_changelog.md` — the system's own evidence-linked changelog
(feeds CHANGELOG.md). Audit-memory convergence ablation = stretch goal only.

### Phase 5 — Frozen test + ablations (~3 h)
One-time frozen-test run per arm {A, A2, B, C} with `test_run_receipt.json`;
Makefile-enforced ordering; per-case CSV per arm. Core ablation rows (test
config fixed): verifier OFF/ON; tuned vs default config; hybrid OFF/ON; plus
the 3-way structural proof (A vs A2 vs C on contradiction cases). Cost/latency
recorded per arm. Any re-score requires a logged receipt entry tied to a code
bug, never a config change.
**FABLE CHECKPOINT #2:** user reviews full results honestly (incl. any slice
where B or A2 ties/wins) before the story is written.

### Phase 6 — Writeup (~3 h)
README (opens with the four kickoff questions as literal headings; fairness
table; repro guide with pinned versions + measured runtime + measured $).
CHANGELOG.md: baseline row → each kept/reverted round with numbers → the
LedgerGuard removed-experiment row → main failure mode + hot take (pick the
empirically-confirmed hypothesis, e.g. self-ask-doesn't-catch-stale-facts with
the actual case id + quoted outputs). Trajectories manifest. CI green.

### Phase 7 — Video + packaging (~3 h)
VIDEO_SCRIPT.md beats (cold open: before/after transcript of the stale-$500
case; A2 failing the double-check; live C run with verifier override JSON;
frozen-test table; changelog + removed experiment; hot take). Record terminal
demo (script + asciinema/Playwright), assemble ≤5 min with ffmpeg, host, get
URL. `scripts/package_submission.sh`: zip < 50 MB, secret scan, size audit.
Draft submission Title + Description.
**FABLE CHECKPOINT #3 (final):** user reviews video, zip, submission text
against COMPLIANCE.md; only then submit.

## 3. Schedule vs deadline (deadline Aug 30 23:59 UTC)
Phases 0-2 tonight (Aug 28); 3-4 by Aug 29 evening; 5 Aug 29 night; 6-7
Aug 30 by ~18:00 UTC → ~6 h buffer. Slack absorbs one full re-run of Phase 4-5.

## 4. Risk register (with pre-registered fallbacks)
- **B near-parity on test** → honest reframe (deterministic guarantees +
  ~20×/case cost + latency + per-case slices where B fails), pre-registered
  here, not invented post-hoc.
- **Corpus too easy/too rigged** → Phase-1 gate + one hardening iteration max.
- **16-case variance** → per-case CSVs + concession sentences; never hide.
- **Budget blowout** → cache + Day-1 pilot extrapolation gate.
- **Scope** → cut order (pre-agreed): audit-memory ablation → H2 sycophancy
  bonus ablation → Hebrew slice (already optional) → nothing else cuttable
  without user approval.

## 5. Hebrew extension (optional, user decides at execution gate)
Isolated module after Phase 5 only if ≥4 h slack remains: 5 Hebrew docs + 4
test-only Hebrew probes + glossary-memory fix for cross-lingual vocabulary
mismatch; reported as a separate labeled slice, never mixed into the primary
metric. Default if time is short: documented future-work in README + LinkedIn
post angle.

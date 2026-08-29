# PLAN.md — SelfHeal RAG: master build plan (execution runbook, rev 4 — RETARGETED)

**Status:** approved concept (user gate 2026-08-28). Rev 2 folded in all 36
blocking fixes from a 5-attacker adversarial grill of rev 1; rev 3 folds in
the 10 remaining blockers from the verification re-grill. **Rev 4** folds in
a real Phase-1 finding: two live pre-test gates (12 chunks, then 60 chunks
with 2 decoy supersession pairs + 20 noise docs) both hit STOP on the
single-shot-QA-accuracy hypothesis — claude-sonnet-5 with basic tools (Arm
B, the PDF's own fair baseline) and even a full-context single prompt (A0)
solved it cleanly both times. Per CLAUDE.md's hard gate (2 failed attempts
= stop and consult), the user was consulted and deferred to a retargeting:
not a 3rd attempt at the same hypothesis, but a focused pretest of the
concept's actual distinguishing claim — cross-session memory — which the
two QA gates never touched. That pretest (`results/pretest-selfheal/
memory_experiment.json`) demonstrated a categorical, unconfoundable gap:
a fact whose correction lives only in a persisted memory note (never in
the corpus) is unreachable by any single-shot call regardless of model
strength. Full arc in `results/CHECKPOINT_1_MEMORY_VERDICT.md`. This
revision retargets Phase 2 onward around that mechanism — same
architecture, same rigor, different primary capability claim.

**Execution mode:** this runbook is executed DIRECTLY by a
**claude-sonnet-5**-driven session, phase by phase — not via the
`hackathon-sprint` workflow (its plan/ideation stages are superseded by this
document; `hackathon-fix` remains available for targeted bug-hunt rounds).
Judgment-heavy review moments are marked `FABLE CHECKPOINT` — the user switches
the session to Fable there for benchmarking/review, then back to Sonnet.

**Concept in one sentence:** a working RAG pipeline over a versioned company
policy corpus that audits itself, diagnoses each failure into a structural
category, applies one targeted persistent fix per round, keeps only fixes that
measurably help on a dev split — and proves the result generalizes on a frozen,
pre-registered test split it never saw, against fair baselines.

**Decision provenance:** 3 rubric-blind judge panels across the full process
(LedgerGuard: 2 panels, 24 ideas; SelfHeal RAG: 1 larger panel, 27 ideas — 51
ideas total, ~100 Sonnet agents), SelfHeal RAG's pick then adversarially
grilled twice (5 attackers × 2 rounds, 46 blocking issues found and
resolved — see rev 2/rev 3 notes above), and an empirical pre-test that
killed the previous front-runner (LedgerGuard, which had itself scored
highest at 88.3 across its own two panels) when its fair baseline aced it.
Sellability (8.8/10) tracked separately, never added.

---

## 0. Non-negotiable invariants

1. **Oracle isolation.**
   - The oracle = `data/fact_registry.json` + `data/probes/test_split.locked.json`.
     Readable ONLY by `eval/` grading code. **Scope clarification:**
     `data/probes/dev_split.json`'s expected answers ARE permitted inputs to
     `advanced/diagnose.py` / `advanced/tuner.py` — that is ordinary dev-set
     tuning, not a leak. The prohibition binds the registry and the test split.
   - `advanced/build_index.py` parses ONLY raw `data/corpus/*.md` (headers:
     `chunk_id`, `effective_date`, body incl. any supersession language) —
     never the registry.
   - **Arm B sandbox (runtime isolation, not prompt policy):** Arm B runs with
     cwd = a throwaway tempdir containing a copy of `data/corpus/*.md` ONLY.
     Phase 1 first tests the SDK's `sandbox` option (filesystem confinement to
     the tempdir); if functional, it is the preventive boundary. Regardless,
     `scripts/audit_arm_b.py` runs post-hoc on the trajectory: it tracks
     cumulative `cd` state across the whole shell session, resolves every
     relative/`..`/symlink path against that state, scans Write-tool payloads
     that later execute, and scans tool OUTPUTS for oracle fingerprints (known
     probe_ids / registry keys). **Remediation protocol:** any flagged case is
     discarded and rerun once in a fresh sandbox; both runs logged in the
     receipt. cwd alone is a starting directory, not a boundary — the audit is
     the enforcement.
   - **`make verify-no-leak` (real target, wired into CI before any Phase-3
     commit):** (a) grep `advanced/ baseline/ prompts/` for
     `fact_registry|test_split|all_probes`; (b) source code may reference
     `data/` ONLY via explicit filenames — any wildcard/listing call
     (`glob|os.listdir|iterdir|os.walk`) against `data/` in `advanced/` or
     `baseline/` is a violation; (c) re-hash `test_split.locked.json`,
     `dev_split.json` AND `data/fact_registry.json` against digests recorded
     inline in PROCESS.md (not only co-located `.sha256` files).
   - **The pre-split pool never enters git.** `generate_probes.py` writes
     `all_probes.json` to the session scratchpad (outside the repo); only the
     two split files are committed. Nothing in git history can restore the
     full pool.
   - **Session no-peek rule:** after the freeze commit, no Read/Grep/Bash call
     in the building session may target the registry or the test split until
     the whitelisted Phase-5 frozen run — including via git history
     (`git show|log -p|diff|cat-file|checkout` against oracle paths).
     `scripts/audit_no_peek.py` scans session trajectories for both direct
     and git-mediated access AND scans Bash outputs for oracle fingerprints;
     PROCESS.md states plainly that commit order is necessary but not
     sufficient and this audit is the enforcement. Post-freeze edits to the
     registry or either split file require a PROCESS.md entry with reason.
   - `prompts/*.md` few-shot examples must not reuse planted registry facts —
     examples use a disjoint toy domain.
2. **Temporal discipline.** Corpus → probes → split → locks committed BEFORE
   any retriever/verifier/tuner code exists. The video's "hero case" is
   pre-registered at freeze time (see Phase 2), never chosen post-hoc.
3. **Structural novelty in test.** Implicit (dates-only) supersession probes
   and 3-hop-chain probes exist ONLY in the test split (counts in Phase 2).
4. **Primary metric — locked.** Grounded Answer Accuracy on the frozen 16:
   joint exact-match (normalized value, exact chunk_id). Normalization lives
   in `eval/match.py` (single shared module imported by BOTH `advanced/tuner.py`
   dev scoring and `eval/grade_test.py`): strip `$ ₪ ,` + whitespace, casefold,
   numeric → float equality. `eval/grade_test.py`: stdlib, <60 lines, no
   imports from `advanced/`. **Every case is scored regardless of
   REQUIRES_HUMAN_REVIEW — the flag is metadata, never a scoring exclusion;
   flagged-but-wrong counts wrong, flagged-but-correct counts correct. A
   no-entity-match emits a real prediction (`value:"", chunk_id:"NONE"`) that
   naturally scores wrong — never an excluded sentinel.** Secondary:
   value-only, citation-only, per-taxonomy, cost, latency, human-time
   (methodology in Phase 5).
5. **Fairness artifacts.**
   - One shared `baseline/prompt_template.md`: a TASK+OUTPUT-SCHEMA block used
     verbatim by every arm + a per-arm I/O preamble (injected chunks for
     A/A2/C; corpus-dir access for B). Frozen at end of Phase 3 (PROCESS.md
     entry); Phase-4 tuning touches ONLY `advanced/` config knobs.
   - Identical decoding params for ALL arms: temperature 0, same max_tokens,
     same model `claude-sonnet-5`.
   - **Chunk parity:** the chunk string rendered into A0/A/A2/C prompts (A0's
     inline whole-corpus rendering included) comes from ONE shared rendering
     function and is byte-identical per chunk_id (header incl. effective_date
     + body) to what `build_index.py` parses; a unit test asserts this.
   - A, A2, C import and call the SAME `advanced/retriever.py` /
     `generator.py` functions (single source, no copies); only knob values
     and control flow differ. `prompts/a2_recheck.md` is frozen at end of
     Phase 3 together with the shared template (same PROCESS.md entry).
   - **`correction_signals.json` access (rev 4, the one deliberate asymmetry
     — stated explicitly, per invariant #8's "explain any meaningful
     difference in resources" and kickoff p.2):** NONE of A0/A/A2/B ever
     receive it, at any point, including A0's otherwise-total corpus access.
     Only Arm C's `diagnose`/`tuner` loop reads it, during the Phase-4 dev
     loop only (never at Phase-5 frozen-test time — the frozen run uses
     whatever memory state Phase 4 already persisted). Rationale, stated in
     README: this mirrors a real production RAG bot, which indexes the
     policy corpus and has no connection to a separate ticketing system —
     the differentiator under test is exactly whether the agentic system
     proactively bridges that gap and persists the result, not whether any
     arm can read more text in one call (that was already conceded to
     Sonnet-5-with-tools by both Phase-1 gates).
   - Arm resource differences are enumerated in README (kickoff p.2).
6. **Budget gates — enforced, not eyeballed.** `eval/check_budget.py` (stdlib)
   reads pilot receipts, projects full-eval cost/time (applying a corpus-size
   scaling factor to Arm B's per-case cost, not just case count), and
   hard-fails (non-zero exit, in Makefile) if projection ≥ 40 API-minutes or
   ≥ $15. Scaling formula (pinned): Arm B's projected per-case cost/time =
   mini-pilot measurement × (248 full-corpus chunks ÷ mini-corpus chunk
   count) — validated against the two real Phase-1 gate runs (12 and 60
   chunks; both projected comfortably under budget). Generator calls cached
   keyed by **(case_id, config_hash)** — config_hash = SHA of {retriever_k,
   hybrid_date_boost, glossary_version, rewrite_rules_version,
   **memory_version**, prompt_template_hash, model_id}; verifier on/off is
   EXCLUDED (it runs post-generation and must never gate the cache).
   `memory_version` increments each time `advanced/memory.json` gains a new
   persisted correction, so a memory-affected answer is never served from a
   cache entry keyed to a pre-correction state. Unit tests: two distinct
   knob settings hash differently; two distinct case_ids never collide. The
   official frozen run must report 100% cache-miss in its receipt.
7. **Hard gates (CLAUDE.md).** >2 failed fix attempts on one error → stop,
   show the raw log, consult the user. Deploy-like commands → guarded hook.
8. **Every claim ← a committed artifact.** `eval/run_eval.py`'s frozen path
   auto-appends {timestamp, git SHA, output hash} to `results/test_run_log.md`
   on EVERY invocation. **Bug fix vs config change (operational):** a bug fix
   changes control-flow/parsing logic and ships a new unit test that fails on
   the old code and passes on the new, independent of test-split outcomes;
   any threshold/knob/prompt-wording change is a config change and is never
   eligible for a re-score. When a re-score occurs, the writeup shows pre-fix
   and post-fix numbers side by side. Concede plainly wherever a baseline
   ties or wins.
9. **Model policy.** Product agents + workflow subagents: `claude-sonnet-5`.
   FABLE CHECKPOINTs are user-driven review stops (protocol per checkpoint).

## 1. Repo layout (target)

```
data/corpus/*.md                    34 docs / 248 chunks (exact; generator asserts)
data/correction_signals.json        NEW (rev 4): ~10 ticket/audit-note texts, one per
                                    memory_correction fact; NEVER read by any
                                    baseline (A0/A/A2/B) -- only advanced/diagnose.py
data/fact_registry.json             ORACLE (eval-only); memory_correction entries
                                    carry BOTH stale_documented_value and value
data/probes/{all_probes.json (session-scratchpad only, never committed),
             dev_split.json, test_split.locked.json, *.sha256}
baseline/prompt_template.md         shared TASK+SCHEMA + per-arm preambles
baseline/run_A0_fullcontext.py      Arm A0: whole corpus inline, one call, no retrieval
baseline/run_A_static_rag.py        Arm A: BM25 k=3 → one call
baseline/run_A2_agentic.py          Arm A2: A + EXACTLY ONE forced re-query turn
                                    (fixed self-critique prompt prompts/a2_recheck.md)
baseline/run_B_generalist.py        Arm B: generalist agent in corpus-only tempdir;
                                    max_turns=25, 8-min/case timeout, cost logged;
                                    cap hit → scored as-is and noted
advanced/build_index.py             entity index from RAW corpus text only
advanced/retriever.py               BM25Okapi; knobs: k ∈ {3,5,7,10}, hybrid_date_boost
advanced/generator.py               shared template, temp-0, JSON out; ALSO checks
                                    advanced/memory.json for a persisted correction
                                    matching the answer's entity_key and injects it
                                    into the prompt if present (the pretest's proven
                                    session-2-with-memory mechanic, productionized)
advanced/verifier.py                DETERMINISTIC (LLM-free): entity lookup →
                                    supersession chain-head from parsed headers →
                                    override + reason + REQUIRES_HUMAN_REVIEW flag
                                    (fires on: no entity match / conflicting chain /
                                    override applied)
advanced/memory.json                NEW (rev 4): persisted {entity_key: {value,
                                    source_signal_id, round_added}} corrections;
                                    starts empty; grows only via diagnose/tuner
                                    below; memory_version = length, feeds config_hash
advanced/diagnose.py                deterministic taxonomy classifier (Phase 4 table);
                                    ALSO checks data/correction_signals.json against
                                    each miss's entity_key (never against the oracle
                                    directly -- consults the signal text, same as a
                                    human triaging a ticket would)
advanced/tuner.py                   one action per round per mapping table; keep iff
                                    dev accuracy improves by ≥2 cases; writes
                                    audit_memory.json + selfheal_changelog.md +
                                    advanced/memory.json (memory writes are never
                                    reverted even if a round's OTHER knob change is --
                                    a correction confirmed against a real signal is
                                    kept independent of that round's net verdict)
advanced/run_case.py                flags --no-verifier --no-hybrid --no-memory --k N
eval/{generate_corpus,generate_probes,split_and_lock,run_eval,grade_test,
      taxonomy,match,check_budget}.py
eval/score.py                       thin wrapper → {baseline, advanced, delta} JSON
                                    (keeps Makefile/CI/workflow contracts alive)
scripts/run_baseline.sh             runs arms A0+A+A2+B → results/
scripts/run_advanced.sh             runs arm C → results/
scripts/{audit_arm_b,audit_no_peek}.py
prompts/*.md                        every instruction shaping each agent
results/                            per-case CSVs per arm, receipts, test_run_log.md
trajectories/ + MANIFEST.md         per-agent, hand-mapped (role, phase, arm, retries)
PROCESS.md                          temporal-discipline ledger + inline hashes
```

## 2. Phases

### Phase 0 — Housekeeping (~0.5 h)
Archive LedgerGuard exploration → `archive/ledgerguard-pretest/` (generator,
BUSINESS_RULES; keep `results/pretest/` + `trajectories/pretest/` as removed-
experiment evidence). Purge stale "Frontier Engineering Challenge"/HackerEarth
framing from README/TOOLKIT/HANDOFF (CLAUDE.md is authoritative). Commit.

### Phase 1 — PRE-TEST GATE (~1.5 h + gate)
Mini-corpus: 8 docs (~60 chunks), 2 supersession pairs (1 explicit, 1
implicit) + 1 near-dup trap. 6 draft probes (schema below; NOT reused later).
Run text-only (A0-mini), static RAG (A-mini), generalist agent (B-mini, in the
Arm-B sandbox) on all 6. Budget pilot: measure $/call + sec/call per arm →
`eval/check_budget.py` projection (with Arm-B corpus-size scaling).
Probe mix (pinned): 3 staleness (2 on the explicit pair, 1 on the implicit
pair) + 1 near-dup + 2 atomic.
**Pre-registered decision rule — evaluated in this order:**
1. B-mini == 6/6 OR A0-mini == 6/6 (trivially, i.e. no probe missed) → STOP,
   report to user. This rule short-circuits everything below.
2. PROCEED iff: A-mini fails ≥2 of the 3 staleness probes AND B-mini ≤5/6 AND
   A0-mini ≤5/6 AND the budget projection passes.
3. Otherwise (A-mini or A0-mini too strong) → apply the hardening recipe ONCE
   and re-run the gate: (a) +2 distractor chunks per supersession pair; (b)
   superseding fact's effective_date ≥90 days after v1; (c) supersession
   language ≥3 chunks away from the superseded fact chunk; (d) implicit pair
   loses any "supersede" keyword entirely.
4. Second gate run not PROCEED (in ANY direction) → 2nd failed attempt under
   CLAUDE.md's hard gate: STOP, show both per-probe pass/fail tables, consult
   the user. No third pass, no proceed-on-inertia.
**FABLE CHECKPOINT #1 (soft):** write `results/CHECKPOINT_1.md` (gate tables +
budget projection + verdict). If verdict is PROCEED — post it and continue;
any STOP branch ends the turn and waits for the user.

### Phase 2 — Corpus, probes, freeze (~4.5 h)
- `generate_corpus.py` (seed 42): exactly 34 docs / 248 chunks, Acme Corp
  handbook (HR/IT/Finance); registry written at authoring time; version chains
  (explicit + implicit + one 3-hop), near-dup distractors, multi-hop pairs
  — AND, per the rev-4 retarget, a class of **deliberately stale documented
  facts** (the corpus states a value that is realistically out of date).
  Script asserts exact counts on exit.
- **`data/correction_signals.json` (NEW, rev 4):** ~10 short synthetic
  "operational exhaust" texts (support-ticket transcripts, audit notes) —
  a system DIFFERENT from the policy corpus, exactly mirroring the pretest's
  `memory_experiment.json` finding. Each stale fact from the corpus has
  exactly one corresponding signal document mentioning its true current
  value in passing (never phrased as "the handbook is wrong", so it isn't
  a giveaway — realistic ticket prose). `fact_registry.json` records BOTH
  values per such entity: `stale_documented_value` (what the corpus says)
  and `value` (the true current one, matching what the signal implies).
  Baselines (A0/A/A2/B) are NEVER given `correction_signals.json` — not
  withheld unfairly, but because in the real-world analogy it's a different,
  unindexed system (see invariant #5 update below); this is the load-bearing
  design difference from every other probe category.
- Probe schema (literal): `{"probe_id": str, "question": str,
  "expected_value": str, "expected_chunk_id": str,
  "category": "atomic|contradiction|near_dup|multi_hop|memory_correction",
  "trap_subtype": "none|explicit_supersession|implicit_supersession|
  2hop_chain|3hop_chain|stale_no_memory", "construction_seed": int}`.
  For `memory_correction` probes, `expected_chunk_id` is `"MEMORY"` (no
  corpus chunk supports the correct answer — matching the pretest's schema).
- 40 probes: atomic 8; contradiction 12 (9 explicit + 3 implicit); near-dup
  8; multi-hop 4 (3 two-hop + 1 three-hop); **memory_correction 8** (trap
  subtype `stale_no_memory`). Claude-assisted paraphrasing (trajectory
  captured). Leak filter (exact): reject any probe whose question shares a
  contiguous case-insensitive substring of ≥10 tokens with any corpus chunk,
  any fact_registry.json string, OR any correction_signals.json string.
  `split_and_lock.py` asserts dev ∩ test = ∅ and dev ∪ test = all 40; the
  assertion result is logged in the PROCESS.md freeze entry, alongside a
  plain-language "what a good result looks like for the intended user"
  statement (E2) written BEFORE any scored run.
- `split_and_lock.py` (seed 42), exact partition: atomic 5 dev / 3 test;
  contradiction 7 dev / 5 test (3 implicit forced into test); near-dup 5
  dev / 3 test; multi-hop 2 dev / 2 test (the 3-hop forced into test);
  memory_correction 5 dev / 3 test (per invariant #3, this whole category's
  trap subtype is structurally novel to the mechanism — additionally force
  at least 1 of the 3 test memory_correction cases to be a paraphrase never
  seen in dev, not just a held-out row id). = 24 dev / 16 test. SHA-256 of
  all three artifacts (corpus registry, correction signals, both splits)
  into PROCESS.md inline + `.sha256` files. Archive `all_probes.json`
  (kept out of git entirely per invariant #1, not just moved).
- **Hero-case pre-registration (rev 4):** one `memory_correction` test probe
  (an on-call-stipend-shaped case, mirroring the pretest exactly) is
  designated in PROCESS.md at freeze time as the video/README hard case —
  by construction, not post-hoc. This supersedes rev 3's refund-cap choice:
  the refund-cap supersession case is exactly the shape both Phase-1 gates
  proved baselines already handle, so it no longer earns the "hard case
  that reveals something real" slot (kickoff doc E5) — a memory-only
  correction is the one case class baselines are structurally guaranteed
  to fail, which is what makes it honest, not rigged.
- Commit ("freeze"). No solution code exists at this commit.

### Phase 3 — Arms (~6.5 h)
Build order: `eval/match.py` → shared template → A0 → A → A2 (protocol: always
exactly one additional forced BM25 re-query turn using `prompts/a2_recheck.md`,
then final answer) → B (sandboxed; budget caps) → C components (`build_index` →
`retriever` → `generator` → `verifier` → `diagnose` → `tuner`) →
`eval/score.py` wrapper → `scripts/run_baseline.sh` (A0+A+A2+B) /
`run_advanced.sh` (C) → `make verify-no-leak` in CI. Unit checks: taxonomy-vs-
grader agreement on a shared sample; chunk-parity test; config-hash test;
verifier zero-false-override on atomic dev cases. Freeze the prompt template
(PROCESS.md entry).

### Phase 4 — Self-improvement dev loop (~3 h)
**Failure taxonomy (fixed now, deterministic, vs dev labels).** Priority
order — used uniformly for per-case classification precedence when multiple
conditions match, plurality tie-breaks, and next-category moves:
`memory_correction_missed` (predicted value = the stale documented value on
a `memory_correction`-category case; NEW, rev 4 — the pretest's proven
mechanism, now the highest-priority category since it's the one baselines
are structurally guaranteed to fail) > `retrieval_miss` (gold chunk not
retrieved) > `stale_value_uncaught` (gold retrieved; predicted value = a
superseded planted value; no override) > `hallucinated_citation` (value
correct, cited chunk not a valid source) > `wrong_override` (verifier
overrode a correct answer) > `wrong_value_other`. `correct` is terminal.
Unit check: `taxonomy.py`-vs-`grade_test.py` agreement on the shared sample
must be **100%** (both are deterministic).
**Arm C round-0 config (pinned):** k=3, hybrid_date_boost=OFF, verifier=OFF,
glossary_version=0, rewrite_rules_version=0 — identical retrieval config to
Arm A; the Phase-5 "tuned vs default" ablation compares final locked config
vs exactly this round-0 config.
**Taxonomy → action mapping (closed sets, in order; one action per round):**
- **memory_correction_missed → consult `data/correction_signals.json` for
  the case's entity_key (never the oracle); if a signal document mentions
  it, extract the stated value via a temp-0 Sonnet call
  (`prompts/signal_extractor.md`, given ONLY the signal text + the entity_key
  — no oracle, no other dev cases) and write `{entity_key, value,
  source_signal_id, round_added}` to `advanced/memory.json`. This write is
  KEPT unconditionally (never reverted by the round's keep/revert check —
  see the repo-layout note on `tuner.py`), because it's confirmed against
  an actual signal document, not a guess.**
- retrieval_miss → k ∈ {5,7,10} (first untried), then query-rewrite rule, then
  glossary entry.
- stale_value_uncaught → verifier ON (once); if already ON → hybrid_date_boost.
- wrong_override → hybrid_date_boost toggle; if tried → revert last glossary.
- hallucinated_citation → verifier ON (its citation check); then rewrite rule.
- Glossary/rewrite text is authored by a temp-0 Sonnet call
  (`prompts/glossary_author.md`) given ONLY the failing dev cases' questions +
  retrieved chunks (no oracle), must cite motivating dev case ids in
  `selfheal_changelog.md`.
**Round protocol:** clean 24-case dev run (cache-aware) → classify → plurality
category → mapped action → KEEP iff dev accuracy improves by **≥2 cases**,
else revert (logged). Recurring plurality with exhausted actions → counts as
no-improvement, move to next category. Stop: 2 consecutive no-improvement
rounds or 8 rounds (cuttable to 5). Output: `selfheal_changelog.md`.

### Phase 5 — Frozen test + ablations (~3 h; FINAL by Aug 30 ~12:00 UTC)
One-time frozen run per arm {A0, A, A2, B, C}: receipts (incl. per-arm call
counts) + 100% cache-miss + auto-appended `test_run_log.md`.

**PRIMARY causal row (rev 4 — the categorical proof, promoted from stretch
to required):** memory ON (C as actually built, `advanced/memory.json`
populated by Phase 4) vs. memory OFF (C re-run with `--no-memory`, i.e. the
`generator.py` memory-lookup step disabled, everything else identical),
scored on the 3 `memory_correction` test cases. Expected, mirroring
`results/pretest-selfheal/memory_experiment.json` exactly: memory-OFF
reproduces the baselines' stale answer on every one; memory-ON gets the
true current value on every case whose signal was successfully diagnosed
in Phase 4. Any case where memory-ON still fails is reported honestly
(diagnosis didn't fire in Phase 4) — not hidden.

**Secondary ablations** at C's final locked config, retrieval knobs held
fixed: verifier OFF/ON (the in-corpus-supersession causal row — still
real, just no longer the headline); tuned vs round-0 config; hybrid OFF/ON.

**Required deliverable — the 3-way structural proof:** per-case join of A0/
A/A2 vs C over every `memory_correction` test case (the category where the
gap is categorical, not just empirical) AND every `contradiction` test
case (dev too, for power): the count and list of cases where every baseline
fails identically and only C (via memory or the independent verifier)
succeeds. This row is the requires-agents-not-a-longer-prompt evidence,
now with two independent supporting mechanisms instead of one; if the
contradiction-category slice comes out empty (plausible — both Phase-1
gates suggest it might, since baselines are strong there), that is reported
honestly and the story rests on the memory_correction slice, which the
pretest already de-risked.

Per-case CSV per arm. Cost/latency measured per arm. **Human-time row
methodology (disclosed):** B's measured wall-clock as the agent-as-analyst
proxy + a labeled modeled estimate for a human (stated assumptions:
read/cross-check ~15 chunks per question at ~20 sec/chunk, PLUS — for
memory_correction cases only — an added estimate for a human manually
noticing and cross-referencing a ticket against the handbook, since that's
the real task those cases represent), never presented as measured human
data.
**FABLE CHECKPOINT #2 (hard stop):** write `results/CHECKPOINT_2.md` (all
tables incl. slices where any baseline ties/wins). End turn; wait for user.

### Phase 6 — Writeup (~3 h)
README: four kickoff questions as literal headings; capability story leads
with **cross-session memory persistence** (rev 4's headline, categorically
proven in the pretest — link `results/pretest-selfheal/memory_experiment.json`
as the earliest evidence of this exact mechanism) alongside the other 3
load-bearing choices (deterministic independent verification; structural
retrieval knobs; self-correcting tuning loop) with infra framed as
infra; fairness table; **results table** (primary metric + human-time + cost
rows × A0/A/A2/B/C, sourced from Phase-5 receipts); **"What the hard case
revealed"** section (hero case, quoted A/A2 vs C outputs); Human-review
section (G4: REQUIRES_HUMAN_REVIEW semantics + banner in the answer
artifact); polished example Q&A transcript (the end-user deliverable); repro
guide (pinned versions, measured runtime, measured $; note that CI runs
lint/unit/leak checks always and skips API-calling targets without
`ANTHROPIC_API_KEY`, with a skip notice — full repro requires the key);
pre-competition boundary (scaffold tag `5aa5839` + kickoff-fill `49a647a`,
both stated). **Claims-vs-evidence audit:** before packaging, every number
in README/CHANGELOG is grepped against `results/*.json|csv`; any unmatched
claim is fixed or deleted (G7). CHANGELOG.md: baseline row → kept/reverted rounds
with numbers → LedgerGuard removed-experiment row (real pretest numbers) →
main failure mode + hot take (the empirically confirmed hypothesis with case
id + quoted outputs). Trajectories MANIFEST hand-mapped. CI green.

### Phase 7 — Video + packaging (~3 h)
Beats (≤5:00): 0:00-0:30 cold open — before/after transcript of the
memory-correction hero case (all baselines confidently give the stale
handbook value; C gives the true current one, citing "MEMORY"); 0:30-1:15
problem + A0/A/A2/B all failing identically on camera (the categorical gap,
not a cherry-picked miss); 1:15-2:45 one GENUINE unedited C run: Phase-4
diagnose step reading the correction signal live, writing to
`advanced/memory.json`, then a frozen-test query correctly citing it
(speed-ups disclosed); 2:45-3:45 the in-corpus verifier catching a
supersession case, as the secondary mechanism; 3:45-4:30 frozen-test table
+ changelog + the LedgerGuard removed experiment; 4:30-5:00 hot take. Recording: `script`/
asciinema of real executions; assemble with Playwright-bundled ffmpeg. Hosting:
private Artifact page with embedded video (≤16MB data-URI) — Vercel fallback;
URL into the submission form. `scripts/package_submission.sh`: zip <50MB,
secret scan, size audit. Draft Title + Description.
**FABLE CHECKPOINT #3 (hard stop):** `results/CHECKPOINT_3.md` + video + zip +
submission text vs COMPLIANCE.md. User submits.

## 3. Schedule (deadline Aug 30 23:59 UTC)
Critical path = 24.5 h of phase estimates + ~1 h Phase-1 gate wait = ~25.5 h.
Tonight (Aug 28): Phases 0-2. Aug 29: Phases 3-4 by evening, Phase 5 at
night. **Phase 5 FINAL by Aug 30 12:00 UTC.** Aug 30 afternoon: Phases 6-7
done by ~19:00 UTC. Two separate slack pools: (a) the Aug 30 00:00-12:00
contingency window (~12 h wall-clock, enough for the full 6 h of a Phase 4-5
re-run — triggered only by a CHECKPOINT-2 verdict of "results unusable"; the
frozen re-run legitimately reports fresh cache misses and is logged in
`test_run_log.md`); (b) ~4 h final-day buffer after 19:00 UTC. They are not
the same hours.

## 4. Risk register (pre-registered fallbacks)
- **B near-parity with C** → honest reframe: deterministic guarantees +
  measured cost/latency multiplier (expected order-of-magnitude, reported as
  measured) + per-case slices; pre-registered here.
- **Corpus too easy** → Phase-1 recipe, once; second failure = hard stop.
- **16-case variance** → per-case CSVs + concession sentences.
- **Budget** → check_budget.py hard gate + cache.
- **Cut order.** Stretch items (NOT in the critical-path ledger; dropped
  first at zero schedule impact): H2 sycophancy bonus ablation
  (verifier-blind vs CoT-visible, dev only, ~1 h if attempted) and
  audit-memory convergence ablation (~1 h if attempted). Real critical-path
  cuts, in order: Hebrew slice (~4 h, already optional) → dev-loop cap 8→5
  rounds (~1 h) → drop A0 from the frozen table, keep as pretest evidence
  (~0.5 h). Nothing else without user approval.

## 5. Hebrew extension (optional; user decides at CHECKPOINT #2)
Isolated post-Phase-5 module iff ≥4 h slack: 5 Hebrew docs + 4 test-only
Hebrew probes + glossary-memory cross-lingual fix; separate labeled slice,
never mixed into the primary metric. Otherwise: documented future-work.

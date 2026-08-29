# Improvement Changelog

This file is the actual judged artifact (Measured Improvement 15%, Hot
Take/Insights 5%), not paperwork — entries are added as decisions are made,
not reconstructed from memory at the end (per `CLAUDE.md`).

| Stage | What we tried and why | Evidence | Decision / learning |
|---|---|---|---|
| Concept selection: LedgerGuard | Cross-source revenue reconciliation agent. Chosen after 2 independent rubric-blind judge panels (24 candidate ideas total) scored it highest, with a mechanically-planted oracle and a "tool-mediated ground truth" structural argument for why a single prompt should fail. | `results/pretest/*.json`: text-only baseline 1.44% error, 24.6 min, $3.55. **Single generalist agent with basic tools (the PDF's own fair baseline): 0.00% error, 2.3 min, $0.42.** | **Removed.** The fair baseline the kickoff document itself specifies already solved the task exactly, faster and cheaper. Deterministic, rule-following arithmetic over structured CSVs is exactly what a single generalist agent with tools is good at — orchestration would have measured zero delta against its own baseline. Full writeup: `archive/ledgerguard-pretest/README.md`. |
| Concept selection: SelfHeal RAG | Self-improving RAG pipeline over a versioned policy corpus: closed audit→diagnose→fix→reverify loop, generalizing to a frozen held-out split. Selected via a second, larger rubric-blind scan (27 ideas) explicitly steered toward "a single prompt structurally cannot do this" + the participant's own domain (RAG/data-analytics), then adversarially grilled twice (5 attackers × 2 rounds, 46 blocking issues found and resolved) before any code was written. | `PLAN.md` rev 1→3 diff; grill transcripts (`/workflows` run history). | **Adopted**, on the condition that Phase 1's empirical pre-test gate (same LedgerGuard protocol — generalist-agent-with-tools baseline vs. the concept) confirms the structural gap actually exists before committing further build time. |
| Pre-test: SelfHeal RAG single-shot QA hypothesis | Piloted whether a small (12-chunk) then scaled (60-chunk, +2 decoy supersession pairs +20 noise docs) corpus would show static-RAG-vs-agent QA-accuracy gaps, mirroring the LedgerGuard protocol. | `results/CHECKPOINT_1_FINAL.md`: both runs, A0=6/6 and B=6/6 (identical, down to the same single Arm-A miss on both runs). | **Retargeted, not abandoned.** Two consecutive real gates hit CLAUDE.md's hard stop (>2 failed attempts, same hypothesis) — single-shot QA accuracy is confounded by Sonnet-5's raw capability, the same lesson LedgerGuard taught. User consulted; deferred to my judgment. |
| Pre-test: cross-session memory hypothesis | Tested the concept's actually-distinctive claim instead: can a fact whose correction lives ONLY in a persisted memory note (never the corpus) be answered correctly by a fresh, memory-equipped call, vs. reproducing the stale corpus answer with no memory? | `results/pretest-selfheal/memory_experiment.json`: session 1 (no memory) → $200 (stale); session 2 + memory note (fresh context) → **$250 (true)**; session 2 control (no memory) → $200 again. `categorical_gap_demonstrated: true`. | **Adopted, PLAN.md retargeted (rev 4).** This gap is categorical (information-theoretically absent from the corpus), not empirical — unlike QA accuracy, no model capability closes it without an actual persistence mechanism. |
| Baseline (Phase 3, real 81-chunk/40-probe corpus) | Built A0 (full-context)/A (BM25 k=3)/A2 (+1 forced re-query)/B (sandboxed generalist agent) + the SelfHeal pipeline (retriever→generator→verifier→diagnose→tuner). Found and fixed 2 real bugs live: `allowed_tools` doesn't block Bash (fixed with explicit `disallowed_tools`); split context/value chunks broke both retrieval and citation-grading (fixed by merging to one chunk per version) — see `PROCESS.md`. | 7/7 verifier unit tests, 12/12 match unit tests, 7/7 sandbox-guard unit tests, all green post-fix. | Kept. Full per-arm frozen-test numbers land in Phase 5 below. |
| Iteration 1 (Phase 4, dev loop round 0→1) | Round 0: SelfHeal config with an empty memory store (operationally identical to Arm A's static config). Round 1: on the plurality failure (`memory_correction_missed`, 5/5 dev cases in that category wrong), consulted `data/correction_signals.json`, extracted, and persisted 5 corrections. | `advanced/selfheal_changelog.md`: round 0 = **17/24** dev accuracy (2 `retrieval_miss` + **all 5** memory_correction cases wrong); round 1 = **21/24 (+4)**. | **Kept.** Reproduces the pretest's categorical mechanism at real corpus scale with independently-authored ticket text, not the same toy example. |
| Iteration 2 (Phase 4, dev loop rounds 2–3) | Tried k=3→5, then k=3→7 (after fixing a bug where the k-ladder re-offered k=5 forever instead of advancing past a reverted attempt), targeting the 2 remaining `retrieval_miss` cases. | Both rounds: 22/24 (+1, below the +2 keep threshold). | **Reverted, both times — reported honestly.** k-bumping alone doesn't fix these 2 cases; the glossary/query-rewrite actions PLAN.md's full action mapping specifies were a disclosed, pre-agreed scope cut (see `advanced/tuner.py`'s docstring), not implemented this build. Loop stopped after 2 consecutive no-improvement rounds, by design — k=10 was never reached. |
| Final | *(filled after Phase 5 frozen-test run)* | | Main contribution identified here. |

---

## What the hard case revealed

*(filled in Phase 6, after the frozen-test run — the pre-registered hero case
is the Finance refund-cap implicit-supersession probe; see `PLAN.md` Phase 2)*

## Main failure mode

*(filled in Phase 6 — empirically confirmed, not invented in advance; see
`PLAN.md` Phase 5's hot-take hypotheses)*

## Hot take

*(filled in Phase 6)*

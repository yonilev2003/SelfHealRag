# Improvement Changelog

This file is the actual judged artifact (Measured Improvement 15%, Hot
Take/Insights 5%), not paperwork — entries are added as decisions are made,
not reconstructed from memory at the end (per `CLAUDE.md`).

| Stage | What we tried and why | Evidence | Decision / learning |
|---|---|---|---|
| Concept selection: LedgerGuard | Cross-source revenue reconciliation agent. Chosen after 2 independent rubric-blind judge panels (24 candidate ideas total) scored it highest, with a mechanically-planted oracle and a "tool-mediated ground truth" structural argument for why a single prompt should fail. | `results/pretest/*.json`: text-only baseline 1.44% error, 24.6 min, $3.55. **Single generalist agent with basic tools (the PDF's own fair baseline): 0.00% error, 2.3 min, $0.42.** | **Removed.** The fair baseline the kickoff document itself specifies already solved the task exactly, faster and cheaper. Deterministic, rule-following arithmetic over structured CSVs is exactly what a single generalist agent with tools is good at — orchestration would have measured zero delta against its own baseline. Full writeup: `archive/ledgerguard-pretest/README.md`. |
| Concept selection: SelfHeal RAG | Self-improving RAG pipeline over a versioned policy corpus: closed audit→diagnose→fix→reverify loop, generalizing to a frozen held-out split. Selected via a second, larger rubric-blind scan (27 ideas) explicitly steered toward "a single prompt structurally cannot do this" + the participant's own domain (RAG/data-analytics), then adversarially grilled twice (5 attackers × 2 rounds, 46 blocking issues found and resolved) before any code was written. | `PLAN.md` rev 1→3 diff; grill transcripts (`/workflows` run history). | **Adopted**, on the condition that Phase 1's empirical pre-test gate (same LedgerGuard protocol — generalist-agent-with-tools baseline vs. the concept) confirms the structural gap actually exists before committing further build time. |
| Baseline | *(filled after Phase 3 build)* | | |
| Iteration 1 | *(filled after Phase 4 dev-loop round 1)* | | |
| ... | | | |
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

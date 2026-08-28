# LedgerGuard — removed experiment

**What it was:** the first candidate concept selected for this hackathon — a
multi-agent revenue-reconciliation auditor over three cross-source CSV
exports (orders/payments/shipments), with a deterministic + LLM verifier
catching cross-source discrepancies.

**Why it was tried:** it scored highest (88.3-then-78 range across two
independent judge panels) of ~24 candidate ideas on a rubric-blind scoring
pass, with a clean, mechanically-verifiable oracle (`true_total` planted at
data-generation time, before corruption injection) and a structural
argument — tool-mediated ground truth over thousands of rows — for why a
single prompt should structurally fail.

**What killed it — real numbers, not a guess:**

| Arm | Predicted total | True total | % error | Wall-clock | Cost |
|---|---|---|---|---|---|
| Text-only single prompt (no tools) | $226,520.96 | $223,300.40 | 1.44% | 24.6 min | $3.55 |
| **Single generalist agent, basic code tools** (the PDF's own "one general purpose agent with basic tools" baseline) | $223,300.40 | $223,300.40 | **0.00%** | 2.3 min | **$0.42** |

The fair baseline the kickoff document itself specifies — a generalist agent
with basic tools, not a bare prompt — reconciled the pilot case to the cent,
faster and cheaper than a hand-orchestrated pipeline could realistically
have. The task was deterministic, rule-following arithmetic over structured
CSVs: exactly the shape of problem an agentic *system* adds no structural
value over a competent single agent for. Orchestration would have measured
zero delta against its own fair baseline.

**What it taught us:** the load-bearing question for concept selection isn't
"can this be computed only via execution/tools" (LedgerGuard satisfied that)
— it's "does a *single, unorchestrated* agent with the same tools already
solve it." A tool-mediated task with a clean deterministic solution path is
exactly what a single generalist agent is good at. The gap that justifies
agentic *architecture* (verification, memory, multi-round self-correction)
has to come from somewhere a single pass structurally cannot reach even with
tools — ambiguity/staleness a single read-through won't catch, state that
spans multiple independent runs, or an answer a same-context self-check
can't verify against anything but its own reasoning. This is exactly the
`scripts/pretest.py` protocol reused (and mandated in `PLAN.md`) to
pre-validate the next concept, SelfHeal RAG, before committing to it.

**Files preserved here (untouched, as generated/run):**
- `generate.py` — the seeded synthetic data + oracle generator
- `BUSINESS_RULES.md` — the shared revenue-recognition policy given to all arms
- `pilot-data/` — the two generated pilot cases
- `../../results/pretest/*.json`, `../../trajectories/pretest/*.jsonl` — the
  actual arm outputs and full agent trajectories from the runs above (kept in
  their original locations, not moved, since `trajectories/` is a disclosure
  requirement and must not be reshuffled retroactively)

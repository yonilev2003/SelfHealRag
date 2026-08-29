# Agent trajectories

Disclosure is mandatory per the Rule Book. Two capture paths — use whichever
matches how a given piece of work was actually run.

**Current coverage, exactly as it exists (no synthesized/reconstructed
traces):**
- `{A0,A,A2,B,C}_test/` — one file per frozen-test case per arm (16 cases
  each; A2 has 32, one per turn) — the actual eval-arm LLM calls.
- `pretest/` (2 files) and `pretest-selfheal/` (39 files) — the concept-
  selection/pivot pretest runs (LedgerGuard, the cross-session-memory
  experiment).
- `raw/` (2 interactive Claude Code session logs) — real, unedited
  session transcripts, not per-agent Workflow-run traces. One is the
  original repo-scaffold/hardening session (pre-kickoff); the other is
  the interactive session covering the V3 video audit, the README/
  AGENTS.md rewrite, and this final cleanup pass — captured mid-session,
  so it does not include this file's own edit or anything after it.
  **This build does not currently have a full raw-transcript trace for
  every interactive phase of the actual product build (Phases 2–7,
  below)** — only for the sessions above. Disclosed as-is rather than
  implied otherwise.

**Interactive Claude Code session (the default for this workflow):**
Every session is already logged, unprompted, to
`~/.claude/projects/<cwd-with-slashes-as-dashes>/<session-id>.jsonl`.
Run `make trajectories` (or `scripts/collect_trajectories.sh`) to copy the raw
files into `trajectories/raw/`. This format is internal and undocumented, and
can shift between Claude Code versions — copy it as-is rather than reformatting
it, so the disclosure stays faithful to what actually ran.

**Scripted / headless runs:**
If any part of the pipeline calls Claude Code non-interactively, capture it with
the documented, stable structured-output path:
```bash
claude -p "<prompt>" --output-format stream-json --verbose > trajectories/run.jsonl
```

**Workflow-tool runs (`.claude/workflows/*.js`):**
Every `agent()` call inside a Workflow run is itself a Claude Code session and is
captured the same way — `make trajectories` picks those up too, if a run's
transcript directory is still present locally. The workflow's own journal
(phases, which agent ran what, structured outputs) is additionally useful
context for judges evaluating "Agent Solution & Engineering"; consider copying
the relevant `journal.jsonl` from the run's transcript directory into
`trajectories/raw/` alongside the session logs. **Scope, precisely:**
`hackathon-sprint.js`/`hackathon-fix.js` genuinely ran for concept selection
(the judge panels and adversarial grilling that picked SelfHeal RAG over
LedgerGuard, per README §7/`PLAN.md`) — Phases 2–7, the actual baseline/
advanced build, ran directly in an interactive session instead, per `PLAN.md`'s
own execution-mode note, and are covered by the `raw/` interactive session
logs above, not by a Workflow-tool run journal.

**Curating for trace acquisition:** the event's conditional trace-reimbursement
program pays per qualifying trace ($2–$15, capped $100–200/participant) and looks
for exactly what the FAQ describes — "what the agent did and how its tools
responded, the feedback that shaped its next step, plus any retries or human
checkpoints." That's not automatic from a raw dump: when picking which sessions to
highlight (or trim `trajectories/raw/` to the representative set the submission
package actually asks for), favor runs that show real signal over noise —
- A `hackathon-sprint` concept-selection run that hit a `stopAfter`
  checkpoint, or either workflow's "grill" panel voting to reconsider (a
  genuine human-in-the-loop decision point — `hackathon-fix.js` has no
  `stopAfter`, only its own per-round grill) — if that run's transcript
  directory is still available locally; not claimed as currently present
  in `trajectories/raw/` otherwise.
- A round where `hackathon-fix.js`'s adversarial refute actually flipped a
  candidate bug (tool feedback changing the next step, not a rubber stamp)
  — same availability caveat.
- The original scaffold-hardening session, where an adversarial review found and
  fixed real bugs (race condition, regex false positives, a broken path-encoding
  script) — a clean before/after with concrete tool output driving the fix.
Don't hand-pick by deleting inconvenient sessions, though — disclosure is about
faithfulness first; curation here means *pointing to* the good examples (e.g. in
`MANIFEST.md` or the video), not scrubbing the record.

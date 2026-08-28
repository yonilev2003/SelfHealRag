# Agent trajectories

Disclosure is mandatory per the Rule Book. Two capture paths — use whichever
matches how a given piece of work was actually run.

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
captured the same way — `make trajectories` picks those up too. The workflow's own
journal (phases, which agent ran what, structured outputs) is additionally useful
context for judges evaluating "Agent Solution & Engineering"; consider copying the
relevant `journal.jsonl` from the run's transcript directory into `trajectories/raw/`
alongside the session logs.

**Curating for trace acquisition:** the event's conditional trace-reimbursement
program pays per qualifying trace ($2–$15, capped $100–200/participant) and looks
for exactly what the FAQ describes — "what the agent did and how its tools
responded, the feedback that shaped its next step, plus any retries or human
checkpoints." That's not automatic from a raw dump: when picking which sessions to
highlight (or trim `trajectories/raw/` to the representative set the submission
package actually asks for), favor runs that show real signal over noise —
- A `hackathon-sprint` run that hit a `stopAfter` checkpoint, or either
  workflow's "grill" panel voting to reconsider (a genuine human-in-the-loop
  decision point — `hackathon-fix.js` has no `stopAfter`, only its own
  per-round grill).
- A round where `hackathon-fix.js`'s adversarial refute actually flipped a
  candidate bug (tool feedback changing the next step, not a rubber stamp).
- The original scaffold-hardening session, where an adversarial review found and
  fixed real bugs (race condition, regex false positives, a broken path-encoding
  script) — a clean before/after with concrete tool output driving the fix.
Don't hand-pick by deleting inconvenient sessions, though — disclosure is about
faithfulness first; curation here means *pointing to* the good examples (e.g. in
`MANIFEST.md` or the video), not scrubbing the record.

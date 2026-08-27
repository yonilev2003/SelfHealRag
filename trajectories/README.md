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
